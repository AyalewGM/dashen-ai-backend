from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IntentResult:
    intent: str


def map_question_to_intent(question: str) -> IntentResult:
    q = (question or "").lower()
    if any(k in q for k in ["bill", "utility", "electric", "water", "telecom"]):
        return IntentResult(intent="BILLS_SUMMARY")
    if any(k in q for k in ["spend", "spending", "expense", "trend"]):
        return IntentResult(intent="SPENDING_TREND")
    if any(k in q for k in ["category", "categories", "breakdown"]):
        return IntentResult(intent="CATEGORY_BREAKDOWN")
    if any(k in q for k in ["save", "saving", "budget", "advice"]):
        return IntentResult(intent="SAVINGS_ADVICE")
    return IntentResult(intent="SAVINGS_ADVICE")
