"""
Escalation API Endpoints
Provides REST API for human escalation management
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.modules.escalation.models import (
    AssignEscalationRequest,
    ConversationMessage,
    CreateEscalationRequest,
    EscalationMetrics,
    EscalationResponse,
    EscalationTicket,
    EscalationTrigger,
    ResolveEscalationRequest,
)
from app.modules.escalation.service import escalation_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/escalation", tags=["escalation"])


@router.post("/detect", response_model=EscalationTrigger)
async def detect_escalation(
    conversation_history: list[ConversationMessage],
    language: str = "en",
    bot_confidence: Optional[float] = None
):
    """
    Detect if conversation should be escalated to human agent
    
    Args:
        conversation_history: List of conversation messages
        language: Conversation language (en, am, om, ti, so)
        bot_confidence: Bot's confidence in last response (0-1)
    
    Returns:
        EscalationTrigger with detection results
    """
    try:
        trigger = await escalation_service.detect_escalation_needed(
            conversation_history=conversation_history,
            language=language,
            bot_confidence=bot_confidence
        )
        return trigger
    
    except Exception as e:
        logger.error(f"Error detecting escalation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create", response_model=EscalationResponse)
async def create_escalation(request: CreateEscalationRequest):
    """
    Create a new escalation ticket
    
    Args:
        request: Escalation creation request with conversation context
    
    Returns:
        EscalationResponse with ticket ID and estimated wait time
    """
    try:
        response = await escalation_service.create_escalation(request)
        return response
    
    except Exception as e:
        logger.error(f"Error creating escalation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/assign", response_model=EscalationTicket)
async def assign_escalation(request: AssignEscalationRequest):
    """
    Assign escalation ticket to an agent
    
    Args:
        request: Assignment request with ticket_id and agent_id
    
    Returns:
        Updated EscalationTicket
    """
    try:
        ticket = await escalation_service.assign_escalation(request)
        return ticket
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error assigning escalation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resolve", response_model=EscalationTicket)
async def resolve_escalation(request: ResolveEscalationRequest):
    """
    Resolve escalation ticket
    
    Args:
        request: Resolution request with ticket_id and notes
    
    Returns:
        Updated EscalationTicket
    """
    try:
        ticket = await escalation_service.resolve_escalation(request)
        return ticket
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error resolving escalation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ticket/{ticket_id}", response_model=EscalationTicket)
async def get_ticket(ticket_id: str):
    """
    Get escalation ticket by ID
    
    Args:
        ticket_id: Unique ticket identifier
    
    Returns:
        EscalationTicket details
    """
    try:
        ticket = await escalation_service.get_ticket(ticket_id)
        
        if not ticket:
            raise HTTPException(status_code=404, detail=f"Ticket not found: {ticket_id}")
        
        return ticket
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ticket: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pending", response_model=list[EscalationTicket])
async def get_pending_escalations(
    bank_id: Optional[str] = Query(None, description="Filter by bank ID"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of tickets to return")
):
    """
    Get pending escalation tickets
    
    Args:
        bank_id: Optional bank ID filter
        limit: Maximum number of tickets (1-100)
    
    Returns:
        List of pending EscalationTickets
    """
    try:
        tickets = await escalation_service.get_pending_escalations(
            bank_id=bank_id,
            limit=limit
        )
        return tickets
    
    except Exception as e:
        logger.error(f"Error getting pending escalations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics", response_model=EscalationMetrics)
async def get_escalation_metrics(
    bank_id: Optional[str] = Query(None, description="Filter by bank ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze")
):
    """
    Get escalation metrics and analytics
    
    Args:
        bank_id: Optional bank ID filter
        days: Number of days to analyze (1-365)
    
    Returns:
        EscalationMetrics with performance data
    """
    try:
        metrics = await escalation_service.get_metrics(
            bank_id=bank_id,
            days=days
        )
        return metrics
    
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
