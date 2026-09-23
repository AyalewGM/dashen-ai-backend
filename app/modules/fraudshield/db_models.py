"""
Database models for Gasha Fraud Detection System
Stores transactions, alerts, cases, and audit trail
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Boolean, ForeignKey, Enum, JSON, Index
from sqlalchemy.orm import relationship, declarative_base
import enum

Base = declarative_base()


class RiskLevel(str, enum.Enum):
    """Risk level enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CaseStatus(str, enum.Enum):
    """Case status enumeration"""
    OPEN = "open"
    INVESTIGATING = "investigating"
    PENDING_REVIEW = "pending_review"
    CLOSED_FRAUD = "closed_fraud"
    CLOSED_LEGITIMATE = "closed_legitimate"
    CLOSED_INCONCLUSIVE = "closed_inconclusive"


class AlertStatus(str, enum.Enum):
    """Alert status enumeration"""
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


# ============================================================================
# TRANSACTION MODELS
# ============================================================================

class Transaction(Base):
    """
    Main transaction table - stores all monitored transactions
    """
    __tablename__ = "gasha_transactions"
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(100), unique=True, nullable=False, index=True)
    
    # Transaction Details
    customer_id = Column(String(50), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="ETB")
    channel = Column(String(50))  # mobile, web, atm, branch, pos
    event_type = Column(String(50))  # transaction, login, transfer, etc.
    
    # Merchant Information
    merchant_name = Column(String(200))
    merchant_category = Column(String(100))
    merchant_id = Column(String(100))
    
    # Location & Device
    location = Column(String(200))
    country = Column(String(100))
    ip_address = Column(String(50))
    device_id = Column(String(200), index=True)
    session_id = Column(String(200))
    
    # Risk Assessment
    risk_score = Column(Integer, nullable=False)  # 0-100
    risk_level = Column(Enum(RiskLevel), nullable=False, index=True)
    risk_reasons = Column(JSON)  # List of risk factors
    
    # Fraud Detection
    is_fraud = Column(Boolean, default=False, index=True)
    fraud_confirmed_by = Column(String(100))  # User who confirmed
    fraud_confirmed_at = Column(DateTime)
    
    # Metadata
    bank_id = Column(String(50), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    alerts = relationship("Alert", back_populates="transaction", cascade="all, delete-orphan")
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_gtx_customer_date', 'customer_id', 'created_at'),
        Index('idx_gtx_risk_date', 'risk_level', 'created_at'),
        Index('idx_gtx_bank_date', 'bank_id', 'created_at'),
        Index('idx_fraud_date', 'is_fraud', 'created_at'),
    )


# ============================================================================
# ALERT MODELS
# ============================================================================

class Alert(Base):
    """
    Fraud alerts generated from transactions
    """
    __tablename__ = "gasha_alerts"
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_id = Column(String(100), unique=True, nullable=False, index=True)
    
    # Alert Details
    severity = Column(Enum(RiskLevel), nullable=False, index=True)
    alert_type = Column(String(100))  # velocity, structuring, account_takeover, etc.
    summary = Column(String(500))
    description = Column(Text)
    
    # Supporting Evidence
    supporting_signals = Column(JSON)  # List of signals/reasons
    affected_transactions = Column(JSON)  # List of transaction IDs
    
    # Status & Assignment
    status = Column(Enum(AlertStatus), default=AlertStatus.NEW, nullable=False, index=True)
    assigned_to = Column(String(100))  # Analyst username
    assigned_at = Column(DateTime)
    
    # Resolution
    resolved_by = Column(String(100))
    resolved_at = Column(DateTime)
    resolution_notes = Column(Text)
    
    # Foreign Keys
    transaction_id = Column(Integer, ForeignKey("gasha_transactions.id"), index=True)
    case_id = Column(Integer, index=True)  # Will be linked to cases later, no FK constraint to avoid circular dependency
    
    # Metadata
    bank_id = Column(String(50), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    transaction = relationship("Transaction", back_populates="alerts")
    
    # Indexes
    __table_args__ = (
        Index('idx_ga_status_severity', 'status', 'severity'),
        Index('idx_ga_bank_status', 'bank_id', 'status'),
    )


# ============================================================================
# CASE MANAGEMENT MODELS
# ============================================================================

class Case(Base):
    """
    Investigation cases for fraud analysis
    """
    __tablename__ = "gasha_cases"
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(100), unique=True, nullable=False, index=True)
    
    # Case Details
    title = Column(String(500), nullable=False)
    description = Column(Text)
    case_type = Column(String(100))  # fraud_investigation, false_positive_review, etc.
    priority = Column(String(50))  # low, medium, high, critical
    
    # Customer Information
    customer_id = Column(String(50), nullable=False, index=True)
    customer_name = Column(String(200))
    customer_risk_score = Column(Integer)
    
    # Status & Assignment
    status = Column(Enum(CaseStatus), default=CaseStatus.OPEN, nullable=False, index=True)
    assigned_to = Column(String(100), index=True)  # Analyst username
    assigned_at = Column(DateTime)
    
    # Investigation
    investigation_notes = Column(Text)
    evidence = Column(JSON)  # List of evidence items
    total_amount_involved = Column(Float)
    transaction_count = Column(Integer)
    
    # Resolution
    resolution = Column(String(100))  # fraud_confirmed, legitimate, inconclusive
    resolution_notes = Column(Text)
    resolved_by = Column(String(100))
    resolved_at = Column(DateTime)
    
    # NBE Reporting
    nbe_report_generated = Column(Boolean, default=False)
    nbe_report_id = Column(String(100))
    nbe_report_submitted_at = Column(DateTime)
    
    # SLA Tracking
    sla_due_date = Column(DateTime)
    sla_breached = Column(Boolean, default=False)
    
    # Metadata
    bank_id = Column(String(50), nullable=False, index=True)
    created_by = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    notes = relationship("CaseNote", back_populates="case", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_gc_status_priority', 'status', 'priority'),
        Index('idx_gc_customer_status', 'customer_id', 'status'),
        Index('idx_gc_assigned_status', 'assigned_to', 'status'),
    )


