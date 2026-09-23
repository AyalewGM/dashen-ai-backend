"""
Escalation Trigger Detector
Analyzes conversation to detect when human escalation is needed
"""

import re
from typing import Optional

from .models import (
    ConversationMessage,
    EscalationPriority,
    EscalationTrigger,
    TriggerType,
)


class EscalationDetector:
    """Detects when a conversation should be escalated to human agent"""
    
    # Keywords that indicate explicit request for human
    HUMAN_REQUEST_KEYWORDS = {
        "en": ["human", "agent", "person", "representative", "speak to someone", "talk to someone", "real person"],
        "am": ["ሰው", "ወኪል", "ተወካይ", "ሰው ማነጋገር", "እውነተኛ ሰው"],
        "om": ["nama", "bakka bu'aa", "nama dhugaa"],
        "ti": ["ሰብ", "ወኪል"],
        "so": ["qof", "wakiil", "qof run ah"],
    }
    
    # Keywords indicating frustration
    FRUSTRATION_KEYWORDS = {
        "en": ["frustrated", "angry", "useless", "terrible", "worst", "stupid", "waste of time", "not helping"],
        "am": ["ተበሳጭቻለሁ", "ቁጣ", "ጥሩ አይደለም", "መጥፎ", "ጊዜ ማባከን"],
        "om": ["aarii", "badaa", "faayidaa hin qabu"],
    }
    
    # Keywords indicating complaints
    COMPLAINT_KEYWORDS = {
        "en": ["complaint", "complain", "report", "problem", "issue", "wrong", "error", "mistake"],
        "am": ["ቅሬታ", "ችግር", "ስህተት", "ተሳስቷል"],
        "om": ["komii", "rakkoo", "dogoggora"],
    }
    
    def __init__(self):
        self.min_messages_for_pattern = 3
        self.max_conversation_length = 20
        self.similarity_threshold = 0.7
    
    def detect_escalation_trigger(
        self,
        conversation_history: list[ConversationMessage],
        language: str = "en"
    ) -> EscalationTrigger:
        """
        Analyze conversation and detect if escalation is needed
        
        Args:
            conversation_history: List of conversation messages
            language: Conversation language
            
        Returns:
            EscalationTrigger with detection results
        """
        if not conversation_history:
            return EscalationTrigger(should_escalate=False, confidence=0.0)
        
        # Get last user message
        user_messages = [msg for msg in conversation_history if msg.role == "user"]
        if not user_messages:
            return EscalationTrigger(should_escalate=False, confidence=0.0)
        
        last_message = user_messages[-1].content.lower()
        
        # Check 1: Explicit request for human
        explicit_trigger = self._check_explicit_request(last_message, language)
        if explicit_trigger.should_escalate:
            return explicit_trigger
        
        # Check 2: Frustration detected
        frustration_trigger = self._check_frustration(last_message, language)
        if frustration_trigger.should_escalate:
            return frustration_trigger
        
        # Check 3: Complaint detected
        complaint_trigger = self._check_complaint(last_message, language)
        if complaint_trigger.should_escalate:
            return complaint_trigger
        
        # Check 4: Repeated questions
        if len(user_messages) >= self.min_messages_for_pattern:
            repeated_trigger = self._check_repeated_questions(user_messages)
            if repeated_trigger.should_escalate:
                return repeated_trigger
        
        # Check 5: Conversation too long (timeout)
        if len(conversation_history) >= self.max_conversation_length:
            return EscalationTrigger(
                should_escalate=True,
                trigger_type=TriggerType.TIMEOUT,
                confidence=0.8,
                reason=f"Conversation exceeded {self.max_conversation_length} messages",
                priority=EscalationPriority.MEDIUM
            )
        
        # No escalation needed
        return EscalationTrigger(should_escalate=False, confidence=0.0)
    
    def _check_explicit_request(self, message: str, language: str) -> EscalationTrigger:
        """Check if user explicitly requests human agent"""
        keywords = self.HUMAN_REQUEST_KEYWORDS.get(language, self.HUMAN_REQUEST_KEYWORDS["en"])
        
        for keyword in keywords:
            if keyword in message:
                return EscalationTrigger(
                    should_escalate=True,
                    trigger_type=TriggerType.EXPLICIT_REQUEST,
                    confidence=0.95,
                    reason=f"User explicitly requested human agent: '{keyword}'",
                    priority=EscalationPriority.HIGH
                )
        
        return EscalationTrigger(should_escalate=False, confidence=0.0)
    
    def _check_frustration(self, message: str, language: str) -> EscalationTrigger:
        """Check for frustration indicators"""
        keywords = self.FRUSTRATION_KEYWORDS.get(language, self.FRUSTRATION_KEYWORDS["en"])
        
        # Check for frustration keywords
        frustration_count = sum(1 for keyword in keywords if keyword in message)
        
        # Check for excessive punctuation (!!!, ???)
        excessive_punctuation = len(re.findall(r'[!?]{2,}', message))
        
        # Check for ALL CAPS (shouting)
        words = message.split()
        caps_ratio = sum(1 for word in words if word.isupper() and len(word) > 2) / max(len(words), 1)
        
        # Calculate frustration score
        frustration_score = (
            (frustration_count * 0.4) +
            (excessive_punctuation * 0.3) +
            (caps_ratio * 0.3)
        )
        
        if frustration_score >= 0.5:
            return EscalationTrigger(
                should_escalate=True,
                trigger_type=TriggerType.FRUSTRATION_DETECTED,
                confidence=min(frustration_score, 0.95),
                reason="Customer frustration detected in message",
                priority=EscalationPriority.HIGH
            )
        
        return EscalationTrigger(should_escalate=False, confidence=0.0)
    
    def _check_complaint(self, message: str, language: str) -> EscalationTrigger:
        """Check for complaint indicators"""
        keywords = self.COMPLAINT_KEYWORDS.get(language, self.COMPLAINT_KEYWORDS["en"])
        
        complaint_count = sum(1 for keyword in keywords if keyword in message)
        
        if complaint_count >= 2:
            return EscalationTrigger(
                should_escalate=True,
                trigger_type=TriggerType.COMPLAINT,
                confidence=0.85,
                reason="Customer complaint detected",
                priority=EscalationPriority.HIGH
            )
        
        return EscalationTrigger(should_escalate=False, confidence=0.0)
    
    def _check_repeated_questions(self, user_messages: list[ConversationMessage]) -> EscalationTrigger:
        """Check if user is asking the same question repeatedly"""
        if len(user_messages) < self.min_messages_for_pattern:
            return EscalationTrigger(should_escalate=False, confidence=0.0)
        
        # Get last 5 messages
        recent_messages = user_messages[-5:]
        
        # Simple similarity check: count common words
        for i in range(len(recent_messages) - 1):
            msg1_words = set(recent_messages[i].content.lower().split())
            msg2_words = set(recent_messages[i + 1].content.lower().split())
            
            if not msg1_words or not msg2_words:
                continue
            
            # Calculate Jaccard similarity
            intersection = msg1_words & msg2_words
            union = msg1_words | msg2_words
            similarity = len(intersection) / len(union) if union else 0
            
            if similarity >= self.similarity_threshold:
                return EscalationTrigger(
                    should_escalate=True,
                    trigger_type=TriggerType.REPEATED_QUESTIONS,
                    confidence=0.8,
                    reason="User asking similar questions repeatedly",
                    priority=EscalationPriority.MEDIUM
                )
        
        return EscalationTrigger(should_escalate=False, confidence=0.0)
    
    def check_complex_issue(self, bot_confidence: float) -> EscalationTrigger:
        """Check if issue is too complex for bot (low confidence)"""
        if bot_confidence < 0.5:
            return EscalationTrigger(
                should_escalate=True,
                trigger_type=TriggerType.COMPLEX_ISSUE,
                confidence=1.0 - bot_confidence,
                reason=f"Bot confidence too low: {bot_confidence:.2f}",
                priority=EscalationPriority.MEDIUM
            )
        
        return EscalationTrigger(should_escalate=False, confidence=0.0)


# Singleton instance
detector = EscalationDetector()
