"""
Escalation Module
Handles human escalation from AI chatbot
"""

from .detector import detector, EscalationDetector
from .models import (
    AssignEscalationRequest,
    ConversationMessage,
    CreateEscalationRequest,
    EscalationMetrics,
    EscalationPriority,
    EscalationResponse,
    EscalationStatus,
    EscalationTicket,
    EscalationTrigger,
    ResolveEscalationRequest,
    TriggerType,
)
from .service import escalation_service, EscalationService

__all__ = [
    "detector",
    "EscalationDetector",
    "AssignEscalationRequest",
    "ConversationMessage",
    "CreateEscalationRequest",
    "EscalationMetrics",
    "EscalationPriority",
    "EscalationResponse",
    "EscalationStatus",
    "EscalationTicket",
    "EscalationTrigger",
    "ResolveEscalationRequest",
    "TriggerType",
    "escalation_service",
    "EscalationService",
]
