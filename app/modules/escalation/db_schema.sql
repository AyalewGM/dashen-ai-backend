-- Escalation Service Database Schema
-- Creates tables for managing human escalation tickets

-- Escalation tickets table
CREATE TABLE IF NOT EXISTS escalation_tickets (
    id SERIAL PRIMARY KEY,
    ticket_id VARCHAR(50) UNIQUE NOT NULL,
    session_id VARCHAR(100) NOT NULL,
    customer_id VARCHAR(100),
    bank_id VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',
    reason TEXT,
    trigger_type VARCHAR(50),
    assigned_to VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    assigned_at TIMESTAMP,
    resolved_at TIMESTAMP,
    resolution_notes TEXT,
    conversation_context JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    
    -- Indexes for performance
    CONSTRAINT valid_status CHECK (status IN ('pending', 'assigned', 'in_progress', 'resolved', 'cancelled')),
    CONSTRAINT valid_priority CHECK (priority IN ('low', 'medium', 'high', 'urgent'))
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_escalation_tickets_session_id ON escalation_tickets(session_id);
CREATE INDEX IF NOT EXISTS idx_escalation_tickets_customer_id ON escalation_tickets(customer_id);
CREATE INDEX IF NOT EXISTS idx_escalation_tickets_bank_id ON escalation_tickets(bank_id);
CREATE INDEX IF NOT EXISTS idx_escalation_tickets_status ON escalation_tickets(status);
CREATE INDEX IF NOT EXISTS idx_escalation_tickets_assigned_to ON escalation_tickets(assigned_to);
CREATE INDEX IF NOT EXISTS idx_escalation_tickets_created_at ON escalation_tickets(created_at DESC);

-- Escalation metrics table
CREATE TABLE IF NOT EXISTS escalation_metrics (
    id SERIAL PRIMARY KEY,
    ticket_id VARCHAR(50) NOT NULL,
    wait_time_seconds INTEGER,
    resolution_time_seconds INTEGER,
    customer_satisfaction INTEGER CHECK (customer_satisfaction BETWEEN 1 AND 5),
    recorded_at TIMESTAMP DEFAULT NOW(),
    
    FOREIGN KEY (ticket_id) REFERENCES escalation_tickets(ticket_id) ON DELETE CASCADE
);

-- Create index on ticket_id for metrics
CREATE INDEX IF NOT EXISTS idx_escalation_metrics_ticket_id ON escalation_metrics(ticket_id);

-- Escalation events log (audit trail)
CREATE TABLE IF NOT EXISTS escalation_events (
    id SERIAL PRIMARY KEY,
    ticket_id VARCHAR(50) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB DEFAULT '{}',
    performed_by VARCHAR(100),
    timestamp TIMESTAMP DEFAULT NOW(),
    
    FOREIGN KEY (ticket_id) REFERENCES escalation_tickets(ticket_id) ON DELETE CASCADE
);

-- Create index on ticket_id for events
CREATE INDEX IF NOT EXISTS idx_escalation_events_ticket_id ON escalation_events(ticket_id);
CREATE INDEX IF NOT EXISTS idx_escalation_events_timestamp ON escalation_events(timestamp DESC);

-- Comments for documentation
COMMENT ON TABLE escalation_tickets IS 'Stores human escalation tickets from AI chatbot';
COMMENT ON TABLE escalation_metrics IS 'Tracks performance metrics for escalations';
COMMENT ON TABLE escalation_events IS 'Audit trail of all escalation events';
