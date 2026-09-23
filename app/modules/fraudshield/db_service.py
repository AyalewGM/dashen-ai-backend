"""
Database service layer for Gasha Fraud Detection
Handles all database operations for transactions, alerts, and cases
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func, case

from .db_models import (
    Transaction,
    Alert,
    Case,
    CaseNote,
    FraudPatternDetection,
    AuditLog,
    CustomerProfile,
    RiskLevel,
    CaseStatus,
    AlertStatus,
)


class TransactionService:
    """Service for transaction database operations"""
    
    @staticmethod
    def create_transaction(db: Session, transaction_data: Dict[str, Any]) -> Transaction:
        """Create a new transaction record"""
        transaction = Transaction(**transaction_data)
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        return transaction
    
    @staticmethod
    def get_transaction_by_event_id(db: Session, event_id: str) -> Optional[Transaction]:
        """Get transaction by event ID"""
        return db.query(Transaction).filter(Transaction.event_id == event_id).first()
    
    @staticmethod
    def get_transactions_by_customer(
        db: Session,
        customer_id: str,
        bank_id: str,
        limit: int = 100,
        hours_back: int = 24
    ) -> List[Transaction]:
        """Get recent transactions for a customer"""
        since = datetime.utcnow() - timedelta(hours=hours_back)
        return db.query(Transaction).filter(
            and_(
                Transaction.customer_id == customer_id,
                Transaction.bank_id == bank_id,
                Transaction.created_at >= since
            )
        ).order_by(desc(Transaction.created_at)).limit(limit).all()
    
    @staticmethod
    def get_high_risk_transactions(
        db: Session,
        bank_id: str,
        limit: int = 50,
        hours_back: int = 24
    ) -> List[Transaction]:
        """Get recent high-risk transactions"""
        since = datetime.utcnow() - timedelta(hours=hours_back)
        return db.query(Transaction).filter(
            and_(
                Transaction.bank_id == bank_id,
                Transaction.created_at >= since
            )
        ).order_by(desc(Transaction.created_at)).limit(limit).all()
    
    @staticmethod
    def mark_as_fraud(
        db: Session,
        transaction_id: int,
        confirmed_by: str
    ) -> Transaction:
        """Mark transaction as confirmed fraud"""
        transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if transaction:
            transaction.is_fraud = True
            transaction.fraud_confirmed_by = confirmed_by
            transaction.fraud_confirmed_at = datetime.utcnow()
            db.commit()
            db.refresh(transaction)
        return transaction
    
    @staticmethod
    def get_transaction_stats(
        db: Session,
        bank_id: str,
        hours_back: int = 24
    ) -> Dict[str, Any]:
        """Get transaction statistics"""
        since = datetime.utcnow() - timedelta(hours=hours_back)
        
        stats = db.query(
            func.count(Transaction.id).label('total'),
            func.sum(case((Transaction.risk_level == RiskLevel.HIGH, 1), else_=0)).label('high_risk'),
            func.sum(case((Transaction.risk_level == RiskLevel.MEDIUM, 1), else_=0)).label('medium_risk'),
            func.sum(case((Transaction.risk_level == RiskLevel.LOW, 1), else_=0)).label('low_risk'),
            func.sum(case((Transaction.is_fraud == True, Transaction.amount), else_=0)).label('fraud_amount'),
        ).filter(
            and_(
                Transaction.bank_id == bank_id,
                Transaction.created_at >= since
            )
        ).first()
        
        return {
            'total_transactions': stats.total or 0,
            'high_risk': stats.high_risk or 0,
            'medium_risk': stats.medium_risk or 0,
            'low_risk': stats.low_risk or 0,
            'fraud_prevented': stats.fraud_amount or 0.0,
        }


class AlertService:
    """Service for alert database operations"""
    
    @staticmethod
    def create_alert(db: Session, alert_data: Dict[str, Any]) -> Alert:
        """Create a new alert"""
        alert = Alert(**alert_data)
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert
    
    @staticmethod
    def get_alert_by_id(db: Session, alert_id: str) -> Optional[Alert]:
        """Get alert by ID"""
        return db.query(Alert).filter(Alert.alert_id == alert_id).first()
    
    @staticmethod
    def get_alerts(
        db: Session,
        bank_id: str,
        status: Optional[AlertStatus] = None,
        severity: Optional[RiskLevel] = None,
        limit: int = 100
    ) -> List[Alert]:
        """Get alerts with optional filters"""
        query = db.query(Alert).filter(Alert.bank_id == bank_id)
        
        if status:
            query = query.filter(Alert.status == status)
        if severity:
            query = query.filter(Alert.severity == severity)
        
        return query.order_by(desc(Alert.created_at)).limit(limit).all()
    
    @staticmethod
    def assign_alert(
        db: Session,
        alert_id: str,
        assigned_to: str
    ) -> Alert:
        """Assign alert to an analyst"""
        alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
        if alert:
            alert.assigned_to = assigned_to
            alert.assigned_at = datetime.utcnow()
            alert.status = AlertStatus.INVESTIGATING
            db.commit()
            db.refresh(alert)
        return alert
    
    @staticmethod
    def resolve_alert(
        db: Session,
        alert_id: str,
        resolved_by: str,
        resolution_notes: str,
        is_false_positive: bool = False
    ) -> Alert:
        """Resolve an alert"""
        alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
        if alert:
            alert.resolved_by = resolved_by
            alert.resolved_at = datetime.utcnow()
            alert.resolution_notes = resolution_notes
            alert.status = AlertStatus.FALSE_POSITIVE if is_false_positive else AlertStatus.RESOLVED
            db.commit()
            db.refresh(alert)
        return alert


class CaseService:
    """Service for case management database operations"""
    
    @staticmethod
    def create_case(db: Session, case_data: Dict[str, Any]) -> Case:
        """Create a new investigation case"""
        # Set SLA due date (default: 48 hours for high priority, 72 hours for others)
        if 'sla_due_date' not in case_data:
            hours = 48 if case_data.get('priority') == 'high' else 72
            case_data['sla_due_date'] = datetime.utcnow() + timedelta(hours=hours)
        
        case = Case(**case_data)
        db.add(case)
        db.commit()
        db.refresh(case)
        return case
    
    @staticmethod
    def get_case_by_id(db: Session, case_id: str) -> Optional[Case]:
        """Get case by ID"""
        return db.query(Case).filter(Case.case_id == case_id).first()
    
    @staticmethod
    def get_cases(
        db: Session,
        bank_id: str,
        status: Optional[CaseStatus] = None,
        assigned_to: Optional[str] = None,
        limit: int = 100
    ) -> List[Case]:
        """Get cases with optional filters"""
        query = db.query(Case).filter(Case.bank_id == bank_id)
        
        if status:
            query = query.filter(Case.status == status)
        if assigned_to:
            query = query.filter(Case.assigned_to == assigned_to)
        
        return query.order_by(desc(Case.created_at)).limit(limit).all()
    
    @staticmethod
    def assign_case(
        db: Session,
        case_id: str,
        assigned_to: str
    ) -> Case:
        """Assign case to an analyst"""
        case = db.query(Case).filter(Case.case_id == case_id).first()
        if case:
            case.assigned_to = assigned_to
            case.assigned_at = datetime.utcnow()
            case.status = CaseStatus.INVESTIGATING
            db.commit()
            db.refresh(case)
        return case
    
    @staticmethod
    def add_case_note(
        db: Session,
        case_id: int,
        note: str,
        created_by: str,
        note_type: str = "investigation"
    ) -> CaseNote:
        """Add a note to a case"""
        case_note = CaseNote(
            case_id=case_id,
            note=note,
            note_type=note_type,
            created_by=created_by
        )
        db.add(case_note)
        db.commit()
        db.refresh(case_note)
        return case_note
    
    @staticmethod
    def close_case(
        db: Session,
        case_id: str,
        resolution: str,
        resolution_notes: str,
        resolved_by: str
    ) -> Case:
        """Close a case"""
        case = db.query(Case).filter(Case.case_id == case_id).first()
        if case:
            case.resolution = resolution
            case.resolution_notes = resolution_notes
            case.resolved_by = resolved_by
            case.resolved_at = datetime.utcnow()
            
            # Set status based on resolution
            if resolution == "fraud_confirmed":
                case.status = CaseStatus.CLOSED_FRAUD
            elif resolution == "legitimate":
                case.status = CaseStatus.CLOSED_LEGITIMATE
            else:
                case.status = CaseStatus.CLOSED_INCONCLUSIVE
            
            db.commit()
            db.refresh(case)
        return case


class FraudPatternService:
    """Service for fraud pattern detection storage"""
    
    @staticmethod
    def create_pattern(db: Session, pattern_data: Dict[str, Any]) -> FraudPatternDetection:
        """Store a detected fraud pattern"""
        pattern = FraudPatternDetection(**pattern_data)
        db.add(pattern)
        db.commit()
        db.refresh(pattern)
        return pattern
    
    @staticmethod
    def get_patterns(
        db: Session,
        bank_id: str,
        pattern_type: Optional[str] = None,
        hours_back: int = 24,
        limit: int = 50
    ) -> List[FraudPatternDetection]:
        """Get detected patterns"""
        since = datetime.utcnow() - timedelta(hours=hours_back)
        query = db.query(FraudPatternDetection).filter(
            and_(
                FraudPatternDetection.bank_id == bank_id,
                FraudPatternDetection.detected_at >= since
            )
        )
        
        if pattern_type:
            query = query.filter(FraudPatternDetection.pattern_type == pattern_type)
        
        return query.order_by(desc(FraudPatternDetection.detected_at)).limit(limit).all()


class AuditService:
    """Service for audit trail logging"""
    
    @staticmethod
    def log_action(
        db: Session,
        action: str,
        entity_type: str,
        entity_id: str,
        user_id: str,
        bank_id: str,
        user_role: Optional[str] = None,
        user_ip: Optional[str] = None,
        old_value: Optional[Dict] = None,
        new_value: Optional[Dict] = None,
        change_reason: Optional[str] = None
    ) -> AuditLog:
        """Log an action to audit trail"""
        audit_log = AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            user_role=user_role,
            user_ip=user_ip,
            old_value=old_value,
            new_value=new_value,
            change_reason=change_reason,
            bank_id=bank_id
        )
        db.add(audit_log)
        db.commit()
        return audit_log
    
    @staticmethod
    def get_audit_trail(
        db: Session,
        entity_type: str,
        entity_id: str,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit trail for an entity"""
        return db.query(AuditLog).filter(
            and_(
                AuditLog.entity_type == entity_type,
                AuditLog.entity_id == entity_id
            )
        ).order_by(desc(AuditLog.created_at)).limit(limit).all()
    
    @staticmethod
    def get_audit_logs(
        db: Session,
        bank_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs with optional filters"""
        query = db.query(AuditLog)
        
        if bank_id:
            query = query.filter(AuditLog.bank_id == bank_id)
        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)
        if entity_id:
            query = query.filter(AuditLog.entity_id == entity_id)
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        
        return query.order_by(desc(AuditLog.created_at)).limit(limit).all()


class CustomerProfileService:
    """Service for customer profile management"""
    
    @staticmethod
    def get_or_create_profile(
        db: Session,
        customer_id: str,
        bank_id: str
    ) -> CustomerProfile:
        """Get existing profile or create new one"""
        profile = db.query(CustomerProfile).filter(
            and_(
                CustomerProfile.customer_id == customer_id,
                CustomerProfile.bank_id == bank_id
            )
        ).first()
        
        if not profile:
            profile = CustomerProfile(
                customer_id=customer_id,
                bank_id=bank_id,
                overall_risk_score=50,  # Default medium risk
                risk_category=RiskLevel.MEDIUM
            )
            db.add(profile)
            db.commit()
            db.refresh(profile)
        
        return profile
    
    @staticmethod
    def update_profile_from_transaction(
        db: Session,
        customer_id: str,
        bank_id: str,
        transaction: Transaction
    ) -> CustomerProfile:
        """Update customer profile based on new transaction"""
        profile = CustomerProfileService.get_or_create_profile(db, customer_id, bank_id)
        
        # Update statistics
        profile.total_transactions = (profile.total_transactions or 0) + 1
        profile.total_volume = (profile.total_volume or 0.0) + transaction.amount
        profile.last_transaction_at = transaction.created_at
        
        # Update behavioral baselines (simplified)
        if profile.total_transactions > 0:
            profile.avg_transaction_amount = profile.total_volume / profile.total_transactions
        
        # Track devices
        if transaction.device_id:
            known_devices = profile.known_devices or []
            if transaction.device_id not in known_devices:
                known_devices.append(transaction.device_id)
                profile.known_devices = known_devices[-10:]  # Keep last 10 devices
        
        db.commit()
        db.refresh(profile)
        return profile
