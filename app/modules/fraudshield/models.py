from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class LocationModel(BaseModel):
    country: Optional[str] = None
    city: Optional[str] = None


class DeviceModel(BaseModel):
    device_id: Optional[str] = Field(default=None, alias="deviceId")
    ip: Optional[str] = None

    class Config:
        populate_by_name = True


class TransactionEventModel(BaseModel):
    event_id: str = Field(..., alias="eventId")
    session_id: Optional[str] = Field(default=None, alias="sessionId")
    customer_id: Optional[str] = Field(default=None, alias="customerId")
    timestamp: str
    amount: float
    currency: str = "ETB"
    channel: str
    merchant: Optional[str] = None
    location: Optional[LocationModel] = None
    device: Optional[DeviceModel] = None
    event_type: str = Field(..., alias="eventType")

    class Config:
        populate_by_name = True


class FraudScoreRequestModel(BaseModel):
    event: TransactionEventModel
    bankId: Optional[str] = Field(default=None, alias="bankId")

    class Config:
        populate_by_name = True


RiskLevel = Literal["low", "medium", "high"]


class FraudScoreMetadataModel(BaseModel):
    engine: str
    latency_ms: int = Field(..., alias="latencyMs")

    class Config:
        populate_by_name = True


class FraudScoreResponseModel(BaseModel):
    risk_score: int = Field(..., alias="riskScore")
    risk_level: RiskLevel = Field(..., alias="riskLevel")
    reasons: list[str]
    recommended_action: str = Field(..., alias="recommendedAction")
    metadata: FraudScoreMetadataModel
    explanation: Optional[str] = None

    class Config:
        populate_by_name = True


class FraudAlertsRequestModel(BaseModel):
    events: list[TransactionEventModel]
    bankId: Optional[str] = Field(default="dashen", alias="bankId")

    class Config:
        populate_by_name = True


class AlertModel(BaseModel):
    alert_id: str = Field(..., alias="alertId")
    severity: RiskLevel
    summary: str
    supporting_signals: list[str] = Field(..., alias="supportingSignals")
    timestamp: str

    class Config:
        populate_by_name = True


class FraudAlertsMetadataModel(BaseModel):
    engine: str
    latency_ms: int = Field(..., alias="latencyMs")

    class Config:
        populate_by_name = True


class FraudAlertsResponseModel(BaseModel):
    top_alerts: list[AlertModel] = Field(..., alias="topAlerts")
    metadata: FraudAlertsMetadataModel

    class Config:
        populate_by_name = True


# Transaction Monitoring Models
class BehavioralScore(BaseModel):
    velocity_score: int = Field(..., alias="velocityScore")
    pattern_score: int = Field(..., alias="patternScore")
    anomaly_score: int = Field(..., alias="anomalyScore")
    total: int

    class Config:
        populate_by_name = True


class MonitoringAlert(BaseModel):
    alert_id: str = Field(..., alias="alertId")
    customer_id: Optional[str] = Field(default=None, alias="customerId")
    severity: RiskLevel
    scenario: str
    rule_score: int = Field(..., alias="ruleScore")
    behavioral_score: BehavioralScore = Field(..., alias="behavioralScore")
    combined_score: int = Field(..., alias="combinedScore")
    false_positive_risk: str = Field(..., alias="falsePositiveRisk")  # low, medium, high
    summary: str
    signals: list[str]
    timestamp: str
    recommended_action: str = Field(..., alias="recommendedAction")

    class Config:
        populate_by_name = True


class FraudPattern(BaseModel):
    pattern_id: str = Field(..., alias="patternId")
    pattern_type: str = Field(..., alias="patternType")
    description: str
    affected_customers: int = Field(..., alias="affectedCustomers")
    event_count: int = Field(..., alias="eventCount")
    severity: RiskLevel
    confidence: float

    class Config:
        populate_by_name = True


class MonitoringMetrics(BaseModel):
    total_events: int = Field(..., alias="totalEvents")
    alerts_generated: int = Field(..., alias="alertsGenerated")
    high_risk_count: int = Field(..., alias="highRiskCount")
    medium_risk_count: int = Field(..., alias="mediumRiskCount")
    avg_risk_score: float = Field(..., alias="avgRiskScore")
    false_positive_rate: float = Field(..., alias="falsePositiveRate")
    patterns_detected: int = Field(..., alias="patternsDetected")

    class Config:
        populate_by_name = True


class TransactionMonitorRequest(BaseModel):
    events: list[TransactionEventModel]
    bank_id: Optional[str] = Field(default="dashen", alias="bankId")

    class Config:
        populate_by_name = True


class TransactionMonitorResponse(BaseModel):
    alerts: list[MonitoringAlert]
    patterns: list[FraudPattern]
    metrics: MonitoringMetrics
    summary: str

    class Config:
        populate_by_name = True
