"""Analytics Agent - Natural language interface to banking intelligence data."""

from __future__ import annotations

import re
from typing import Optional

from app.modules.banking_intelligence.service import BankingIntelligenceService
from app.modules.banking_intelligence.models import (
    UnifiedDashboardRequest,
    PredictiveRequest,
    DecisionSupportRequest,
)


class AnalyticsAgent:
    """Detects analytics questions and routes to appropriate intelligence endpoints."""
    
    def __init__(self):
        self.intelligence_service = BankingIntelligenceService()
        
    def is_analytics_question(self, message: str) -> bool:
        """Detect if the message is asking for analytics/data."""
        message_lower = message.lower()
        
        analytics_keywords = [
            # Metrics
            "deposit", "loan", "npl", "customer", "revenue", "profit",
            "growth", "trend", "performance", "kpi", "metric",
            
            # Questions
            "how much", "how many", "what is", "what are", "show me",
            "tell me about", "give me", "what's our", "what's the",
            
            # Analytics terms
            "analytics", "data", "statistics", "stats", "numbers",
            "forecast", "predict", "projection", "trend", "analysis",
            
            # Comparisons
            "compare", "versus", "vs", "difference", "better", "worse",
            
            # Time-based
            "this month", "this quarter", "this year", "last month",
            "today", "yesterday", "week", "monthly", "quarterly",
        ]
        
        return any(keyword in message_lower for keyword in analytics_keywords)
    
    async def handle_analytics_query(
        self, 
        message: str, 
        bank_id: str = "dashen",
        language: str = "en"
    ) -> Optional[str]:
        """Process analytics question and return natural language answer."""
        
        message_lower = message.lower()
        
        # 1. Dashboard/KPI Questions
        if self._is_dashboard_query(message_lower):
            return await self._handle_dashboard_query(message_lower, bank_id, language)
        
        # 2. Forecast/Prediction Questions
        elif self._is_forecast_query(message_lower):
            return await self._handle_forecast_query(message_lower, bank_id, language)
        
        # 3. Strategic Decision Questions
        elif self._is_decision_query(message_lower):
            return await self._handle_decision_query(message, bank_id, language)
        
        # 4. General Analytics Summary
        else:
            return await self._handle_general_analytics(bank_id, language)
    
    def _is_dashboard_query(self, message: str) -> bool:
        """Check if asking for current metrics/KPIs."""
        patterns = [
            r"what('s| is) (our|the) (current|latest)?",
            r"show me (the )?(current|latest)?",
            r"how (much|many)",
            r"(deposit|loan|customer|npl|revenue|profit)",
            r"(kpi|metric|performance|trend)",
        ]
        return any(re.search(pattern, message) for pattern in patterns)
    
    def _is_forecast_query(self, message: str) -> bool:
        """Check if asking for predictions/forecasts."""
        forecast_keywords = [
            "forecast", "predict", "projection", "future", "next month",
            "next quarter", "will be", "expect", "anticipate", "outlook"
        ]
        return any(keyword in message for keyword in forecast_keywords)
    
    def _is_decision_query(self, message: str) -> bool:
        """Check if asking for strategic advice."""
        decision_keywords = [
            "should we", "should i", "recommend", "advice", "suggest",
            "what if", "consider", "expand", "launch", "invest"
        ]
        return any(keyword in message for keyword in decision_keywords)
    
    async def _handle_dashboard_query(
        self, 
        message: str, 
        bank_id: str,
        language: str
    ) -> str:
        """Get current KPIs and format as natural language."""
        
        request = UnifiedDashboardRequest(bankId=bank_id, timeRange="30d")
        dashboard = await self.intelligence_service.get_unified_dashboard(request, language=language)
        
        # Extract specific metric if asked
        if "deposit" in message:
            deposit_card = next((card for card in dashboard.kpi_cards if "Deposit" in card.title), None)
            if deposit_card:
                return self._format_kpi_answer(deposit_card, language)
        
        elif "customer" in message:
            customer_card = next((card for card in dashboard.kpi_cards if "Customer" in card.title), None)
            if customer_card:
                return self._format_kpi_answer(customer_card, language)
        
        elif "loan" in message:
            loan_card = next((card for card in dashboard.kpi_cards if "Loan" in card.title), None)
            if loan_card:
                return self._format_kpi_answer(loan_card, language)
        
        elif "npl" in message:
            npl_card = next((card for card in dashboard.kpi_cards if "NPL" in card.title), None)
            if npl_card:
                return self._format_kpi_answer(npl_card, language)
        
        elif "digital" in message:
            digital_card = next((card for card in dashboard.kpi_cards if "Digital" in card.title), None)
            if digital_card:
                return self._format_kpi_answer(digital_card, language)
        
        elif "fraud" in message:
            fraud_card = next((card for card in dashboard.kpi_cards if "Fraud" in card.title), None)
            if fraud_card:
                return self._format_kpi_answer(fraud_card, language)
        
        # General overview
        return self._format_dashboard_summary(dashboard, language)
    
    async def _handle_forecast_query(
        self,
        message: str,
        bank_id: str,
        language: str
    ) -> str:
        """Generate forecast and format as natural language."""
        
        # Detect metric from message
        metric_name = "deposit_growth"  # default
        
        if "customer" in message:
            metric_name = "customer_acquisition"
        elif "digital" in message:
            metric_name = "digital_adoption"
        elif "loan" in message:
            metric_name = "loan_demand"
        elif "fraud" in message:
            metric_name = "fraud_rate"
        elif "revenue" in message:
            metric_name = "revenue"
        
        # Detect time horizon
        horizon_days = 30  # default
        if "90 day" in message or "3 month" in message or "quarter" in message:
            horizon_days = 90
        elif "60 day" in message or "2 month" in message:
            horizon_days = 60
        
        request = PredictiveRequest(
            metricName=metric_name,
            horizonDays=horizon_days,
            bankId=bank_id
        )
        
        forecast = await self.intelligence_service.predict_metric(request, language=language)
        
        return self._format_forecast_answer(forecast, language)
    
    async def _handle_decision_query(
        self,
        message: str,
        bank_id: str,
        language: str
    ) -> str:
        """Provide strategic decision support."""
        
        request = DecisionSupportRequest(
            question=message,
            bankId=bank_id
        )
        
        decision = await self.intelligence_service.decision_support(request, language=language)
        
        return self._format_decision_answer(decision, language)
    
    async def _handle_general_analytics(self, bank_id: str, language: str) -> str:
        """Provide general analytics overview."""
        
        request = UnifiedDashboardRequest(bankId=bank_id, timeRange="30d")
        dashboard = await self.intelligence_service.get_unified_dashboard(request, language=language)
        
        return dashboard.insight_narrative
    
    def _format_kpi_answer(self, kpi_card, language: str) -> str:
        """Format a single KPI as natural language."""
        
        templates = {
            "en": f"{kpi_card.title} is currently {kpi_card.value}, {kpi_card.delta} from last period. This shows a {kpi_card.trend} trend.",
            "am": f"{kpi_card.title} በአሁኑ ጊዜ {kpi_card.value} ነው፣ ከቀዳሚው ጊዜ {kpi_card.delta}። ይህ {kpi_card.trend} አዝማሚያ ያሳያል።",
            "om": f"{kpi_card.title} yeroo ammaa {kpi_card.value} dha, yeroo darbe irraa {kpi_card.delta}. Kun kallattii {kpi_card.trend} agarsiisa.",
            "ti": f"{kpi_card.title} ኣብዚ እዋን {kpi_card.value} እዩ፣ ካብ ዝሓለፈ እዋን {kpi_card.delta}። እዚ ኣንፈት {kpi_card.trend} የርኢ።",
        }
        
        return templates.get(language, templates["en"])
    
    def _format_dashboard_summary(self, dashboard, language: str) -> str:
        """Format full dashboard as natural language summary."""
        
        # Get top 3 KPIs
        top_kpis = dashboard.kpi_cards[:3]
        kpi_summary = "\n".join([
            f"• {card.title}: {card.value} ({card.delta})"
            for card in top_kpis
        ])
        
        templates = {
            "en": f"Here's your current performance overview:\n\n{kpi_summary}\n\n{dashboard.insight_narrative}",
            "am": f"የአሁኑ አፈጻጸም ማጠቃለያ:\n\n{kpi_summary}\n\n{dashboard.insight_narrative}",
            "om": f"Cuunfaa raawwii ammaa:\n\n{kpi_summary}\n\n{dashboard.insight_narrative}",
            "ti": f"ናይ ሕጂ ኣፈጻጽማ ማሕበረ-ሓበሬታ:\n\n{kpi_summary}\n\n{dashboard.insight_narrative}",
        }
        
        return templates.get(language, templates["en"])
    
    def _format_forecast_answer(self, forecast, language: str) -> str:
        """Format forecast as natural language."""
        
        first_point = forecast.forecast[0]
        last_point = forecast.forecast[-1]
        
        templates = {
            "en": f"Based on predictive analytics:\n\n"
                  f"• Current forecast: {first_point.predicted_value:.1f}\n"
                  f"• {len(forecast.forecast)}-day outlook: {last_point.predicted_value:.1f}\n"
                  f"• Trend: {forecast.trend_direction}\n"
                  f"• Confidence: {int(forecast.confidence_level * 100)}%\n\n"
                  f"{forecast.narrative}\n\n"
                  f"Key risks: {', '.join(forecast.risk_factors[:2])}",
            
            "am": f"በትንበያ ትንታኔ መሠረት:\n\n"
                  f"• የአሁኑ ትንበያ: {first_point.predicted_value:.1f}\n"
                  f"• የ{len(forecast.forecast)}-ቀን እይታ: {last_point.predicted_value:.1f}\n"
                  f"• አዝማሚያ: {forecast.trend_direction}\n"
                  f"• እምነት: {int(forecast.confidence_level * 100)}%\n\n"
                  f"{forecast.narrative}",
        }
        
        return templates.get(language, templates["en"])
    
    def _format_decision_answer(self, decision, language: str) -> str:
        """Format decision support as natural language."""
        
        top_option = decision.recommended_options[0] if decision.recommended_options else None
        
        if not top_option:
            return decision.analysis
        
        templates = {
            "en": f"{decision.analysis}\n\n"
                  f"**Recommended Option:** {top_option.option}\n"
                  f"• Impact Score: {top_option.impact_score:.0f}/100\n"
                  f"• Risk Level: {top_option.risk_level}\n"
                  f"• Expected Outcome: {top_option.expected_outcome}\n\n"
                  f"**Pros:**\n" + "\n".join([f"  ✓ {pro}" for pro in top_option.pros[:3]]) + "\n\n"
                  f"**Cons:**\n" + "\n".join([f"  ✗ {con}" for con in top_option.cons[:3]]),
            
            "am": f"{decision.analysis}\n\n"
                  f"**የሚመከር አማራጭ:** {top_option.option}\n"
                  f"• የተፅዕኖ ነጥብ: {top_option.impact_score:.0f}/100\n"
                  f"• የአደጋ ደረጃ: {top_option.risk_level}\n"
                  f"• የሚጠበቀው ውጤት: {top_option.expected_outcome}",
        }
        
        return templates.get(language, templates["en"])


# Global instance
analytics_agent = AnalyticsAgent()
