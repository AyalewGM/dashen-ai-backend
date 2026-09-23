# Escalation Service Documentation

## Overview

The Escalation Service provides intelligent detection and management of human escalations from the AI chatbot. It automatically detects when a customer needs human assistance and creates tickets for agent assignment.

---

## Features

### 1. **Intelligent Trigger Detection**
- Explicit requests for human agent
- Frustration detection (sentiment analysis)
- Complaint identification
- Repeated question patterns
- Conversation timeout
- Low bot confidence (complex issues)

### 2. **Ticket Management**
- Create escalation tickets with full context
- Assign tickets to agents
- Track ticket status and resolution
- Audit trail of all events

### 3. **Multilingual Support**
- English, Amharic, Oromo, Tigrinya, Somali, Sidama
- Language-specific trigger keywords
- Multilingual escalation messages

### 4. **Analytics & Metrics**
- Total escalations
- Average wait time
- Average resolution time
- Customer satisfaction scores
- Top trigger types

---

## Architecture

```
┌─────────────────────────────────────┐
│      Conversation Service           │
│  (Chatbot detects triggers)         │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│     Escalation Detector             │
│  - Pattern analysis                 │
│  - Sentiment detection              │
│  - Confidence scoring               │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│     Escalation Service              │
│  - Ticket creation                  │
│  - Agent assignment                 │
│  - Status tracking                  │
└──────────────┬──────────────────────┘
               │
               ├──────────┬────────────┐
               ▼          ▼            ▼
         ┌─────────┐ ┌────────┐ ┌──────────┐
         │Database │ │ Notify │ │  Audit   │
         └─────────┘ └────────┘ └──────────┘
```

---

## API Endpoints

### **1. Detect Escalation**

```http
POST /api/escalation/detect
```

**Request:**
```json
{
  "conversation_history": [
    {
      "role": "user",
      "content": "I want to speak to a human agent",
      "timestamp": "2024-01-15T10:30:00Z",
      "language": "en"
    }
  ],
  "language": "en",
  "bot_confidence": 0.85
}
```

**Response:**
```json
{
  "should_escalate": true,
  "trigger_type": "explicit_request",
  "confidence": 0.95,
  "reason": "User explicitly requested human agent: 'human agent'",
  "priority": "high"
}
```

---

### **2. Create Escalation**

```http
POST /api/escalation/create
```

**Request:**
```json
{
  "session_id": "sess-123",
  "customer_id": "CUST001",
  "bank_id": "dashen",
  "reason": "Customer requested human agent",
  "trigger_type": "explicit_request",
  "priority": "high",
  "conversation_history": [...],
  "language": "en"
}
```

**Response:**
```json
{
  "ticket_id": "ESC-DASHEN-20240115103000-A1B2C3D4",
  "status": "pending",
  "estimated_wait_time_minutes": 5,
  "message": "I've connected you with a human agent. Estimated wait time: 5 minutes. Please hold."
}
```

---

### **3. Assign Escalation**

```http
POST /api/escalation/assign
```

**Request:**
```json
{
  "ticket_id": "ESC-DASHEN-20240115103000-A1B2C3D4",
  "agent_id": "agent-001",
  "agent_name": "John Doe"
}
```

**Response:**
```json
{
  "ticket_id": "ESC-DASHEN-20240115103000-A1B2C3D4",
  "status": "assigned",
  "assigned_to": "agent-001",
  "assigned_at": "2024-01-15T10:32:00Z",
  ...
}
```

---

### **4. Resolve Escalation**

```http
POST /api/escalation/resolve
```

**Request:**
```json
{
  "ticket_id": "ESC-DASHEN-20240115103000-A1B2C3D4",
  "resolution_notes": "Issue resolved, customer satisfied",
  "customer_satisfaction": 5
}
```

---

### **5. Get Ticket**

```http
GET /api/escalation/ticket/{ticket_id}
```

