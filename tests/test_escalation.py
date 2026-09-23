"""
Unit Tests for Escalation Service
Tests escalation detection, ticket creation, and management
"""

import pytest
from datetime import datetime

from app.modules.escalation.detector import EscalationDetector
from app.modules.escalation.models import (
    ConversationMessage,
    CreateEscalationRequest,
    EscalationPriority,
    TriggerType,
)


class TestEscalationDetector:
    """Test escalation trigger detection"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.detector = EscalationDetector()
    
    def test_explicit_request_english(self):
        """Test detection of explicit human request in English"""
        messages = [
            ConversationMessage(
                role="user",
                content="I want to speak to a human agent",
                timestamp=datetime.now().isoformat()
            )
        ]
        
        trigger = self.detector.detect_escalation_trigger(messages, "en")
        
        assert trigger.should_escalate is True
        assert trigger.trigger_type == TriggerType.EXPLICIT_REQUEST
        assert trigger.confidence >= 0.9
        assert trigger.priority == EscalationPriority.HIGH
    
    def test_explicit_request_amharic(self):
        """Test detection of explicit human request in Amharic"""
        messages = [
            ConversationMessage(
                role="user",
                content="ሰው ማነጋገር እፈልጋለሁ",
                timestamp=datetime.now().isoformat()
            )
        ]
        
        trigger = self.detector.detect_escalation_trigger(messages, "am")
        
        assert trigger.should_escalate is True
        assert trigger.trigger_type == TriggerType.EXPLICIT_REQUEST
    
    def test_frustration_detection(self):
        """Test detection of customer frustration"""
        messages = [
            ConversationMessage(
                role="user",
                content="This is TERRIBLE!!! You're not helping at all!!!",
                timestamp=datetime.now().isoformat()
            )
        ]
        
        trigger = self.detector.detect_escalation_trigger(messages, "en")
        
        assert trigger.should_escalate is True
        assert trigger.trigger_type == TriggerType.FRUSTRATION_DETECTED
        assert trigger.priority == EscalationPriority.HIGH
    
    def test_complaint_detection(self):
        """Test detection of customer complaint"""
        messages = [
            ConversationMessage(
                role="user",
                content="I want to file a complaint about this problem",
                timestamp=datetime.now().isoformat()
            )
        ]
        
        trigger = self.detector.detect_escalation_trigger(messages, "en")
        
        assert trigger.should_escalate is True
        assert trigger.trigger_type == TriggerType.COMPLAINT
    
    def test_repeated_questions(self):
        """Test detection of repeated questions"""
        messages = [
            ConversationMessage(
                role="user",
                content="What is my account balance?",
                timestamp=datetime.now().isoformat()
            ),
            ConversationMessage(
                role="assistant",
                content="I can help you check your balance.",
                timestamp=datetime.now().isoformat()
            ),
            ConversationMessage(
                role="user",
                content="What is my account balance?",
                timestamp=datetime.now().isoformat()
            ),
            ConversationMessage(
                role="assistant",
                content="Let me help you with that.",
                timestamp=datetime.now().isoformat()
            ),
            ConversationMessage(
                role="user",
                content="What is my account balance?",
                timestamp=datetime.now().isoformat()
            )
        ]
        
        trigger = self.detector.detect_escalation_trigger(messages, "en")
        
        assert trigger.should_escalate is True
        assert trigger.trigger_type == TriggerType.REPEATED_QUESTIONS
    
    def test_conversation_timeout(self):
        """Test detection of overly long conversation"""
        messages = [
            ConversationMessage(
                role="user" if i % 2 == 0 else "assistant",
                content=f"Message {i}",
                timestamp=datetime.now().isoformat()
            )
            for i in range(25)
        ]
        
        trigger = self.detector.detect_escalation_trigger(messages, "en")
        
        assert trigger.should_escalate is True
        assert trigger.trigger_type == TriggerType.TIMEOUT
    
    def test_low_bot_confidence(self):
        """Test escalation on low bot confidence"""
        trigger = self.detector.check_complex_issue(bot_confidence=0.3)
        
        assert trigger.should_escalate is True
        assert trigger.trigger_type == TriggerType.COMPLEX_ISSUE
    
    def test_no_escalation_needed(self):
        """Test normal conversation with no escalation"""
        messages = [
            ConversationMessage(
                role="user",
                content="Hello, how are you?",
                timestamp=datetime.now().isoformat()
            ),
            ConversationMessage(
                role="assistant",
                content="I'm doing well, how can I help you?",
                timestamp=datetime.now().isoformat()
            )
        ]
        
        trigger = self.detector.detect_escalation_trigger(messages, "en")
        
        assert trigger.should_escalate is False


class TestEscalationModels:
    """Test escalation data models"""
    
    def test_create_escalation_request(self):
        """Test creating escalation request"""
        request = CreateEscalationRequest(
            session_id="test-session-123",
            customer_id="CUST001",
            bank_id="dashen",
            reason="Customer requested human agent",
            trigger_type=TriggerType.EXPLICIT_REQUEST,
            priority=EscalationPriority.HIGH,
            conversation_history=[
                ConversationMessage(
                    role="user",
                    content="I want to speak to a human",
                    timestamp=datetime.now().isoformat()
                )
            ],
            language="en"
        )
        
        assert request.session_id == "test-session-123"
        assert request.bank_id == "dashen"
        assert request.trigger_type == TriggerType.EXPLICIT_REQUEST
        assert len(request.conversation_history) == 1
    
    def test_escalation_priority_levels(self):
        """Test escalation priority enum"""
        assert EscalationPriority.URGENT.value == "urgent"
        assert EscalationPriority.HIGH.value == "high"
        assert EscalationPriority.MEDIUM.value == "medium"
        assert EscalationPriority.LOW.value == "low"
    
    def test_trigger_types(self):
        """Test trigger type enum"""
        assert TriggerType.EXPLICIT_REQUEST.value == "explicit_request"
        assert TriggerType.FRUSTRATION_DETECTED.value == "frustration_detected"
        assert TriggerType.COMPLAINT.value == "complaint"
        assert TriggerType.REPEATED_QUESTIONS.value == "repeated_questions"
        assert TriggerType.TIMEOUT.value == "timeout"
        assert TriggerType.COMPLEX_ISSUE.value == "complex_issue"


# Integration tests would go here
# These would test the full service with database
# Skipped for now as they require database setup

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
