from __future__ import annotations

import time
from datetime import datetime, timezone

from app.modules.shared.logging import log_request, log_response

from .explain import build_explanation
from .models import (
    AlertModel,
    FraudAlertsMetadataModel,
    FraudAlertsRequestModel,
    FraudAlertsResponseModel,
    FraudScoreMetadataModel,
    FraudScoreRequestModel,
    FraudScoreResponseModel,
    TransactionEventModel,
)
from .rules import ENGINE_LABEL, recommended_action_from_level, risk_level_from_score, score_event


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class FraudShieldService:
    async def score_event(self, request: FraudScoreRequestModel, *, language: str) -> FraudScoreResponseModel:
        start = time.monotonic()

        event = request.event
        log_request(
            module="fraudshield",
            session_id=event.session_id,
            extra={"event_type": event.event_type, "channel": event.channel},
        )

        result = score_event(event)
        level = risk_level_from_score(result.score)
        action = recommended_action_from_level(level)
        explanation = build_explanation(risk_level=level, reasons=result.reasons, event=event, language=language)

        latency_ms = int((time.monotonic() - start) * 1000)
        response = FraudScoreResponseModel(
            riskScore=result.score,
            riskLevel=level,
            reasons=result.reasons,
            recommendedAction=action,
            metadata=FraudScoreMetadataModel(engine=ENGINE_LABEL, latencyMs=latency_ms),
            explanation=explanation,
        )

        log_response(module="fraudshield", session_id=event.session_id, extra={"risk_level": level})
        return response

    async def generate_alerts(self, request: FraudAlertsRequestModel, *, language: str) -> FraudAlertsResponseModel:
        start = time.monotonic()

        events = request.events
        log_request(module="fraudshield", session_id=None, extra={"events": len(events)})

        alerts: list[AlertModel] = []

        # For demo: score each event using the remaining list as "recent" context.
        for idx, event in enumerate(events):
            recent = events[max(0, idx - 10) : idx]
            rr = score_event(event, recent_events=recent)
            level = risk_level_from_score(rr.score)
            if rr.score >= 70:
                alerts.append(
                    AlertModel(
                        alertId=f"alert-{event.event_id}",
                        severity=level,
                        summary=f"High-risk {event.event_type} detected ({rr.score}/100)",
                        supportingSignals=rr.reasons,
                        timestamp=event.timestamp or _now_iso(),
                    )
                )

        # Add a light "pattern" alert: many medium risks
        medium_count = 0
        medium_reasons: list[str] = []
        for idx, event in enumerate(events):
            recent = events[max(0, idx - 10) : idx]
            rr = score_event(event, recent_events=recent)
            if 40 <= rr.score <= 69:
                medium_count += 1
                for r in rr.reasons:
                    if r not in medium_reasons:
                        medium_reasons.append(r)

        if medium_count >= 3:
            alerts.append(
                AlertModel(
                    alertId="alert-pattern-medium-burst",
                    severity="medium",
                    summary="Multiple medium-risk events detected in a short sequence",
                    supportingSignals=medium_reasons[:5],
                    timestamp=_now_iso(),
                )
            )

        # Sort: high first then by number of signals.
        def _severity_rank(a: AlertModel) -> int:
            return {"high": 2, "medium": 1, "low": 0}.get(a.severity, 0)

        alerts.sort(key=lambda a: (_severity_rank(a), len(a.supporting_signals)), reverse=True)

        top_alerts = alerts[:5]
        latency_ms = int((time.monotonic() - start) * 1000)

        response = FraudAlertsResponseModel(
            topAlerts=top_alerts,
            metadata=FraudAlertsMetadataModel(engine=ENGINE_LABEL, latencyMs=latency_ms),
        )

        log_response(module="fraudshield", session_id=None, extra={"alerts": len(top_alerts)})
        return response
