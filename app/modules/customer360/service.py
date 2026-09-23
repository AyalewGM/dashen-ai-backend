from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from typing import Any

from .models import (
    AccountSummary,
    ActionType,
    BehavioralInsight,
    ChannelBehavior,
    ChannelType,
    ChurnRiskAssessment,
    Customer360Request,
    Customer360Response,
    CustomerBehaviorAnalysis,
    CustomerDemographics,
    CustomerSearchRequest,
    CustomerSearchResponse,
    CustomerSearchResult,
    CustomerSegment,
    FinancialHealth,
    InteractionTimeline,
    LifeEvent,
    NextBestAction,
    ProductType,
    RiskLevel,
    TransactionPattern,
    UnifiedCustomerProfile,
)


class Customer360Service:
    """Service for unified customer profiles, insights, and next-best actions"""

    def __init__(self):
        self.customer_data = self._initialize_sample_data()

    def _initialize_sample_data(self) -> dict[str, Any]:
        """Initialize sample customer data for demonstration"""
        return {
            "CUST001": {
                "full_name": "Abebe Kebede",
                "segment": CustomerSegment.VIP,
                "location": "Addis Ababa",
                "age": 45,
                "occupation": "Business Owner",
                "income_bracket": "High",
                "customer_since": "2018-03-15",
            },
            "CUST002": {
                "full_name": "Tigist Haile",
                "segment": CustomerSegment.ACTIVE,
                "location": "Bahir Dar",
                "age": 32,
                "occupation": "Software Engineer",
                "income_bracket": "Medium-High",
                "customer_since": "2020-07-22",
            },
            "CUST003": {
                "full_name": "Yohannes Tesfaye",
                "segment": CustomerSegment.AT_RISK,
                "location": "Mekelle",
                "age": 28,
                "occupation": "Teacher",
                "income_bracket": "Medium",
                "customer_since": "2019-11-10",
            },
        }

    def get_customer_360(
        self, request: Customer360Request, bank_id: str = "dashen"
    ) -> Customer360Response:
        """Get comprehensive 360-degree customer view"""
        customer_id = request.customer_id

        # Generate deterministic data based on customer_id
        seed = int(hashlib.sha256(customer_id.encode()).hexdigest(), 16) % 10000

        # Get or generate customer base data
        base_data = self.customer_data.get(
            customer_id,
            {
                "full_name": f"Customer {customer_id[-4:]}",
                "segment": self._determine_segment(seed),
                "location": ["Addis Ababa", "Bahir Dar", "Mekelle", "Hawassa"][seed % 4],
                "age": 25 + (seed % 40),
                "occupation": ["Business Owner", "Employee", "Self-Employed", "Student"][seed % 4],
                "income_bracket": ["Low", "Medium", "Medium-High", "High"][seed % 4],
                "customer_since": f"{2015 + (seed % 8)}-{1 + (seed % 12):02d}-{1 + (seed % 28):02d}",
            },
        )

        # Build unified profile
        profile = self._build_profile(customer_id, base_data, seed)

        # Build behavioral analysis
        behavior = self._build_behavior_analysis(customer_id, seed, request.time_range_days)

        # Assess churn risk
        churn_risk = self._assess_churn_risk(customer_id, seed, behavior)

        # Generate next-best actions
        next_best_actions = self._generate_next_best_actions(
            customer_id, profile, behavior, churn_risk, seed
        )

        # Get recent interactions
        recent_interactions = self._get_recent_interactions(customer_id, seed, request.time_range_days)

        return Customer360Response(
            profile=profile,
            behavior=behavior,
            churn_risk=churn_risk,
            next_best_actions=next_best_actions,
            recent_interactions=recent_interactions,
            metadata={
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "bank_id": bank_id,
                "time_range_days": request.time_range_days,
            },
        )

    def _determine_segment(self, seed: int) -> CustomerSegment:
        """Determine customer segment based on seed"""
        segments = [
            CustomerSegment.VIP,
            CustomerSegment.ACTIVE,
            CustomerSegment.NEW,
            CustomerSegment.DORMANT,
            CustomerSegment.AT_RISK,
            CustomerSegment.SME,
        ]
        return segments[seed % len(segments)]

    def _build_profile(
        self, customer_id: str, base_data: dict[str, Any], seed: int
    ) -> UnifiedCustomerProfile:
        """Build unified customer profile"""
        demographics = CustomerDemographics(
            age=base_data["age"],
            location=base_data["location"],
            occupation=base_data.get("occupation"),
            income_bracket=base_data.get("income_bracket"),
        )

        # Generate accounts
        accounts = []
        num_accounts = 1 + (seed % 4)
        product_types = [ProductType.SAVINGS, ProductType.CURRENT, ProductType.LOAN, ProductType.CREDIT_CARD]

        for i in range(num_accounts):
            balance = 5000 + (seed * (i + 1) % 500000)
            accounts.append(
                AccountSummary(
                    product_type=product_types[i % len(product_types)],
                    account_number=f"{customer_id}-{i+1:03d}",
                    balance=float(balance),
                    opened_date=f"{2018 + i}-{1 + (seed % 12):02d}-01",
                    status="Active",
                    monthly_activity=float(1000 + (seed * i % 50000)),
                )
            )

        # Financial health
        credit_score = 600 + (seed % 250)
        debt_to_income = 0.1 + ((seed % 40) / 100)
        savings_rate = 0.05 + ((seed % 25) / 100)
        payment_score = 70 + (seed % 30)
        health_score = (credit_score / 10 + (1 - debt_to_income) * 50 + savings_rate * 100 + payment_score) / 3

        financial_health = FinancialHealth(
            credit_score=credit_score,
            debt_to_income_ratio=round(debt_to_income, 2),
            savings_rate=round(savings_rate, 2),
            payment_history_score=float(payment_score),
            overall_health_score=round(health_score, 1),
            health_trend=["improving", "stable", "declining"][seed % 3],
        )

        total_value = sum(acc.balance for acc in accounts)
        last_interaction = (datetime.utcnow() - timedelta(days=seed % 30)).isoformat() + "Z"

        return UnifiedCustomerProfile(
            customer_id=customer_id,
            full_name=base_data["full_name"],
            segment=base_data["segment"],
            demographics=demographics,
            accounts=accounts,
            financial_health=financial_health,
            total_relationship_value=round(total_value, 2),
            customer_since=base_data["customer_since"],
            last_interaction=last_interaction,
        )

    def _build_behavior_analysis(
        self, customer_id: str, seed: int, time_range_days: int
    ) -> CustomerBehaviorAnalysis:
        """Build behavioral analysis"""
        # Transaction patterns
        transaction_patterns = TransactionPattern(
            avg_monthly_spend=float(2000 + (seed % 8000)),
            avg_transaction_value=float(50 + (seed % 500)),
            top_categories=[
                {"category": "Groceries", "amount": 800 + (seed % 400), "percentage": 35},
                {"category": "Transport", "amount": 400 + (seed % 300), "percentage": 20},
                {"category": "Utilities", "amount": 300 + (seed % 200), "percentage": 15},
                {"category": "Entertainment", "amount": 200 + (seed % 300), "percentage": 12},
            ],
            preferred_merchants=["Shoa Supermarket", "Total Gas Station", "Ethio Telecom"],
            peak_transaction_hours=[9, 12, 18],
        )

        # Channel preferences
        channels = [
            ChannelType.MOBILE_APP,
            ChannelType.BRANCH,
            ChannelType.ATM,
            ChannelType.CALL_CENTER,
        ]
        channel_behaviors = []
        for i, channel in enumerate(channels):
            usage = 50 - (i * 10) + (seed % 30)
            channel_behaviors.append(
                ChannelBehavior(
                    channel=channel,
                    usage_count=usage,
                    last_used=(datetime.utcnow() - timedelta(days=i + (seed % 10))).isoformat() + "Z",
                    preference_score=round(1.0 - (i * 0.2), 2),
                )
            )

        # Behavioral insights
        insights = self._generate_behavioral_insights(customer_id, seed)

        # Life events
        life_events = self._detect_life_events(customer_id, seed)

        engagement_score = 60 + (seed % 40)
        loyalty_score = 55 + (seed % 45)

        return CustomerBehaviorAnalysis(
            customer_id=customer_id,
            transaction_patterns=transaction_patterns,
            channel_preferences=channel_behaviors,
            engagement_score=float(engagement_score),
            loyalty_score=float(loyalty_score),
            behavioral_insights=insights,
            detected_life_events=life_events,
        )

    def _generate_behavioral_insights(self, customer_id: str, seed: int) -> list[BehavioralInsight]:
        """Generate behavioral insights"""
        insights_pool = [
            {
                "type": "spending_increase",
                "title": "Increased Spending Pattern",
                "description": "Customer spending has increased by 25% in the last 30 days, primarily in groceries and utilities.",
                "impact": "medium",
            },
            {
                "type": "channel_shift",
                "title": "Digital Channel Adoption",
                "description": "Customer has shifted from branch to mobile app for 80% of transactions.",
                "impact": "high",
            },
            {
                "type": "savings_decline",
                "title": "Declining Savings Rate",
                "description": "Savings rate has decreased from 15% to 8% over the last quarter.",
                "impact": "high",
            },
            {
                "type": "payment_consistency",
                "title": "Consistent Payment Behavior",
                "description": "Customer maintains excellent payment history with 100% on-time payments.",
                "impact": "low",
            },
        ]

        selected_insights = []
        num_insights = 2 + (seed % 3)
        for i in range(num_insights):
            insight_data = insights_pool[i % len(insights_pool)]
            selected_insights.append(
                BehavioralInsight(
                    insight_type=insight_data["type"],
                    title=insight_data["title"],
                    description=insight_data["description"],
                    confidence=0.7 + ((seed + i) % 30) / 100,
                    detected_at=(datetime.utcnow() - timedelta(days=i * 5)).isoformat() + "Z",
                    impact=insight_data["impact"],
                )
            )

        return selected_insights

    def _detect_life_events(self, customer_id: str, seed: int) -> list[LifeEvent]:
        """Detect potential life events"""
        events_pool = [
            {
                "type": "salary_increase",
                "description": "Detected 30% increase in monthly deposits, indicating potential salary raise or bonus.",
                "products": ["Investment Account", "Premium Credit Card"],
            },
            {
                "type": "major_purchase",
                "description": "Large transaction of 500,000 ETB detected, possibly for property or vehicle purchase.",
                "products": ["Auto Loan", "Home Loan"],
            },
            {
                "type": "business_expansion",
                "description": "Increased business-related transactions suggest business growth.",
                "products": ["Business Loan", "Merchant Services"],
            },
        ]

        if seed % 3 == 0:
            event_data = events_pool[seed % len(events_pool)]
            return [
                LifeEvent(
                    event_type=event_data["type"],
                    detected_at=(datetime.utcnow() - timedelta(days=seed % 15)).isoformat() + "Z",
                    confidence=0.75 + ((seed % 20) / 100),
                    description=event_data["description"],
                    recommended_products=event_data["products"],
                )
            ]
        return []

    def _assess_churn_risk(
        self, customer_id: str, seed: int, behavior: CustomerBehaviorAnalysis
    ) -> ChurnRiskAssessment:
        """Assess customer churn risk"""
        # Calculate risk based on engagement and loyalty
        risk_score = 100 - (behavior.engagement_score + behavior.loyalty_score) / 2

        if risk_score < 25:
            risk_level = RiskLevel.LOW
            factors = ["High engagement", "Strong loyalty", "Regular transactions"]
            actions = ["Continue excellent service", "Offer loyalty rewards"]
        elif risk_score < 50:
            risk_level = RiskLevel.MEDIUM
            factors = ["Moderate engagement", "Declining transaction frequency"]
            actions = ["Send personalized offers", "Schedule relationship manager call"]
        elif risk_score < 75:
            risk_level = RiskLevel.HIGH
            factors = ["Low engagement", "Reduced balance", "Competitor activity detected"]
            actions = ["Urgent retention campaign", "Exclusive VIP offer", "Personal branch visit"]
        else:
            risk_level = RiskLevel.CRITICAL
            factors = ["Minimal activity", "Account closure inquiry", "Negative sentiment"]
            actions = ["Immediate executive intervention", "Special retention package", "Win-back campaign"]

        return ChurnRiskAssessment(
            risk_level=risk_level,
            risk_score=round(risk_score, 1),
            risk_factors=factors,
            recommended_actions=actions,
        )

    def _generate_next_best_actions(
        self,
        customer_id: str,
        profile: UnifiedCustomerProfile,
        behavior: CustomerBehaviorAnalysis,
        churn_risk: ChurnRiskAssessment,
        seed: int,
    ) -> list[NextBestAction]:
        """Generate next-best actions based on customer profile and behavior"""
        actions = []

        # Cross-sell opportunities
        if profile.segment in [CustomerSegment.VIP, CustomerSegment.ACTIVE]:
            actions.append(
                NextBestAction(
                    action_id=f"NBA-{customer_id}-001",
                    action_type=ActionType.CROSS_SELL,
                    title="Offer Premium Credit Card",
                    description="Customer qualifies for premium credit card with high credit limit and exclusive benefits.",
                    expected_value=50000.0,
                    priority=1,
                    confidence=0.85,
                    valid_until=(datetime.utcnow() + timedelta(days=30)).isoformat() + "Z",
                    metadata={"product": "Premium Credit Card", "estimated_revenue": 50000},
                )
            )

        # Retention actions for at-risk customers
        if churn_risk.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            actions.append(
                NextBestAction(
                    action_id=f"NBA-{customer_id}-002",
                    action_type=ActionType.RETENTION,
                    title="Urgent Retention Campaign",
                    description="Customer shows high churn risk. Immediate personalized outreach recommended.",
                    expected_value=200000.0,
                    priority=1,
                    confidence=0.92,
                    valid_until=(datetime.utcnow() + timedelta(days=7)).isoformat() + "Z",
                    metadata={"risk_level": churn_risk.risk_level, "urgency": "high"},
                )
            )

        # Engagement actions
        if behavior.engagement_score < 60:
            actions.append(
                NextBestAction(
                    action_id=f"NBA-{customer_id}-003",
                    action_type=ActionType.ENGAGEMENT,
                    title="Re-engagement Campaign",
                    description="Send personalized mobile app feature highlights and exclusive digital-only offers.",
                    expected_value=15000.0,
                    priority=2,
                    confidence=0.78,
                    valid_until=(datetime.utcnow() + timedelta(days=14)).isoformat() + "Z",
                    metadata={"channel": "mobile_app", "campaign_type": "digital_engagement"},
                )
            )

        # Life event-based actions
        for event in behavior.detected_life_events:
            actions.append(
                NextBestAction(
                    action_id=f"NBA-{customer_id}-{len(actions)+1:03d}",
                    action_type=ActionType.CROSS_SELL,
                    title=f"Life Event: {event.event_type.replace('_', ' ').title()}",
                    description=f"Offer {', '.join(event.recommended_products)} based on detected life event.",
                    expected_value=100000.0,
                    priority=1,
                    confidence=event.confidence,
                    valid_until=(datetime.utcnow() + timedelta(days=21)).isoformat() + "Z",
                    metadata={"event_type": event.event_type, "products": event.recommended_products},
                )
            )

        # Sort by priority and confidence
        actions.sort(key=lambda x: (x.priority, -x.confidence))

        return actions[:5]  # Return top 5 actions

    def _get_recent_interactions(
        self, customer_id: str, seed: int, time_range_days: int
    ) -> list[InteractionTimeline]:
        """Get recent customer interactions"""
        interactions = []
        num_interactions = min(10, 3 + (seed % 8))

        interaction_types = [
            ("Mobile App Login", "Successful login via mobile app"),
            ("Branch Visit", "Visited branch for account inquiry"),
            ("ATM Withdrawal", "Cash withdrawal at ATM"),
            ("Call Center Contact", "Called support for transaction query"),
            ("Online Transfer", "Completed online fund transfer"),
        ]

        for i in range(num_interactions):
            interaction = interaction_types[i % len(interaction_types)]
            interactions.append(
                InteractionTimeline(
                    timestamp=(datetime.utcnow() - timedelta(days=i * 3 + (seed % 5))).isoformat() + "Z",
                    channel=[ChannelType.MOBILE_APP, ChannelType.BRANCH, ChannelType.ATM, ChannelType.CALL_CENTER][
                        i % 4
                    ],
                    interaction_type=interaction[0],
                    summary=interaction[1],
                    outcome="Completed" if i % 3 != 0 else "Pending",
                )
            )

        return sorted(interactions, key=lambda x: x.timestamp, reverse=True)

    def search_customers(
        self, request: CustomerSearchRequest, bank_id: str = "dashen"
    ) -> CustomerSearchResponse:
        """Search customers by various criteria"""
        # For demo, return sample results
        results = []
        query_lower = request.query.lower()

        for customer_id, data in list(self.customer_data.items())[:request.limit]:
            if query_lower in data["full_name"].lower() or query_lower in customer_id.lower():
                seed = int(hashlib.sha256(customer_id.encode()).hexdigest(), 16) % 10000
                results.append(
                    CustomerSearchResult(
                        customer_id=customer_id,
                        full_name=data["full_name"],
                        segment=data["segment"],
                        total_balance=float(50000 + (seed % 500000)),
                        risk_level=[RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH][seed % 3],
                        last_interaction=(datetime.utcnow() - timedelta(days=seed % 30)).isoformat() + "Z",
                        match_score=0.9 - (len(results) * 0.1),
                    )
                )

        return CustomerSearchResponse(
            results=results,
            total_count=len(results),
            metadata={"query": request.query, "bank_id": bank_id},
        )
