from __future__ import annotations

import hashlib
import time
from datetime import datetime, timedelta

from .models import (
    CategoryAmount,
    ChartData,
    CustomerInsightsQueryRequest,
    CustomerInsightsQueryResponse,
    CustomerInsightsSummaryResponse,
    Series,
)
from .intent import map_question_to_intent
from .queries import bills_breakdown, has_db, month_summary, top_categories, weekly_spend_series


class CustomerInsightsService:
    def get_summary(self, *, customer_id: str, language: str) -> CustomerInsightsSummaryResponse:
        if has_db():
            spend, income = month_summary(customer_id)
            savings = income - spend
            cats = [CategoryAmount(category=c, amount=a) for c, a in top_categories(customer_id, limit=5)]
            bills = bills_breakdown(customer_id)
        else:
            # Deterministic stub per customer to prove scoping
            seed = int(hashlib.sha256(customer_id.encode("utf-8")).hexdigest(), 16) % 1000
            spend = 1200.0 + float(seed % 200)
            income = 2000.0 + float(seed % 300)
            savings = income - spend
            cats = [
                CategoryAmount(category="groceries", amount=spend * 0.35),
                CategoryAmount(category="transport", amount=spend * 0.2),
                CategoryAmount(category="utilities", amount=spend * 0.15),
            ]
            bills = {"water": 120.0, "electricity": 280.0, "telecom": 150.0}

        return CustomerInsightsSummaryResponse(
            monthSpend=round(spend, 2),
            monthIncome=round(income, 2),
            netSavings=round(savings, 2),
            topCategories=cats,
            billsThisMonth=bills,
        )

    async def query(
        self,
        *,
        customer_id: str,
        request: CustomerInsightsQueryRequest,
        language: str,
    ) -> CustomerInsightsQueryResponse:
        start = time.monotonic()

        # Hard boundary enforcement: never accept customerId from the body.
        # Use ONLY the customer_id argument (derived from token scope).
        _ = request.customer_id

        intent = request.intent
        if not intent and request.question:
            intent = map_question_to_intent(request.question).intent
        if not intent:
            intent = "SAVINGS_ADVICE"

        # Default time window: last 28 days
        if request.time_range:
            tr_start = request.time_range.start
            tr_end = request.time_range.end
        else:
            now = datetime.utcnow()
            tr_end = now.isoformat() + "Z"
            tr_start = (now - timedelta(days=28)).isoformat() + "Z"

        if intent == "SPENDING_TREND":
            if has_db():
                labels, data = weekly_spend_series(customer_id, start=tr_start, end=tr_end)
            else:
                labels, data = (["W1", "W2", "W3", "W4"], [200.0, 260.0, 240.0, 300.0])

            chart = ChartData(labels=labels, series=[Series(name="spend", data=data)])
            answer = {
                "en": "Here is your spending trend for the selected time range.",
                "am": "ለተመረጠው የጊዜ ክልል የወጪ አዝማሚያዎ እነሆ።",
                "om": "Yeroo filatameef haala baasii kee kunoo.",
                "ti": "ንተመረጸ ናይ ግዜ ክልል ኣዝማሚያ ወጪ እዚ እዩ።",
            }[language]
            table = None
        elif intent == "BILLS_SUMMARY":
            chart = None
            b = bills_breakdown(customer_id) if has_db() else {"water": 120.0, "electricity": 280.0, "telecom": 150.0}
            table = [{"bill": k, "amount": float(v)} for k, v in b.items()]
            answer = {
                "en": "Here is a summary of your utility bills this month.",
                "am": "የዚህ ወር የዩቲሊቲ ክፍያዎች ማጠቃለያ እነሆ።",
                "om": "Gabaasa kaffaltii tajaajila mootummaa ji'a kanaa kunoo.",
                "ti": "ናይ ወርሒ ዩቲሊቲ ክፍሊት ማጠቃለያ እዚ እዩ።",
            }[language]
        elif intent == "CATEGORY_BREAKDOWN":
            chart = None
            cats = top_categories(customer_id, limit=8) if has_db() else [("groceries", 420.0), ("utilities", 180.0)]
            table = [{"category": c, "amount": float(a)} for c, a in cats]
            answer = {
                "en": "Here is your spending breakdown by category.",
                "am": "የወጪዎ በምድብ ዝርዝር እነሆ።",
                "om": "Baasiin kee ramaddii irratti akka qoodame kunoo.",
                "ti": "ወጪኻ ብምድብ ከመይ ከምዝተከፈለ እዚ እዩ።",
            }[language]
        else:
            chart = None
            table = None
            answer = {
                "en": "A simple tip: set a monthly budget and track top categories.",
                "am": "ቀላል ምክር፦ ወርሃዊ በጀት ያዘጋጁ እና ዋና ምድቦችን ይከታተሉ።",
                "om": "Gorsa salphaa: baajata ji'a kaa'iitii ramaddii ijoo hordofi.",
                "ti": "ቀሊል ምኽሪ፦ ወርሓዊ ባጀት ኣቐምጥ እና ዋና ምድቦች ተከታተል።",
            }[language]

        latency_ms = int((time.monotonic() - start) * 1000)
        return CustomerInsightsQueryResponse(
            answerText=answer,
            chartData=chart,
            tableData=table,
            metadata={"latencyMs": latency_ms},
        )
