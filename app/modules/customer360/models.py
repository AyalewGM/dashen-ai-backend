from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# Enums
class CustomerSegment(str, Enum):
    VIP = "VIP"
    ACTIVE = "Active"
    NEW = "New"
    DORMANT = "Dormant"
    AT_RISK = "At Risk"
    SME = "SME"


class RiskLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class ChannelType(str, Enum):
    MOBILE_APP = "Mobile App"
    BRANCH = "Branch"
    ATM = "ATM"
    CALL_CENTER = "Call Center"
    WEB = "Web"
    USSD = "USSD"


class ProductType(str, Enum):
    SAVINGS = "Savings Account"
    CURRENT = "Current Account"
    LOAN = "Loan"
    CREDIT_CARD = "Credit Card"
    INVESTMENT = "Investment"
    MOBILE_BANKING = "Mobile Banking"


class ActionType(str, Enum):
    CROSS_SELL = "Cross-Sell"
    RETENTION = "Retention"
    ENGAGEMENT = "Engagement"
    RISK_MITIGATION = "Risk Mitigation"
    UPSELL = "Upsell"


# Core Models
class CustomerDemographics(BaseModel):
    age: int
    gender: Optional[str] = None
    location: str
    occupation: Optional[str] = None
    income_bracket: Optional[str] = None
    education_level: Optional[str] = None


class AccountSummary(BaseModel):
    product_type: ProductType
    account_number: str
    balance: float
    opened_date: str
    status: str
    monthly_activity: float


class TransactionPattern(BaseModel):
    avg_monthly_spend: float
    avg_transaction_value: float
    top_categories: list[dict[str, Any]]
    preferred_merchants: list[str]
    peak_transaction_hours: list[int]


class ChannelBehavior(BaseModel):
    channel: ChannelType
    usage_count: int
    last_used: str
    preference_score: float


class FinancialHealth(BaseModel):
    credit_score: int
    debt_to_income_ratio: float
    savings_rate: float
    payment_history_score: float
    overall_health_score: float
    health_trend: str  # "improving", "stable", "declining"


class BehavioralInsight(BaseModel):
    insight_type: str
    title: str
    description: str
    confidence: float
    detected_at: str
    impact: str  # "high", "medium", "low"


class ChurnRiskAssessment(BaseModel):
    risk_level: RiskLevel
    risk_score: float
    risk_factors: list[str]
    recommended_actions: list[str]


class NextBestAction(BaseModel):
    action_id: str
    action_type: ActionType
    title: str
    description: str
    expected_value: float
    priority: int
    confidence: float
    valid_until: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class LifeEvent(BaseModel):
    event_type: str
    detected_at: str
    confidence: float
    description: str
    recommended_products: list[str]


class InteractionTimeline(BaseModel):
    timestamp: str
    channel: ChannelType
    interaction_type: str
    summary: str
    outcome: Optional[str] = None


# Response Models
class UnifiedCustomerProfile(BaseModel):
    customer_id: str
    full_name: str
    segment: CustomerSegment
    demographics: CustomerDemographics
    accounts: list[AccountSummary]
    financial_health: FinancialHealth
    total_relationship_value: float
    customer_since: str
    last_interaction: str


class CustomerBehaviorAnalysis(BaseModel):
    customer_id: str
    transaction_patterns: TransactionPattern
    channel_preferences: list[ChannelBehavior]
    engagement_score: float
    loyalty_score: float
    behavioral_insights: list[BehavioralInsight]
    detected_life_events: list[LifeEvent]


class Customer360Response(BaseModel):
    profile: UnifiedCustomerProfile
    behavior: CustomerBehaviorAnalysis
    churn_risk: ChurnRiskAssessment
    next_best_actions: list[NextBestAction]
    recent_interactions: list[InteractionTimeline]
    metadata: dict[str, Any] = Field(default_factory=dict)


class Customer360Request(BaseModel):
    customer_id: str
    include_transactions: bool = True
    include_interactions: bool = True
    include_predictions: bool = True
    time_range_days: int = 90


class CustomerSearchRequest(BaseModel):
    query: str
    filters: dict[str, Any] = Field(default_factory=dict)
    limit: int = 20


class CustomerSearchResult(BaseModel):
    customer_id: str
    full_name: str
    segment: CustomerSegment
    total_balance: float
    risk_level: RiskLevel
    last_interaction: str
    match_score: float


class CustomerSearchResponse(BaseModel):
    results: list[CustomerSearchResult]
    total_count: int
    metadata: dict[str, Any] = Field(default_factory=dict)
