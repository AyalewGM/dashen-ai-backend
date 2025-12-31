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