**Response:**
```json
{
  "ticket_id": "ESC-DASHEN-20240115103000-A1B2C3D4",
  "session_id": "sess-123",
  "customer_id": "CUST001",
  "bank_id": "dashen",
  "status": "resolved",
  "priority": "high",
  "reason": "Customer requested human agent",
  "trigger_type": "explicit_request",
  "assigned_to": "agent-001",
  "created_at": "2024-01-15T10:30:00Z",
  "assigned_at": "2024-01-15T10:32:00Z",
  "resolved_at": "2024-01-15T10:45:00Z",
  "resolution_notes": "Issue resolved",
  "conversation_context": {...}
}
```

---

### **6. Get Pending Escalations**

```http
GET /api/escalation/pending?bank_id=dashen&limit=50
```

**Response:**
```json
[
  {
    "ticket_id": "ESC-DASHEN-20240115103000-A1B2C3D4",
    "status": "pending",
    "priority": "high",
    "created_at": "2024-01-15T10:30:00Z",
    ...
  }
]
```

---

### **7. Get Metrics**

```http
GET /api/escalation/metrics?bank_id=dashen&days=30
```

**Response:**
```json
{
  "total_escalations": 245,
  "pending_escalations": 12,
  "average_wait_time_seconds": 180,
  "average_resolution_time_seconds": 900,
  "escalation_rate": 0.032,
  "top_trigger_types": [
    {"trigger_type": "explicit_request", "count": 120},
    {"trigger_type": "frustration_detected", "count": 65},
    {"trigger_type": "repeated_questions", "count": 40}
  ],
  "satisfaction_score": 4.2
}
```

---

## Usage Examples

### **Example 1: Integrate with Chatbot**

```python
from app.modules.escalation import escalation_service
from app.modules.escalation.models import ConversationMessage

# In your chatbot service
async def handle_message(session_id, message, conversation_history):
    # Check if escalation is needed
    trigger = await escalation_service.detect_escalation_needed(
        conversation_history=conversation_history,
        language="en",
        bot_confidence=0.75
    )
    
    if trigger.should_escalate:
        # Create escalation ticket
        request = CreateEscalationRequest(
            session_id=session_id,
            bank_id="dashen",
            reason=trigger.reason,
            trigger_type=trigger.trigger_type,
            priority=trigger.priority,
            conversation_history=conversation_history,
            language="en"
        )
        
        response = await escalation_service.create_escalation(request)
        
        return {
            "escalated": True,
            "ticket_id": response.ticket_id,
            "message": response.message
        }
    
    # Continue normal chatbot flow
    return {"escalated": False}
```

---

### **Example 2: Agent Dashboard**

```python
# Get pending escalations for agent dashboard
async def get_agent_queue(bank_id: str):
    tickets = await escalation_service.get_pending_escalations(
        bank_id=bank_id,
        limit=50
    )
    
    return {
        "pending_count": len(tickets),
        "tickets": tickets
    }
```

---

### **Example 3: Assign to Agent**

```python
# When agent accepts ticket
async def assign_to_agent(ticket_id: str, agent_id: str):
    request = AssignEscalationRequest(
        ticket_id=ticket_id,
        agent_id=agent_id,
        agent_name="John Doe"
    )
    
    ticket = await escalation_service.assign_escalation(request)
    
    # Notify agent with conversation context
    conversation = ticket.conversation_context
    return {
        "ticket": ticket,
        "conversation": conversation
    }
```

---

## Trigger Detection Logic

### **1. Explicit Request**
- Keywords: "human", "agent", "person", "representative"
- Confidence: 95%
- Priority: HIGH

### **2. Frustration Detection**
- Negative keywords: "frustrated", "angry", "terrible", "useless"
- Excessive punctuation: "!!!", "???"
- ALL CAPS words
- Confidence: 70-95%
- Priority: HIGH

### **3. Complaint**
- Keywords: "complaint", "complain", "report", "problem"
- Multiple complaint indicators
- Confidence: 85%
- Priority: HIGH

### **4. Repeated Questions**
- Same question asked 2+ times
- Similarity threshold: 70%
- Confidence: 80%
- Priority: MEDIUM

