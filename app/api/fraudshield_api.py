from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import uuid4
from sqlalchemy.orm import Session

from app.modules.fraudshield.models import (
    FraudAlertsRequestModel,
    FraudAlertsResponseModel,
    FraudScoreRequestModel,
    FraudScoreResponseModel,
    TransactionMonitorRequest,
    TransactionMonitorResponse,
    TransactionEventModel,
)
from app.modules.fraudshield.service import FraudShieldService
from app.modules.fraudshield.demo_generator import get_demo_generator
from app.modules.fraudshield.pattern_detector import get_pattern_detector
from app.modules.fraudshield.db_service import (
    TransactionService,
    AlertService,
    CustomerProfileService,
    FraudPatternService,
    CaseService,
    AuditService,
)
from app.modules.fraudshield.db_models import (
    Alert,
    AlertStatus,
    Case,
    CaseStatus,
    CustomerProfile,
    FraudPatternDetection,
    RiskLevel,
    Transaction,
)
from app.database import get_db
from app.modules.shared.logging import log_error
from app.modules.shared.language import resolve_language

router = APIRouter()
service = FraudShieldService()


@router.post("/fraud/score", response_model=FraudScoreResponseModel)
async def score_fraud(
    http_request: Request, 
    request: FraudScoreRequestModel,
    db: Session = Depends(get_db)
) -> FraudScoreResponseModel:
    try:
        language = await resolve_language(http_request)
        result = await service.score_event(request, language=language)
        
        # Store transaction in database
        try:
            event = request.event
            transaction_data = {
                'event_id': event.event_id,
                'customer_id': event.customer_id,
                'amount': event.amount or 0.0,
                'currency': event.currency or 'ETB',
                'channel': event.channel,
                'event_type': event.event_type,
                'merchant_name': event.merchant,
                'location': event.location.city if event.location else None,
                'country': event.location.country if event.location else None,
                'ip_address': event.device.ip if event.device else None,
                'device_id': event.device.device_id if event.device else None,
                'session_id': event.session_id,
                'risk_score': result.risk_score,
                'risk_level': result.risk_level,
                'risk_reasons': result.reasons,
                'bank_id': request.bankId or 'dashen',
            }
            
            transaction = TransactionService.create_transaction(db, transaction_data)
            
            # Update customer profile
            if event.customer_id:
                CustomerProfileService.update_profile_from_transaction(
                    db, event.customer_id, request.bankId or 'dashen', transaction
                )
            
            # Auto-create alert for high-risk transactions
            if result.risk_score >= 70:
                try:
                    alert_data = {
                        'alert_id': f"alert-{event.event_id}",
                        'severity': result.risk_level,
                        'alert_type': ','.join(result.reasons) if result.reasons else 'fraud',
                        'summary': f"High-risk {event.event_type} detected (score {result.risk_score})",
                        'description': result.explanation or "",
                        'supporting_signals': result.reasons or [],
                        'affected_transactions': [event.event_id],
                        'status': AlertStatus.NEW,
                        'transaction_id': transaction.id,
                        'bank_id': request.bankId or 'dashen',
                    }
                    AlertService.create_alert(db, alert_data)
                except Exception:
                    pass  # Don't fail the request if alert creation fails

            # Audit log scoring decision
            try:
                AuditService.log_action(
                    db,
                    action="score_transaction",
                    entity_type="transaction",
                    entity_id=event.event_id,
                    user_id="system",
                    bank_id=request.bankId or 'dashen',
                    new_value={
                        'risk_score': result.risk_score,
                        'risk_level': result.risk_level,
                        'amount': event.amount,
                        'channel': event.channel,
                    }
                )
            except Exception:
                pass

        except Exception as db_error:
            # Log but don't fail the request if DB write fails
            log_error(module="fraudshield", session_id=event.session_id, error=db_error)
        
        return result
        
    except ValueError as exc:
        log_error(module="fraudshield", session_id=request.event.session_id if request.event else None, error=exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        log_error(module="fraudshield", session_id=request.event.session_id if request.event else None, error=exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post("/fraud/alerts", response_model=FraudAlertsResponseModel)
async def fraud_alerts(
    http_request: Request,
    request: FraudAlertsRequestModel,
    db: Session = Depends(get_db)
) -> FraudAlertsResponseModel:
    try:
        language = await resolve_language(http_request)
        result = await service.generate_alerts(request, language=language)

        bank_id = request.bankId or 'dashen'
        for alert in result.top_alerts:
            try:
                alert_data = {
                    'alert_id': alert.alert_id,
                    'severity': alert.severity,
                    'alert_type': 'fraud',
                    'summary': alert.summary,
                    'description': '',
                    'supporting_signals': alert.supporting_signals or [],
                    'affected_transactions': [],
                    'status': AlertStatus.NEW,
                    'bank_id': bank_id,
                }
                alert = AlertService.create_alert(db, alert_data)
                try:
                    AuditService.log_action(
                        db,
                        action="create_alert",
                        entity_type="alert",
                        entity_id=alert.alert_id,
                        user_id="system",
                        bank_id=bank_id,
                        new_value={
                            'severity': alert.severity.value,
                            'summary': alert.summary,
                            'status': alert.status.value,
                        }
                    )
                except Exception:
                    pass
            except Exception:
                pass  # Don't fail the request if a single alert fails to persist

        return result
    except ValueError as exc:
        log_error(module="fraudshield", session_id=None, error=exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        log_error(module="fraudshield", session_id=None, error=exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post("/fraud/monitor", response_model=TransactionMonitorResponse)
async def monitor_transactions(http_request: Request, request: TransactionMonitorRequest) -> TransactionMonitorResponse:
    try:
        language = await resolve_language(http_request)
        return await service.monitor_transactions(request, language=language)
    except ValueError as exc:
        log_error(module="fraudshield", session_id=None, error=exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        log_error(module="fraudshield", session_id=None, error=exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


class LiveFeedRequest(BaseModel):
    """Request for live transaction feed"""
    count: int = 10
    include_fraud: bool = True
    fraud_probability: float = 0.15
    bank_id: Optional[str] = Field(default="dashen", alias="bankId")

    class Config:
        populate_by_name = True


class ScoredTransaction(BaseModel):
    """Transaction with fraud score"""
    transaction: TransactionEventModel
    riskScore: int
    riskLevel: str
    reasons: List[str]
    timestamp: str


class LiveFeedResponse(BaseModel):
    """Response with scored transactions"""
    transactions: List[ScoredTransaction]
    metrics: dict


@router.post("/fraud/live-feed", response_model=LiveFeedResponse)
async def get_live_feed(http_request: Request, request: LiveFeedRequest) -> LiveFeedResponse:
    """
    Generate a live feed of transactions with fraud scores for demo purposes
    """
    try:
        language = await resolve_language(http_request)
        generator = get_demo_generator()
        
        # Generate transaction stream
        transactions = generator.generate_transaction_stream(
            count=request.count,
            fraud_probability=request.fraud_probability if request.include_fraud else 0.0
        )
        
        # Score each transaction using the selected bank's thresholds
        scored_transactions = []
        for txn in transactions:
            score_request = FraudScoreRequestModel(event=txn, bankId=request.bank_id)
            score_response = await service.score_event(score_request, language=language)
            
            scored_transactions.append(
                ScoredTransaction(
                    transaction=txn,
                    riskScore=score_response.risk_score,
                    riskLevel=score_response.risk_level,
                    reasons=score_response.reasons,
                    timestamp=txn.timestamp or "",
                )
            )
        
        # Generate live metrics
        metrics = generator.generate_live_metrics()
        
        return LiveFeedResponse(
            transactions=scored_transactions,
            metrics=metrics
        )
        
    except Exception as exc:  # noqa: BLE001
        log_error(module="fraudshield", session_id=None, error=exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


class LiveMetricsResponse(BaseModel):
    """Live monitoring metrics"""
    totalTransactions: int
    totalAlerts: int
    highRisk: int
    mediumRisk: int
    lowRisk: int
    fraudPrevented: float
    accuracy: float
    detectionRate: float
    falsePositiveRate: float
    transactionsMonitored: str


@router.get("/fraud/live-metrics", response_model=LiveMetricsResponse)
async def get_live_metrics() -> LiveMetricsResponse:
    """
    Get live monitoring metrics for dashboard
    """
    try:
        generator = get_demo_generator()
        metrics = generator.generate_live_metrics()
        
        return LiveMetricsResponse(**metrics)
        
    except Exception as exc:  # noqa: BLE001
        log_error(module="fraudshield", session_id=None, error=exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


class DetectedPattern(BaseModel):
    """Detected fraud pattern"""
    pattern_type: str
    severity: str
    confidence: float
    transaction_count: int
    total_amount: float
    description: str
    indicators: List[str]
    recommendation: str
    detected_at: str


class PatternDetectionResponse(BaseModel):
    """Response with detected fraud patterns"""
    patterns: List[DetectedPattern]
    total_patterns: int


@router.post("/fraud/detect-patterns", response_model=PatternDetectionResponse)
async def detect_fraud_patterns(request: LiveFeedRequest) -> PatternDetectionResponse:
    """
    Detect advanced fraud patterns in transaction stream
    """
    try:
        generator = get_demo_generator()
        detector = get_pattern_detector()
        
        # Generate transaction stream
        transactions = generator.generate_transaction_stream(
            count=request.count,
            fraud_probability=0.3  # Higher probability for pattern detection
        )
        
        # Detect patterns
        patterns = detector.detect_patterns(transactions)
        
        # Convert to response format
        detected_patterns = []
        for pattern in patterns:
            total_amount = sum(t.amount for t in pattern.transactions if t.amount)
            detected_patterns.append(
                DetectedPattern(
                    pattern_type=pattern.pattern_type,
                    severity=pattern.severity,
                    confidence=pattern.confidence,
                    transaction_count=len(pattern.transactions),
                    total_amount=total_amount,
                    description=pattern.description,
                    indicators=pattern.indicators,
                    recommendation=pattern.recommendation,
                    detected_at=pattern.detected_at,
                )
            )
        
        return PatternDetectionResponse(
            patterns=detected_patterns,
            total_patterns=len(detected_patterns)
        )
        
    except Exception as exc:  # noqa: BLE001
        log_error(module="fraudshield", session_id=None, error=exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


# ============================================================================
# DATABASE ENDPOINTS
# ============================================================================

class TransactionResponse(BaseModel):
    """Transaction from database"""
    id: int
    event_id: str
    customer_id: str
    amount: float
    currency: str
    channel: Optional[str]
    merchant_name: Optional[str]
    location: Optional[str]
    risk_score: int
    risk_level: str
    risk_reasons: List[str]
    created_at: str
    is_fraud: bool


@router.get("/fraud/transactions/recent")
async def get_recent_transactions(
    bank_id: str = "dashen",
    limit: int = 50,
    hours_back: int = 24,
    db: Session = Depends(get_db)
) -> List[TransactionResponse]:
    """
    Get recent transactions from database
    """
    try:
        transactions = TransactionService.get_high_risk_transactions(
            db, bank_id, limit, hours_back
        )
        
        return [
            TransactionResponse(
                id=t.id,
                event_id=t.event_id,
                customer_id=t.customer_id,
                amount=t.amount,
                currency=t.currency,
                channel=t.channel,
                merchant_name=t.merchant_name,
                location=t.location,
                risk_score=t.risk_score,
                risk_level=t.risk_level.value,
                risk_reasons=t.risk_reasons or [],
                created_at=t.created_at.isoformat(),
                is_fraud=t.is_fraud
            )
            for t in transactions
        ]
        
    except Exception as exc:  # noqa: BLE001
        log_error(module="fraudshield", session_id=None, error=exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/fraud/stats")
async def get_fraud_stats(
    bank_id: str = "dashen",
    hours_back: int = 24,
    db: Session = Depends(get_db)
):
    """
    Get fraud detection statistics from database
    """
    try:
        stats = TransactionService.get_transaction_stats(db, bank_id, hours_back)
        return stats
        
    except Exception as exc:  # noqa: BLE001
        log_error(module="fraudshield", session_id=None, error=exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


# ============================================================================
# ALERT MANAGEMENT ENDPOINTS
# ============================================================================

class AlertResponse(BaseModel):
    id: int
    alert_id: str
    severity: str
    alert_type: Optional[str]
    summary: Optional[str]
    description: Optional[str]
    status: str
    bank_id: str
    assigned_to: Optional[str]
    created_at: str
    transaction_id: Optional[int]


class AlertAssignmentRequest(BaseModel):
    assigned_to: str


class AlertResolutionRequest(BaseModel):
    resolved_by: str
    resolution_notes: str
    is_false_positive: bool = False


@router.get("/fraud/alerts", response_model=List[AlertResponse])
async def list_alerts(
    bank_id: str = "dashen",
    status: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List stored fraud alerts"""
    try:
        status_enum = AlertStatus(status) if status else None
        severity_enum = None
        if severity:
            try:
                severity_enum = RiskLevel[severity.upper()]
            except KeyError:
                raise HTTPException(status_code=400, detail=f"Invalid severity: {severity}")
        alerts = AlertService.get_alerts(db, bank_id, status=status_enum, severity=severity_enum, limit=limit)
        return [
            AlertResponse(
                id=a.id,
                alert_id=a.alert_id,
                severity=a.severity.value,
                alert_type=a.alert_type,
                summary=a.summary,
                description=a.description,
                status=a.status.value,
                bank_id=a.bank_id,
                assigned_to=a.assigned_to,
                created_at=a.created_at.isoformat(),
                transaction_id=a.transaction_id,
            )
            for a in alerts
        ]
    except HTTPException:
        raise
    except Exception as exc:
        log_error(module="fraudshield", session_id=None, error=exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/fraud/alerts/{alert_id}", response_model=AlertResponse)
async def get_alert(alert_id: str, db: Session = Depends(get_db)):
    """Get a single alert by ID"""
    try:
        alert = AlertService.get_alert_by_id(db, alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        return AlertResponse(
            id=alert.id,
            alert_id=alert.alert_id,
            severity=alert.severity.value,
            alert_type=alert.alert_type,
            summary=alert.summary,
            description=alert.description,
            status=alert.status.value,
            bank_id=alert.bank_id,
            assigned_to=alert.assigned_to,
            created_at=alert.created_at.isoformat(),
            transaction_id=alert.transaction_id,
        )
    except HTTPException:
        raise
    except Exception as exc:
        log_error(module="fraudshield", session_id=None, error=exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post("/fraud/alerts/{alert_id}/assign", response_model=AlertResponse)
async def assign_alert(
    alert_id: str,
    request: AlertAssignmentRequest,
    db: Session = Depends(get_db)
):
    """Assign an alert to an analyst"""
    try:
        alert = AlertService.assign_alert(db, alert_id, request.assigned_to)
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        try:
            AuditService.log_action(
                db,
                action="assign_alert",
                entity_type="alert",
                entity_id=alert.alert_id,
                user_id=request.assigned_to,
                bank_id=alert.bank_id,
                new_value={"assigned_to": request.assigned_to, "status": alert.status.value},
            )
        except Exception:
            pass
        return AlertResponse(
            id=alert.id,
            alert_id=alert.alert_id,
            severity=alert.severity.value,
            alert_type=alert.alert_type,
            summary=alert.summary,
            description=alert.description,
            status=alert.status.value,
            bank_id=alert.bank_id,
            assigned_to=alert.assigned_to,
            created_at=alert.created_at.isoformat(),
            transaction_id=alert.transaction_id,
        )
    except HTTPException:
        raise
    except Exception as exc:
        log_error(module="fraudshield", session_id=None, error=exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post("/fraud/alerts/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert(
    alert_id: str,
    request: AlertResolutionRequest,
    db: Session = Depends(get_db)
):
    """Resolve a fraud alert"""
    try:
        alert = AlertService.resolve_alert(
            db,
            alert_id,
            request.resolved_by,
            request.resolution_notes,
            request.is_false_positive
        )
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        try:
            AuditService.log_action(
                db,
                action="resolve_alert",
                entity_type="alert",
                entity_id=alert.alert_id,
                user_id=request.resolved_by,
                bank_id=alert.bank_id,
                new_value={
                    "status": alert.status.value,
                    "is_false_positive": request.is_false_positive,
                    "resolution_notes": request.resolution_notes,
                },
            )
        except Exception:
            pass
        return AlertResponse(
            id=alert.id,
            alert_id=alert.alert_id,
            severity=alert.severity.value,
            alert_type=alert.alert_type,
            summary=alert.summary,
            description=alert.description,
            status=alert.status.value,
            bank_id=alert.bank_id,
            assigned_to=alert.assigned_to,
            created_at=alert.created_at.isoformat(),
            transaction_id=alert.transaction_id,
        )
    except HTTPException:
        raise
    except Exception as exc:
        log_error(module="fraudshield", session_id=None, error=exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


class InvestigationRequest(BaseModel):
    bank_id: str = "dashen"
    customer_id: str
    amount: float
    currency: str = "ETB"
    channel: Optional[str] = None
    device_id: Optional[str] = None
    ip_address: Optional[str] = None
    risk_score: int
    risk_level: str
    reasons: List[str] = []


class InvestigationEvidence(BaseModel):
    source: str
    finding: str
    value: Any


class InvestigationStep(BaseModel):
    tool: str
    status: str
    records_found: int
    finding: str


class InvestigationResponse(BaseModel):
    event_id: str
    recommendation: str
    confidence: int
    hypothesis: str
    rationale: List[str]
    evidence: List[InvestigationEvidence]
    steps: List[InvestigationStep]


@router.post("/fraud/investigate/{event_id}", response_model=InvestigationResponse)
async def investigate_transaction(
    event_id: str,
    request: InvestigationRequest,
    db: Session = Depends(get_db),
):
    stored = TransactionService.get_transaction_by_event_id(db, event_id)
    customer_id = stored.customer_id if stored else request.customer_id
    bank_id = stored.bank_id if stored else request.bank_id
    amount = stored.amount if stored else request.amount
    risk_score = stored.risk_score if stored else request.risk_score
    reasons = list(stored.risk_reasons or []) if stored else list(request.reasons)
    device_id = stored.device_id if stored else request.device_id
    ip_address = stored.ip_address if stored else request.ip_address

    profile = db.query(CustomerProfile).filter(
        CustomerProfile.customer_id == customer_id,
        CustomerProfile.bank_id == bank_id,
    ).first()
    history = TransactionService.get_transactions_by_customer(
        db, customer_id, bank_id, limit=50, hours_back=24 * 180
    )
    related_entities = db.query(Transaction).filter(
        Transaction.bank_id == bank_id,
        Transaction.customer_id != customer_id,
    )
    if device_id and ip_address:
        related_entities = related_entities.filter(
            (Transaction.device_id == device_id) | (Transaction.ip_address == ip_address)
        )
    elif device_id:
        related_entities = related_entities.filter(Transaction.device_id == device_id)
    elif ip_address:
        related_entities = related_entities.filter(Transaction.ip_address == ip_address)
    else:
        related_entities = related_entities.filter(Transaction.id == -1)
    linked_transactions = related_entities.limit(50).all()
    if stored:
        alerts = db.query(Alert).filter(
            Alert.bank_id == bank_id,
            Alert.transaction_id == stored.id,
        ).all()
    else:
        bank_alerts = db.query(Alert).filter(Alert.bank_id == bank_id).limit(200).all()
        alerts = [item for item in bank_alerts if event_id in (item.affected_transactions or [])]
    cases = db.query(Case).filter(
        Case.bank_id == bank_id,
        Case.customer_id == customer_id,
    ).limit(20).all()
    patterns = FraudPatternService.get_patterns(db, bank_id, hours_back=24 * 30, limit=50)
    related_patterns = [
        pattern for pattern in patterns
        if customer_id in (pattern.customer_ids or []) or event_id in (pattern.transaction_ids or [])
    ]

    avg_amount = sum(item.amount for item in history) / len(history) if history else 0
    amount_multiple = amount / avg_amount if avg_amount > 0 else None
    linked_customers = sorted({item.customer_id for item in linked_transactions})
    confirmed_links = sum(1 for item in linked_transactions if item.is_fraud)
    evidence = [
        InvestigationEvidence(source="transaction", finding="Existing fraud assessment", value={"score": risk_score, "reasons": reasons}),
        InvestigationEvidence(source="customer_history", finding="180-day behavioral baseline", value={"transactions": len(history), "average_amount": round(avg_amount, 2), "amount_multiple": round(amount_multiple, 2) if amount_multiple else None}),
        InvestigationEvidence(source="device_graph", finding="Shared device or IP relationships", value={"linked_customers": linked_customers, "confirmed_fraud_links": confirmed_links}),
        InvestigationEvidence(source="alerts", finding="Alerts linked to this event", value=[item.alert_id for item in alerts]),
        InvestigationEvidence(source="cases", finding="Prior cases for this customer", value=[item.case_id for item in cases]),
        InvestigationEvidence(source="patterns", finding="Related detected fraud patterns", value=[item.pattern_id for item in related_patterns]),
        InvestigationEvidence(source="customer_profile", finding="Customer risk profile", value={"risk_score": profile.overall_risk_score, "pep": profile.is_pep, "watchlist": profile.is_watchlist} if profile else None),
    ]
    steps = [
        InvestigationStep(tool="customer_profile", status="completed", records_found=1 if profile else 0, finding="Customer risk and watchlist profile retrieved"),
        InvestigationStep(tool="transaction_history", status="completed", records_found=len(history), finding="Behavioral baseline calculated from stored transactions"),
        InvestigationStep(tool="device_graph", status="completed", records_found=len(linked_transactions), finding=f"Found {len(linked_customers)} linked customer(s) through device/IP"),
        InvestigationStep(tool="alert_case_search", status="completed", records_found=len(alerts) + len(cases), finding="Related alerts and historical cases retrieved"),
        InvestigationStep(tool="pattern_search", status="completed", records_found=len(related_patterns), finding="Known fraud patterns cross-referenced"),
        InvestigationStep(tool="policy_recommendation", status="completed", records_found=1, finding="Evidence aggregated into bounded recommendation"),
    ]

    rationale = list(reasons)
    if amount_multiple and amount_multiple >= 5:
        rationale.append(f"Amount is {amount_multiple:.1f}x the customer's 180-day average")
    if linked_customers:
        rationale.append(f"Device or IP is shared with {len(linked_customers)} other customer(s)")
    if confirmed_links:
        rationale.append(f"{confirmed_links} linked transaction(s) were confirmed as fraud")
    if related_patterns:
        rationale.append(f"Matched {len(related_patterns)} stored fraud pattern(s)")
    if profile and (profile.is_pep or profile.is_watchlist):
        rationale.append("Customer profile requires enhanced review")

    evidence_weight = risk_score + min(15, confirmed_links * 8) + min(10, len(related_patterns) * 4)
    if confirmed_links or evidence_weight >= 85:
        recommendation, confidence, hypothesis = "BLOCK", min(98, 80 + confirmed_links * 5 + len(related_patterns) * 3), "Likely coordinated fraud or account takeover"
    elif evidence_weight >= 55 or linked_customers or (amount_multiple and amount_multiple >= 5):
        recommendation, confidence, hypothesis = "REVIEW", min(95, 65 + len(rationale) * 3), "Material behavioral or relationship anomaly"
    else:
        recommendation, confidence, hypothesis = "APPROVE", max(60, 90 - risk_score // 2), "No corroborated high-risk evidence found"
    if not rationale:
        rationale.append("No material anomaly was found in available evidence")

    result = InvestigationResponse(
        event_id=event_id,
        recommendation=recommendation,
        confidence=confidence,
        hypothesis=hypothesis,
        rationale=rationale,
        evidence=evidence,
        steps=steps,
    )
    AuditService.log_action(
        db,
        action="agentic_investigation",
        entity_type="transaction",
        entity_id=event_id,
        user_id="gasha-investigator",
        user_role="system_agent",
        bank_id=bank_id,
        new_value=result.model_dump(),
        change_reason="Evidence-grounded fraud investigation requested",
    )
    return result


# ============================================================================
# CASE MANAGEMENT ENDPOINTS
# ============================================================================

class CaseResponse(BaseModel):
    id: int
    case_id: str
    title: str
    description: Optional[str]
    case_type: Optional[str]
    priority: Optional[str]
    status: str
    bank_id: str
    customer_id: str
    assigned_to: Optional[str]
    created_by: str
    created_at: str


class CaseCreateRequest(BaseModel):
    bank_id: str
    customer_id: str
    title: str
    description: str
    priority: str  # low, medium, high, critical
    case_type: str = "fraud_investigation"
    created_by: str
    total_amount_involved: Optional[float] = None
    transaction_count: Optional[int] = None
    evidence: Optional[List[Dict[str, Any]]] = None


class CaseNoteRequest(BaseModel):
    note: str
    created_by: str


class CaseAssignmentRequest(BaseModel):
    assigned_to: str


class CaseCloseRequest(BaseModel):
    resolution: str  # fraud_confirmed, legitimate, inconclusive
    resolution_notes: str
    resolved_by: str


@router.post("/fraud/cases", response_model=CaseResponse)
async def create_case(request: CaseCreateRequest, db: Session = Depends(get_db)):
    """Create a new investigation case"""
    try:
        case_data = {
            'case_id': f"CASE-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:6].upper()}",
            'bank_id': request.bank_id,
            'customer_id': request.customer_id,
            'title': request.title,
            'description': request.description,
            'case_type': request.case_type,
            'priority': request.priority,
            'status': CaseStatus.OPEN,
            'created_by': request.created_by,
            'total_amount_involved': request.total_amount_involved,
            'transaction_count': request.transaction_count,
            'evidence': request.evidence,
        }
        case = CaseService.create_case(db, case_data)
        try:
            AuditService.log_action(
                db,
                action="create_case",
                entity_type="case",
                entity_id=case.case_id,
                user_id=request.created_by,
                bank_id=case.bank_id,
                new_value={
                    "priority": case.priority,
                    "status": case.status.value,
                    "customer_id": case.customer_id,
                },
            )
        except Exception:
            pass
        return CaseResponse(
            id=case.id,
            case_id=case.case_id,
            title=case.title,
            description=case.description,
            case_type=case.case_type,
            priority=case.priority,
            status=case.status.value,
            bank_id=case.bank_id,
            customer_id=case.customer_id,
            assigned_to=case.assigned_to,
            created_by=case.created_by,
            created_at=case.created_at.isoformat(),
        )
    except Exception as exc:
        log_error(module="fraudshield", session_id=None, error=exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/fraud/cases", response_model=List[CaseResponse])
async def list_cases(
    bank_id: str = "dashen",
    status: Optional[str] = None,
    assigned_to: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List investigation cases"""
    try:
        status_enum = CaseStatus(status) if status else None
        cases = CaseService.get_cases(db, bank_id, status=status_enum, assigned_to=assigned_to, limit=limit)
        return [
            CaseResponse(
                id=c.id,
                case_id=c.case_id,
                title=c.title,
                description=c.description,
                case_type=c.case_type,
                priority=c.priority,
                status=c.status.value,
                bank_id=c.bank_id,
                customer_id=c.customer_id,
                assigned_to=c.assigned_to,
                created_by=c.created_by,
                created_at=c.created_at.isoformat(),
            )
            for c in cases
        ]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        log_error(module="fraudshield", session_id=None, error=exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/fraud/cases/{case_id}", response_model=CaseResponse)
async def get_case(case_id: str, db: Session = Depends(get_db)):
    """Get a single case by ID"""
    try:
        case = CaseService.get_case_by_id(db, case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        return CaseResponse(
            id=case.id,
            case_id=case.case_id,
            title=case.title,
            description=case.description,
            case_type=case.case_type,
            priority=case.priority,
            status=case.status.value,
            bank_id=case.bank_id,
            customer_id=case.customer_id,
            assigned_to=case.assigned_to,
            created_by=case.created_by,
            created_at=case.created_at.isoformat(),
        )
    except HTTPException:
        raise
    except Exception as exc:
        log_error(module="fraudshield", session_id=None, error=exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post("/fraud/cases/{case_id}/assign", response_model=CaseResponse)
async def assign_case(
    case_id: str,
    request: CaseAssignmentRequest,
    db: Session = Depends(get_db)
):
    """Assign a case to an analyst"""
    try:
        case = CaseService.assign_case(db, case_id, request.assigned_to)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        try:
            AuditService.log_action(
                db,
                action="assign_case",
                entity_type="case",
                entity_id=case.case_id,
                user_id=request.assigned_to,
                bank_id=case.bank_id,
                new_value={"assigned_to": request.assigned_to, "status": case.status.value},
            )
        except Exception:
            pass
        return CaseResponse(
            id=case.id,
            case_id=case.case_id,
            title=case.title,
            description=case.description,
            case_type=case.case_type,
            priority=case.priority,
            status=case.status.value,
            bank_id=case.bank_id,
            customer_id=case.customer_id,
            assigned_to=case.assigned_to,
            created_by=case.created_by,
            created_at=case.created_at.isoformat(),
        )
    except HTTPException:
        raise
    except Exception as exc:
        log_error(module="fraudshield", session_id=None, error=exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post("/fraud/cases/{case_id}/notes")
async def add_case_note(
    case_id: str,
    request: CaseNoteRequest,
    db: Session = Depends(get_db)
):
    """Add a note to a case"""
    try:
        case = CaseService.get_case_by_id(db, case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        note = CaseService.add_case_note(db, case.id, request.note, request.created_by)
        try:
            AuditService.log_action(
                db,
                action="add_case_note",
                entity_type="case",
                entity_id=case.case_id,
                user_id=request.created_by,
                bank_id=case.bank_id,
                new_value={"note_id": note.id, "note_preview": request.note[:200]},
            )
        except Exception:
            pass
        return {"note_id": note.id, "case_id": case_id, "created_at": note.created_at.isoformat()}
    except HTTPException:
        raise
    except Exception as exc:
        log_error(module="fraudshield", session_id=None, error=exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post("/fraud/cases/{case_id}/close", response_model=CaseResponse)
async def close_case(
    case_id: str,
    request: CaseCloseRequest,
    db: Session = Depends(get_db)
):
    """Close an investigation case"""
    try:
        case = CaseService.close_case(
            db,
            case_id,
            request.resolution,
            request.resolution_notes,
            request.resolved_by
        )
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        try:
            AuditService.log_action(
                db,
                action="close_case",
                entity_type="case",
                entity_id=case.case_id,
                user_id=request.resolved_by,
                bank_id=case.bank_id,
                new_value={
                    "status": case.status.value,
                    "resolution": request.resolution,
                    "resolution_notes": request.resolution_notes,
                },
            )
        except Exception:
            pass
        return CaseResponse(
            id=case.id,
            case_id=case.case_id,
            title=case.title,
            description=case.description,
            case_type=case.case_type,
            priority=case.priority,
            status=case.status.value,
            bank_id=case.bank_id,
            customer_id=case.customer_id,
            assigned_to=case.assigned_to,
            created_by=case.created_by,
            created_at=case.created_at.isoformat(),
        )
    except HTTPException:
        raise
    except Exception as exc:
        log_error(module="fraudshield", session_id=None, error=exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


# ============================================================================
# AUDIT TRAIL ENDPOINTS
# ============================================================================

class AuditLogResponse(BaseModel):
    id: int
    action: str
    entity_type: str
    entity_id: str
    user_id: Optional[str]
    user_role: Optional[str]
    bank_id: str
    change_reason: Optional[str]
    new_value: Optional[dict]
    created_at: str


@router.get("/fraud/audit", response_model=List[AuditLogResponse])
async def get_audit_logs(
    bank_id: str = "dashen",
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Query audit trail for fraud-related actions"""
    try:
        logs = AuditService.get_audit_logs(
            db,
            bank_id=bank_id,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            limit=limit
        )
        return [
            AuditLogResponse(
                id=log.id,
                action=log.action,
                entity_type=log.entity_type,
                entity_id=log.entity_id,
                user_id=log.user_id,
                user_role=log.user_role,
                bank_id=log.bank_id,
                change_reason=log.change_reason,
                new_value=log.new_value,
                created_at=log.created_at.isoformat(),
            )
            for log in logs
        ]
    except Exception as exc:
        log_error(module="fraudshield", session_id=None, error=exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc
