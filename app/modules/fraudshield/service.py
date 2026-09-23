from __future__ import annotations

import time
from datetime import datetime, timezone

from app.modules.shared.logging import log_request, log_response

from .explain import build_explanation
from app.modules.shared.bank_config import get_bank_config

from .models import (
    AlertModel,
    BehavioralScore,
    FraudAlertsMetadataModel,
    FraudAlertsRequestModel,
    FraudAlertsResponseModel,
    FraudPattern,
    FraudScoreMetadataModel,
    FraudScoreRequestModel,
    FraudScoreResponseModel,
    MonitoringAlert,
    MonitoringMetrics,
    TransactionEventModel,
    TransactionMonitorRequest,
    TransactionMonitorResponse,
)
from .rules import ENGINE_LABEL, recommended_action_from_level, risk_level_from_score, score_event


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class FraudShieldService:
    async def score_event(self, request: FraudScoreRequestModel, *, language: str) -> FraudScoreResponseModel:
        start = time.monotonic()

        event = request.event
        bank_id = request.bankId or "dashen"
        bank_config = get_bank_config(bank_id)
        fraud_rules = bank_config.fraud_rules

        log_request(
            module="fraudshield",
            session_id=event.session_id,
            extra={"event_type": event.event_type, "channel": event.channel, "bank_id": bank_id},
        )

        result = score_event(
            event,
            amount_high_threshold=fraud_rules.high_amount_threshold,
            amount_medium_threshold=fraud_rules.medium_amount_threshold,
        )
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
        bank_id = request.bankId or "dashen"
        bank_config = get_bank_config(bank_id)
        fraud_rules = bank_config.fraud_rules
        log_request(module="fraudshield", session_id=None, extra={"events": len(events), "bank_id": bank_id})

        alerts: list[AlertModel] = []

        # For demo: score each event using the remaining list as "recent" context.
        for idx, event in enumerate(events):
            recent = events[max(0, idx - 10) : idx]
            rr = score_event(
                event,
                recent_events=recent,
                amount_high_threshold=fraud_rules.high_amount_threshold,
                amount_medium_threshold=fraud_rules.medium_amount_threshold,
            )
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
            rr = score_event(
                event,
                recent_events=recent,
                amount_high_threshold=fraud_rules.high_amount_threshold,
                amount_medium_threshold=fraud_rules.medium_amount_threshold,
            )
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

    async def monitor_transactions(
        self, request: TransactionMonitorRequest, *, language: str = "en"
    ) -> TransactionMonitorResponse:
        """Advanced transaction monitoring with behavioral analytics and pattern detection."""
        start = time.monotonic()
        bank_id = request.bank_id or "dashen"
        bank_config = get_bank_config(bank_id)

        log_request(
            module="fraudshield_monitor",
            session_id=None,
            extra={"events": len(request.events), "bank_id": bank_id},
        )

        alerts: list[MonitoringAlert] = []
        customer_activity: dict[str, list[TransactionEventModel]] = {}
        channel_counts: dict[str, int] = {}
        hourly_distribution: dict[int, int] = {}

        # Aggregate customer activity
        for event in request.events:
            if event.customer_id:
                if event.customer_id not in customer_activity:
                    customer_activity[event.customer_id] = []
                customer_activity[event.customer_id].append(event)

            # Track channel usage
            channel = event.channel.lower()
            channel_counts[channel] = channel_counts.get(channel, 0) + 1

            # Track hourly distribution
            try:
                hour = int(event.timestamp[11:13]) if len(event.timestamp) >= 13 else 12
                hourly_distribution[hour] = hourly_distribution.get(hour, 0) + 1
            except Exception:
                pass

        # Process each event with behavioral analytics
        for idx, event in enumerate(request.events):
            recent = request.events[max(0, idx - 10) : idx]
            rule_result = score_event(
                event,
                recent_events=recent,
                amount_high_threshold=bank_config.fraud_rules.high_amount_threshold,
                amount_medium_threshold=bank_config.fraud_rules.medium_amount_threshold,
            )

            # Behavioral scoring
            velocity_score = 0
            pattern_score = 0
            anomaly_score = 0
            signals: list[str] = []

            # 1. Velocity analysis
            if len(recent) >= 5:
                velocity_score += 15
                signals.append("rapid_transaction_velocity")
            if len(recent) >= 8:
                velocity_score += 10
                signals.append("extreme_velocity")

            # 2. Pattern analysis
            if event.customer_id and event.customer_id in customer_activity:
                customer_events = customer_activity[event.customer_id]
                if len(customer_events) >= 5:
                    pattern_score += 10
                    signals.append("repeated_customer_activity")

                # Check for round amounts (potential structuring)
                if event.amount % 1000 == 0 and event.amount >= 10000:
                    pattern_score += 5
                    signals.append("round_amount_structuring")

            # Channel concentration
            if channel_counts.get(event.channel.lower(), 0) >= 5:
                pattern_score += 8
                signals.append("channel_concentration")

            # 3. Anomaly detection
            try:
                hour = int(event.timestamp[11:13]) if len(event.timestamp) >= 13 else 12
                # Night-time transactions (12am-5am)
                if 0 <= hour <= 5:
                    anomaly_score += 12
                    signals.append("unusual_hours")
                # Weekend/holiday pattern (simplified)
                if hour >= 22 or hour <= 6:
                    anomaly_score += 5
                    signals.append("off_hours_activity")
            except Exception:
                pass

            # Geographic anomaly (simplified - checking if location exists)
            if event.location and event.location.country:
                if event.location.country.lower() not in ["ethiopia", "et"]:
                    anomaly_score += 15
                    signals.append("foreign_location")

            # Device/IP changes
            if event.device and not event.device.device_id:
                anomaly_score += 8
                signals.append("unknown_device")

            behavioral_total = velocity_score + pattern_score + anomaly_score
            behavioral_score_obj = BehavioralScore(
                velocityScore=velocity_score,
                patternScore=pattern_score,
                anomalyScore=anomaly_score,
                total=behavioral_total,
            )

            # Combined risk score (weighted)
            combined = int(rule_result.score * 0.6 + behavioral_total * 0.4)
            combined = min(100, max(0, combined))

            # False positive risk assessment
            if combined >= 75 and rule_result.score < 40:
                fp_risk = "high"
            elif combined >= 60 and behavioral_total > rule_result.score:
                fp_risk = "medium"
            elif combined >= 50:
                fp_risk = "medium"
            else:
                fp_risk = "low"

            # Determine scenario
            if velocity_score >= 20:
                scenario = "velocity_attack"
            elif pattern_score >= 15:
                scenario = "structured_pattern"
            elif anomaly_score >= 20:
                scenario = "behavioral_anomaly"
            elif rule_result.score >= 60:
                scenario = "rule_based_high_risk"
            else:
                scenario = "combined_risk_indicators"

            # Generate alert if combined score is significant
            if combined >= 40:
                severity = risk_level_from_score(combined)
                action = recommended_action_from_level(severity)

                alerts.append(
                    MonitoringAlert(
                        alertId=f"mon-{event.event_id}",
                        customerId=event.customer_id,
                        severity=severity,
                        scenario=scenario,
                        ruleScore=rule_result.score,
                        behavioralScore=behavioral_score_obj,
                        combinedScore=combined,
                        falsePositiveRisk=fp_risk,
                        summary=f"{scenario.replace('_', ' ').title()}: {event.amount} {event.currency} via {event.channel}",
                        signals=rule_result.reasons + signals,
                        timestamp=event.timestamp or _now_iso(),
                        recommendedAction=action,
                    )
                )

        # Pattern detection
        patterns: list[FraudPattern] = []

        # Pattern 1: Velocity burst
        if len(alerts) >= 3:
            velocity_alerts = [a for a in alerts if "velocity" in a.scenario.lower()]
            if len(velocity_alerts) >= 2:
                patterns.append(
                    FraudPattern(
                        patternId="pat-velocity-burst",
                        patternType="rapid_repeated_transactions",
                        description="Multiple rapid transactions detected across customers",
                        affectedCustomers=len(set(a.customerId for a in velocity_alerts if a.customerId)),
                        eventCount=len(velocity_alerts),
                        severity="high" if len(velocity_alerts) >= 5 else "medium",
                        confidence=0.85,
                    )
                )

        # Pattern 2: Channel concentration
        high_risk_channels = [c for c, n in channel_counts.items() if n >= 5]
        if high_risk_channels:
            patterns.append(
                FraudPattern(
                    patternId="pat-channel-concentration",
                    patternType="channel_concentration",
                    description=f"High concentration of transactions on {', '.join(high_risk_channels)} channels",
                    affectedCustomers=len(customer_activity),
                    eventCount=sum(channel_counts[c] for c in high_risk_channels),
                    severity="medium",
                    confidence=0.75,
                )
            )

        # Pattern 3: Time-based anomaly
        night_hours = sum(hourly_distribution.get(h, 0) for h in range(0, 6))
        if night_hours >= 5:
            patterns.append(
                FraudPattern(
                    patternId="pat-time-anomaly",
                    patternType="unusual_time_pattern",
                    description=f"{night_hours} transactions during unusual hours (12am-6am)",
                    affectedCustomers=len(customer_activity),
                    eventCount=night_hours,
                    severity="medium",
                    confidence=0.70,
                )
            )

        # Pattern 4: Coordinated activity (same customer, multiple events)
        for customer_id, events in customer_activity.items():
            if len(events) >= 6:
                patterns.append(
                    FraudPattern(
                        patternId=f"pat-coord-{customer_id}",
                        patternType="coordinated_customer_activity",
                        description=f"Customer {customer_id} with {len(events)} transactions in monitoring window",
                        affectedCustomers=1,
                        eventCount=len(events),
                        severity="high" if len(events) >= 10 else "medium",
                        confidence=0.80,
                    )
                )

        # Calculate metrics
        total_events = len(request.events)
        high_risk = len([a for a in alerts if a.severity == "high"])
        medium_risk = len([a for a in alerts if a.severity == "medium"])
        avg_score = round(sum(a.combinedScore for a in alerts) / len(alerts), 2) if alerts else 0.0
        fp_rate = round(
            len([a for a in alerts if a.falsePositiveRisk in {"high", "medium"}]) / len(alerts), 2
        ) if alerts else 0.0

        metrics = MonitoringMetrics(
            totalEvents=total_events,
            alertsGenerated=len(alerts),
            highRiskCount=high_risk,
            mediumRiskCount=medium_risk,
            avgRiskScore=avg_score,
            falsePositiveRate=fp_rate,
            patternsDetected=len(patterns),
        )

        # Generate summary
        summary_map = {
            "en": f"Monitored {total_events} transactions for {bank_config.bank_name}. Generated {len(alerts)} alerts ({high_risk} high-risk) and detected {len(patterns)} fraud patterns.",
            "am": f"ለ{bank_config.bank_name} {total_events} ግብይቶችን ተከታትለናል። {len(alerts)} ማስጠንቀቂያዎች ({high_risk} ከፍተኛ አደጋ) እና {len(patterns)} የማጭበርበር ቅጦችን አግኝተናል።",
            "om": f"Gurgurtaa {total_events} {bank_config.bank_name}f hordofne. Akeekkachiisa {len(alerts)} ({high_risk} balaa guddaa) fi akkaataa gowwoomsaa {len(patterns)} arganne.",
            "ti": f"ንባንክ {bank_config.bank_name} {total_events} ግብይቶች ተከታተልና። {len(alerts)} ማስጠንቀቂያታት ({high_risk} ልዑል ሓደጋ) ከምኡ'ውን {len(patterns)} ናይ ምትላል ቅዲታት ረኺብና።",
        }

        latency_ms = int((time.monotonic() - start) * 1000)
        log_response(
            module="fraudshield_monitor",
            session_id=None,
            extra={"alerts": len(alerts), "patterns": len(patterns), "latency_ms": latency_ms},
        )

        return TransactionMonitorResponse(
            alerts=sorted(alerts, key=lambda a: a.combinedScore, reverse=True),
            patterns=patterns,
            metrics=metrics,
            summary=summary_map.get(language, summary_map["en"]),
        )