class CaseNote(Base):
    """
    Investigation notes for cases
    """
    __tablename__ = "gasha_case_notes"
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Note Details
    note = Column(Text, nullable=False)
    note_type = Column(String(50))  # investigation, decision, communication, etc.
    
    # Foreign Key
    case_id = Column(Integer, ForeignKey("gasha_cases.id"), nullable=False, index=True)
    
    # Metadata
    created_by = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    case = relationship("Case", back_populates="notes")


# ============================================================================
# FRAUD PATTERN MODELS
# ============================================================================

class FraudPatternDetection(Base):
    """
    Detected fraud patterns (structuring, velocity, etc.)
    """
    __tablename__ = "gasha_fraud_patterns"
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    pattern_id = Column(String(100), unique=True, nullable=False, index=True)
    
    # Pattern Details
    pattern_type = Column(String(100), nullable=False, index=True)  # structuring, velocity, smurfing, etc.
    severity = Column(Enum(RiskLevel), nullable=False)
    confidence = Column(Float)  # 0.0 to 1.0
    
    # Pattern Data
    description = Column(Text)
    indicators = Column(JSON)  # List of indicators
    recommendation = Column(Text)
    
    # Affected Entities
    customer_ids = Column(JSON)  # List of involved customers
    transaction_ids = Column(JSON)  # List of involved transactions
    transaction_count = Column(Integer)
    total_amount = Column(Float)
    
    # Status
    reviewed = Column(Boolean, default=False)
    reviewed_by = Column(String(100))
    reviewed_at = Column(DateTime)
    
    # Metadata
    bank_id = Column(String(50), nullable=False, index=True)
    detected_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_gfp_pattern_severity', 'pattern_type', 'severity'),
        Index('idx_gfp_bank_detected', 'bank_id', 'detected_at'),
    )


# ============================================================================
# AUDIT TRAIL MODELS
# ============================================================================

class AuditLog(Base):
    """
    Audit trail for all system actions (NBE compliance requirement)
    Retention: 10 years minimum
    """
    __tablename__ = "gasha_audit_logs"
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Action Details
    action = Column(String(100), nullable=False, index=True)  # view, update, delete, approve, etc.
    entity_type = Column(String(50), nullable=False)  # transaction, alert, case, etc.
    entity_id = Column(String(100), nullable=False, index=True)
    
    # User Information
    user_id = Column(String(100), nullable=False, index=True)
    user_role = Column(String(50))
    user_ip = Column(String(50))
    
    # Change Details
    old_value = Column(JSON)  # Previous state
    new_value = Column(JSON)  # New state
    change_reason = Column(Text)
    
    # Metadata
    bank_id = Column(String(50), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Indexes for audit queries
    __table_args__ = (
        Index('idx_gal_user_action', 'user_id', 'action'),
        Index('idx_gal_entity_action', 'entity_type', 'entity_id'),
        Index('idx_gal_bank_date', 'bank_id', 'created_at'),
    )


# ============================================================================
# CUSTOMER PROFILE MODELS
# ============================================================================

class CustomerProfile(Base):
    """
    Customer risk profiles and behavior baselines
    """
    __tablename__ = "gasha_customer_profiles"
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String(50), nullable=False, unique=True, index=True)
    
    # Customer Information
    customer_name = Column(String(200))
    account_type = Column(String(50))
    account_opened_date = Column(DateTime)
    
    # Risk Profile
    overall_risk_score = Column(Integer)  # 0-100
    risk_category = Column(Enum(RiskLevel))
    is_pep = Column(Boolean, default=False)  # Politically Exposed Person
    is_watchlist = Column(Boolean, default=False)
    
    # Behavioral Baselines
    avg_transaction_amount = Column(Float)
    avg_daily_transactions = Column(Integer)
    typical_channels = Column(JSON)  # List of channels
    typical_locations = Column(JSON)  # List of locations
    typical_merchants = Column(JSON)  # List of merchants
    
    # Historical Statistics
    total_transactions = Column(Integer, default=0)
    total_volume = Column(Float, default=0.0)
    fraud_incidents = Column(Integer, default=0)
    false_positives = Column(Integer, default=0)
    
    # Devices
    known_devices = Column(JSON)  # List of device IDs
    known_ips = Column(JSON)  # List of IP addresses
    
    # Metadata
    bank_id = Column(String(50), nullable=False, index=True)
    last_transaction_at = Column(DateTime)
    profile_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_gcp_bank_customer', 'bank_id', 'customer_id'),
        Index('idx_gcp_risk_category', 'risk_category'),
    )