### **5. Conversation Timeout**
- More than 20 messages
- Confidence: 80%
- Priority: MEDIUM

### **6. Complex Issue**
- Bot confidence < 50%
- Confidence: 100 - bot_confidence
- Priority: MEDIUM

---

## Database Schema

### **escalation_tickets**
```sql
- id (SERIAL PRIMARY KEY)
- ticket_id (VARCHAR UNIQUE)
- session_id (VARCHAR)
- customer_id (VARCHAR)
- bank_id (VARCHAR)
- status (VARCHAR) -- pending, assigned, in_progress, resolved, cancelled
- priority (VARCHAR) -- low, medium, high, urgent
- reason (TEXT)
- trigger_type (VARCHAR)
- assigned_to (VARCHAR)
- created_at (TIMESTAMP)
- assigned_at (TIMESTAMP)
- resolved_at (TIMESTAMP)
- resolution_notes (TEXT)
- conversation_context (JSONB)
- metadata (JSONB)
```

### **escalation_metrics**
```sql
- id (SERIAL PRIMARY KEY)
- ticket_id (VARCHAR FK)
- wait_time_seconds (INTEGER)
- resolution_time_seconds (INTEGER)
- customer_satisfaction (INTEGER 1-5)
- recorded_at (TIMESTAMP)
```

### **escalation_events**
```sql
- id (SERIAL PRIMARY KEY)
- ticket_id (VARCHAR FK)
- event_type (VARCHAR)
- event_data (JSONB)
- performed_by (VARCHAR)
- timestamp (TIMESTAMP)
```

---

## Configuration

### **Detector Settings**

```python
# In detector.py
min_messages_for_pattern = 3  # Minimum messages to detect patterns
max_conversation_length = 20  # Max messages before timeout
similarity_threshold = 0.7    # Similarity for repeated questions
```

### **Wait Time Estimation**

```python
# In service.py
wait_times = {
    EscalationPriority.URGENT: 2,   # 2 minutes
    EscalationPriority.HIGH: 5,     # 5 minutes
    EscalationPriority.MEDIUM: 10,  # 10 minutes
    EscalationPriority.LOW: 20      # 20 minutes
}
```

---

## Testing

Run unit tests:
```bash
pytest tests/test_escalation.py -v
```

Test coverage:
```bash
pytest tests/test_escalation.py --cov=app.modules.escalation
```

---

## Monitoring

### **Key Metrics to Track**
- Escalation rate (% of conversations escalated)
- Average wait time
- Average resolution time
- Customer satisfaction scores
- Top trigger types
- Agent utilization

### **Alerts**
- High pending queue (> 20 tickets)
- Long wait times (> 15 minutes)
- Low satisfaction scores (< 3.0)
- High escalation rate (> 10%)

---

## Best Practices

1. **Monitor escalation rate** - Should be < 5% of conversations
2. **Quick assignment** - Assign tickets within 2 minutes
3. **Context transfer** - Always provide full conversation history
4. **Follow up** - Collect satisfaction scores
5. **Continuous improvement** - Analyze trigger types to improve bot

---

## Troubleshooting

### **Issue: High false positive rate**
- Adjust trigger detection thresholds
- Review keyword lists
- Tune similarity threshold

### **Issue: Missed escalations**
- Lower confidence thresholds
- Add more trigger keywords
- Enable complex issue detection

### **Issue: Long wait times**
- Increase agent capacity
- Implement priority routing
- Add self-service options

---

## Future Enhancements

1. **Sentiment Analysis** - Use ML for better frustration detection
2. **Proactive Escalation** - Predict escalation before it happens
3. **Smart Routing** - Route to specialized agents
4. **Callback System** - Offer callback instead of waiting
5. **Chat Transfer** - Seamless live chat handoff
6. **Agent Performance** - Track agent metrics and performance

---

## Support

For issues or questions:
- Email: support@goozam.com
- Slack: #escalation-service
- Docs: https://docs.goozam.com/escalation
