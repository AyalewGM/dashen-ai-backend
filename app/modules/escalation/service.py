"""
Escalation Service
Manages human escalation tickets and agent assignment
"""

import json
import logging
import secrets
from datetime import datetime, timezone
from typing import Optional

import psycopg2
from psycopg2.extras import RealDictCursor

from app.modules.shared.db import get_db_connection
from app.modules.shared.bank_config import get_bank_config

from .detector import detector
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

logger = logging.getLogger(__name__)


class EscalationService:
    """Service for managing human escalations"""
    
    def __init__(self):
        self.detector = detector
        self._ensure_tables_exist()
    
    def _ensure_tables_exist(self):
        """Create escalation tables if they don't exist"""
        try:
            conn = get_db_connection()
            if not conn:
                logger.warning("No database connection, escalation tables not created")
                return
            
            with conn.cursor() as cur:
                # Read and execute schema
                schema_path = "app/modules/escalation/db_schema.sql"
                try:
                    with open(schema_path, 'r') as f:
                        schema_sql = f.read()
                        cur.execute(schema_sql)
                        conn.commit()
                        logger.info("Escalation tables created successfully")
                except FileNotFoundError:
                    logger.warning(f"Schema file not found: {schema_path}")
            
            conn.close()
        except Exception as e:
            logger.error(f"Error creating escalation tables: {e}")
    
    async def detect_escalation_needed(
        self,
        conversation_history: list[ConversationMessage],
        language: str = "en",
        bot_confidence: Optional[float] = None
    ) -> EscalationTrigger:
        """
        Detect if conversation should be escalated
        
        Args:
            conversation_history: List of conversation messages
            language: Conversation language
            bot_confidence: Bot's confidence in last response (0-1)
            
        Returns:
            EscalationTrigger with detection results
        """
        # Check conversation patterns
        trigger = self.detector.detect_escalation_trigger(conversation_history, language)
        
        # Also check bot confidence if provided
        if bot_confidence is not None and not trigger.should_escalate:
            confidence_trigger = self.detector.check_complex_issue(bot_confidence)
            if confidence_trigger.should_escalate:
                return confidence_trigger
        
        return trigger
    
    async def create_escalation(
        self,
        request: CreateEscalationRequest
    ) -> EscalationResponse:
        """
        Create a new escalation ticket
        
        Args:
            request: Escalation creation request
            
        Returns:
            EscalationResponse with ticket details
        """
        # Generate unique ticket ID
        ticket_id = self._generate_ticket_id(request.bank_id)
        
        # Prepare conversation context
        conversation_context = {
            "messages": [msg.dict() for msg in request.conversation_history],
            "language": request.language,
            "customer_info": request.customer_info or {}
        }
        
        # Get bank config for context
        bank_config = get_bank_config(request.bank_id)
        
        # Insert ticket into database
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO escalation_tickets (
                            ticket_id, session_id, customer_id, bank_id,
                            status, priority, reason, trigger_type,
                            conversation_context, metadata
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING created_at
                    """, (
                        ticket_id,
                        request.session_id,
                        request.customer_id,
                        request.bank_id,
                        EscalationStatus.PENDING.value,
                        request.priority.value,
                        request.reason,
                        request.trigger_type.value,
                        json.dumps(conversation_context),
                        json.dumps({"bank_name": bank_config.bank_name})
                    ))
                    
                    created_at = cur.fetchone()[0]
                    conn.commit()
                    
                    # Log event
                    self._log_event(
                        conn,
                        ticket_id,
                        "created",
                        {"reason": request.reason, "priority": request.priority.value}
                    )
                    
                    logger.info(f"Created escalation ticket: {ticket_id}")
                
                conn.close()
            except Exception as e:
                logger.error(f"Error creating escalation ticket: {e}")
                if conn:
                    conn.close()
                raise
        
        # Estimate wait time based on priority and current queue
        estimated_wait = self._estimate_wait_time(request.priority)
        
        # Prepare response message
        message = self._get_escalation_message(request.language, estimated_wait)
        
        return EscalationResponse(
            ticket_id=ticket_id,
            status=EscalationStatus.PENDING,
            estimated_wait_time_minutes=estimated_wait,
            message=message
        )
    
    async def assign_escalation(
        self,
        request: AssignEscalationRequest
    ) -> EscalationTicket:
        """
        Assign escalation ticket to an agent
        
        Args:
            request: Assignment request
            
        Returns:
            Updated EscalationTicket
        """
        conn = get_db_connection()
        if not conn:
            raise Exception("Database connection not available")
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Update ticket
                cur.execute("""
                    UPDATE escalation_tickets
                    SET assigned_to = %s,
                        assigned_at = NOW(),
                        status = %s
                    WHERE ticket_id = %s
                    RETURNING *
                """, (
                    request.agent_id,
                    EscalationStatus.ASSIGNED.value,
                    request.ticket_id
                ))
                
                row = cur.fetchone()
                if not row:
                    raise ValueError(f"Ticket not found: {request.ticket_id}")
                
                conn.commit()
                
                # Log event
                self._log_event(
                    conn,
                    request.ticket_id,
                    "assigned",
                    {"agent_id": request.agent_id, "agent_name": request.agent_name}
                )
                
                logger.info(f"Assigned ticket {request.ticket_id} to agent {request.agent_id}")
                
                # Convert to EscalationTicket
                ticket = self._row_to_ticket(row)
            
            conn.close()
            return ticket
        
        except Exception as e:
            logger.error(f"Error assigning escalation: {e}")
            if conn:
                conn.close()
            raise
    
    async def resolve_escalation(
        self,
        request: ResolveEscalationRequest
    ) -> EscalationTicket:
        """
        Resolve escalation ticket
        
        Args:
            request: Resolution request
            
        Returns:
            Updated EscalationTicket
        """
        conn = get_db_connection()
        if not conn:
            raise Exception("Database connection not available")
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get ticket for metrics calculation
                cur.execute("""
                    SELECT created_at, assigned_at
                    FROM escalation_tickets
                    WHERE ticket_id = %s
                """, (request.ticket_id,))
                
                ticket_data = cur.fetchone()
                if not ticket_data:
                    raise ValueError(f"Ticket not found: {request.ticket_id}")
                
                # Calculate metrics
                now = datetime.now(timezone.utc)
                created_at = ticket_data['created_at']
                assigned_at = ticket_data['assigned_at']
                
                wait_time = int((assigned_at - created_at).total_seconds()) if assigned_at else None
                resolution_time = int((now - created_at).total_seconds())
                
                # Update ticket
                cur.execute("""
                    UPDATE escalation_tickets
                    SET status = %s,
                        resolved_at = NOW(),
                        resolution_notes = %s
                    WHERE ticket_id = %s
                    RETURNING *
                """, (
                    EscalationStatus.RESOLVED.value,
                    request.resolution_notes,
                    request.ticket_id
                ))
                
                row = cur.fetchone()
                conn.commit()
                
                # Insert metrics
                cur.execute("""
                    INSERT INTO escalation_metrics (
                        ticket_id, wait_time_seconds, resolution_time_seconds,
                        customer_satisfaction
                    ) VALUES (%s, %s, %s, %s)
                """, (
                    request.ticket_id,
                    wait_time,
                    resolution_time,
                    request.customer_satisfaction
                ))
                
                conn.commit()
                
                # Log event
                self._log_event(
                    conn,
                    request.ticket_id,
                    "resolved",
                    {
                        "resolution_time_seconds": resolution_time,
                        "satisfaction": request.customer_satisfaction
                    }
                )
                
                logger.info(f"Resolved ticket {request.ticket_id}")
                
                ticket = self._row_to_ticket(row)
            
            conn.close()
            return ticket
        
        except Exception as e:
            logger.error(f"Error resolving escalation: {e}")
            if conn:
                conn.close()
            raise
    
    async def get_ticket(self, ticket_id: str) -> Optional[EscalationTicket]:
        """Get escalation ticket by ID"""
        conn = get_db_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM escalation_tickets
                    WHERE ticket_id = %s
                """, (ticket_id,))
                
                row = cur.fetchone()
                if row:
                    ticket = self._row_to_ticket(row)
                    conn.close()
                    return ticket
            
            conn.close()
            return None
        
        except Exception as e:
            logger.error(f"Error getting ticket: {e}")
            if conn:
                conn.close()
            return None
    
    async def get_pending_escalations(
        self,
        bank_id: Optional[str] = None,
        limit: int = 50
    ) -> list[EscalationTicket]:
        """Get pending escalation tickets"""
        conn = get_db_connection()
        if not conn:
            return []
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if bank_id:
                    cur.execute("""
                        SELECT * FROM escalation_tickets
                        WHERE status = %s AND bank_id = %s
                        ORDER BY priority DESC, created_at ASC
                        LIMIT %s
                    """, (EscalationStatus.PENDING.value, bank_id, limit))
                else:
                    cur.execute("""
                        SELECT * FROM escalation_tickets
                        WHERE status = %s
                        ORDER BY priority DESC, created_at ASC
                        LIMIT %s
                    """, (EscalationStatus.PENDING.value, limit))
                
                rows = cur.fetchall()
                tickets = [self._row_to_ticket(row) for row in rows]
            
            conn.close()
            return tickets
        
        except Exception as e:
            logger.error(f"Error getting pending escalations: {e}")
            if conn:
                conn.close()
            return []
    
    async def get_metrics(
        self,
        bank_id: Optional[str] = None,
        days: int = 30
    ) -> EscalationMetrics:
        """Get escalation metrics"""
        conn = get_db_connection()
        if not conn:
            return EscalationMetrics(
                total_escalations=0,
                pending_escalations=0,
                average_wait_time_seconds=0.0,
                average_resolution_time_seconds=0.0,
                escalation_rate=0.0,
                top_trigger_types=[]
            )
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Total and pending escalations
                if bank_id:
                    cur.execute("""
                        SELECT 
                            COUNT(*) as total,
                            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending
                        FROM escalation_tickets
                        WHERE bank_id = %s
                        AND created_at >= NOW() - INTERVAL '%s days'
                    """, (bank_id, days))
                else:
                    cur.execute("""
                        SELECT 
                            COUNT(*) as total,
                            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending
                        FROM escalation_tickets
                        WHERE created_at >= NOW() - INTERVAL '%s days'
                    """, (days,))
                
                counts = cur.fetchone()
                
                # Average times
                cur.execute("""
                    SELECT 
                        AVG(wait_time_seconds) as avg_wait,
                        AVG(resolution_time_seconds) as avg_resolution,
                        AVG(customer_satisfaction) as avg_satisfaction
                    FROM escalation_metrics
                    WHERE recorded_at >= NOW() - INTERVAL '%s days'
                """, (days,))
                
                times = cur.fetchone()
                
                # Top trigger types
                if bank_id:
                    cur.execute("""
                        SELECT trigger_type, COUNT(*) as count
                        FROM escalation_tickets
                        WHERE bank_id = %s
                        AND created_at >= NOW() - INTERVAL '%s days'
                        GROUP BY trigger_type
                        ORDER BY count DESC
                        LIMIT 5
                    """, (bank_id, days))
                else:
                    cur.execute("""
                        SELECT trigger_type, COUNT(*) as count
                        FROM escalation_tickets
                        WHERE created_at >= NOW() - INTERVAL '%s days'
                        GROUP BY trigger_type
                        ORDER BY count DESC
                        LIMIT 5
                    """, (days,))
                
                triggers = cur.fetchall()
                
                metrics = EscalationMetrics(
                    total_escalations=counts['total'] or 0,
                    pending_escalations=counts['pending'] or 0,
                    average_wait_time_seconds=float(times['avg_wait'] or 0),
                    average_resolution_time_seconds=float(times['avg_resolution'] or 0),
                    escalation_rate=0.0,  # Would need total conversations to calculate
                    top_trigger_types=[
                        {"trigger_type": t['trigger_type'], "count": t['count']}
                        for t in triggers
                    ],
                    satisfaction_score=float(times['avg_satisfaction'] or 0) if times['avg_satisfaction'] else None
                )
            
            conn.close()
            return metrics
        
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            if conn:
                conn.close()
            return EscalationMetrics(
                total_escalations=0,
                pending_escalations=0,
                average_wait_time_seconds=0.0,
                average_resolution_time_seconds=0.0,
                escalation_rate=0.0,
                top_trigger_types=[]
            )
    
    def _generate_ticket_id(self, bank_id: str) -> str:
        """Generate unique ticket ID"""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        random_suffix = secrets.token_hex(4).upper()
        return f"ESC-{bank_id.upper()}-{timestamp}-{random_suffix}"
    
    def _estimate_wait_time(self, priority: EscalationPriority) -> int:
        """Estimate wait time in minutes based on priority"""
        # Simple estimation - in production, check actual queue
        wait_times = {
            EscalationPriority.URGENT: 2,
            EscalationPriority.HIGH: 5,
            EscalationPriority.MEDIUM: 10,
            EscalationPriority.LOW: 20
        }
        return wait_times.get(priority, 10)
    
    def _get_escalation_message(self, language: str, wait_time: int) -> str:
        """Get escalation confirmation message in user's language"""
        messages = {
            "en": f"I've connected you with a human agent. Estimated wait time: {wait_time} minutes. Please hold.",
            "am": f"ከሰው ወኪል ጋር አገናኝቼዎታለሁ። የሚገመተው የመጠበቂያ ጊዜ: {wait_time} ደቂቃዎች። እባክዎን ይጠብቁ።",
            "om": f"Nama bakka bu'aa waliin si qunnamsiiseera. Yeroo eegaa tilmaamame: daqiiqaa {wait_time}. Mee eegi.",
            "ti": f"ምስ ሰብ ወኪል ኣራኺበካ። ዝተገመተ ናይ ምጽባይ ግዜ: {wait_time} ደቓይቕ። በጃኻ ተጸበ።",
            "so": f"Waxaan kula xiriiriyay wakiil dadka ah. Waqtiga la qiyaasay ee sugitaanka: {wait_time} daqiiqo. Fadlan sug.",
        }
        return messages.get(language, messages["en"])
    
    def _log_event(self, conn, ticket_id: str, event_type: str, event_data: dict):
        """Log escalation event for audit trail"""
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO escalation_events (ticket_id, event_type, event_data)
                    VALUES (%s, %s, %s)
                """, (ticket_id, event_type, json.dumps(event_data)))
                conn.commit()
        except Exception as e:
            logger.error(f"Error logging event: {e}")
    
    def _row_to_ticket(self, row: dict) -> EscalationTicket:
        """Convert database row to EscalationTicket"""
        return EscalationTicket(
            ticket_id=row['ticket_id'],
            session_id=row['session_id'],
            customer_id=row['customer_id'],
            bank_id=row['bank_id'],
            status=EscalationStatus(row['status']),
            priority=EscalationPriority(row['priority']),
            reason=row['reason'],
            trigger_type=TriggerType(row['trigger_type']),
            assigned_to=row['assigned_to'],
            created_at=row['created_at'],
            assigned_at=row['assigned_at'],
            resolved_at=row['resolved_at'],
            resolution_notes=row['resolution_notes'],
            conversation_context=row['conversation_context'] or {},
            metadata=row['metadata'] or {}
        )


# Singleton instance
escalation_service = EscalationService()
