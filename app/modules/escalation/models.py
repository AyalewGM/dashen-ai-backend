"""
Escalation Service - Data Models
Handles human escalation requests from AI chatbot
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class EscalationStatus(str, Enum):
    """Escalation ticket status"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"


class EscalationPriority(str, Enum):
    """Escalation priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TriggerType(str, Enum):
    """Types of escalation triggers"""
    EXPLICIT_REQUEST = "explicit_request"  # User asks for human
    REPEATED_QUESTIONS = "repeated_questions"  # Same question multiple times
    FRUSTRATION_DETECTED = "frustration_detected"  # Negative sentiment
    COMPLEX_ISSUE = "complex_issue"  # Bot confidence low
    TIMEOUT = "timeout"  # Conversation too long
    COMPLAINT = "complaint"  # Customer complaint
    TECHNICAL_ERROR = "technical_error"  # System error


class ConversationMessage(BaseModel):
    """Single conversation message"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: str
    language: Optional[str] = "en"


class EscalationTrigger(BaseModel):
    """Escalation trigger detection result"""
    should_escalate: bool
    trigger_type: Optional[TriggerType] = None
    confidence: float = Field(ge=0.0, le=1.0)
    reason: Optional[str] = None
    priority: EscalationPriority = EscalationPriority.MEDIUM


class CreateEscalationRequest(BaseModel):
    """Request to create escalation ticket"""
    session_id: str
    customer_id: Optional[str] = None
    bank_id: str = "dashen"
    reason: str
    trigger_type: TriggerType
    priority: EscalationPriority = EscalationPriority.MEDIUM
    conversation_history: list[ConversationMessage] = []
    customer_info: Optional[dict] = None
    language: str = "en"


class EscalationTicket(BaseModel):
    """Escalation ticket model"""
    ticket_id: str
    session_id: str
    customer_id: Optional[str] = None
    bank_id: str
    status: EscalationStatus
    priority: EscalationPriority
    reason: str
    trigger_type: TriggerType
    assigned_to: Optional[str] = None
    created_at: datetime
    assigned_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    conversation_context: dict = {}
    metadata: dict = {}


class AssignEscalationRequest(BaseModel):
    """Request to assign escalation to agent"""
    ticket_id: str
    agent_id: str
    agent_name: Optional[str] = None


class ResolveEscalationRequest(BaseModel):
    """Request to resolve escalation"""
    ticket_id: str
    resolution_notes: str
    customer_satisfaction: Optional[int] = Field(None, ge=1, le=5)


class EscalationMetrics(BaseModel):
    """Escalation metrics"""
    total_escalations: int
    pending_escalations: int
    average_wait_time_seconds: float
    average_resolution_time_seconds: float
    escalation_rate: float  # Percentage of conversations escalated
    top_trigger_types: list[dict]
    satisfaction_score: Optional[float] = None


class EscalationResponse(BaseModel):
    """Response after creating escalation"""
    ticket_id: str
    status: EscalationStatus
    estimated_wait_time_minutes: int
    message: str
    agent_info: Optional[dict] = None
