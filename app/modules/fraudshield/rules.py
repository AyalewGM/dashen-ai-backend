from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from .models import TransactionEventModel


def _parse_iso(ts: str) -> datetime:
    # Accept common ISO formats and Z suffix.
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


@dataclass(frozen=True)
class RuleResult:
    score: int
    reasons: list[str]


ENGINE_LABEL = "rules_v1"


def score_event(
    event: TransactionEventModel,
    *,
    recent_events: Optional[list[TransactionEventModel]] = None,
    amount_high_threshold: float = 100_000,
    amount_medium_threshold: float = 50_000,
    channel_amount_threshold: float = 25_000,
) -> RuleResult:
    reasons: list[str] = []
    score = 0

    # 1) unusually_large_amount
    # Use bank-specific thresholds when provided.
    if event.amount >= amount_high_threshold:
        score += 45
        reasons.append("unusually_large_amount")
    elif event.amount >= amount_medium_threshold:
        score += 30
        reasons.append("unusually_large_amount")

    # 2) suspicious_channel_mix (risky channels for high value)
    if event.channel.lower() in {"atm", "web"} and event.amount >= channel_amount_threshold:
        score += 15
        reasons.append("suspicious_channel_mix")

    # 3) new_device_or_ip (heuristic: device/ip missing or changed vs recent)
    if recent_events:
        prev = None
        for e in reversed(recent_events):
            if e.customer_id and event.customer_id and e.customer_id == event.customer_id:
                prev = e
                break
            if e.session_id and event.session_id and e.session_id == event.session_id:
                prev = e
                break
        if prev and (prev.device or event.device):
            prev_device = prev.device.device_id if prev.device else None
            prev_ip = prev.device.ip if prev.device else None
            curr_device = event.device.device_id if event.device else None
            curr_ip = event.device.ip if event.device else None
            if (prev_device and curr_device and prev_device != curr_device) or (
                prev_ip and curr_ip and prev_ip != curr_ip
            ):
                score += 15
                reasons.append("new_device_or_ip")
        elif event.device is None or (event.device.device_id is None and event.device.ip is None):
            # Unknown device details is mildly risky for demo.
            score += 5
            reasons.append("new_device_or_ip")
    else:
        if event.device is None or (event.device.device_id is None and event.device.ip is None):
            score += 5
            reasons.append("new_device_or_ip")

    # 4) rapid_repeated_transactions (within 2 minutes)
    if recent_events:
        try:
            now_ts = _parse_iso(event.timestamp)
            close = 0
            for e in recent_events:
                if e.event_type != event.event_type:
                    continue
                if event.customer_id and e.customer_id and e.customer_id != event.customer_id:
                    continue
                if event.session_id and e.session_id and e.session_id != event.session_id:
                    continue
                dt = abs((now_ts - _parse_iso(e.timestamp)).total_seconds())
                if dt <= 120:
                    close += 1
            if close >= 3:
                score += 25
                reasons.append("rapid_repeated_transactions")
            elif close == 2:
                score += 15
                reasons.append("rapid_repeated_transactions")
        except Exception:
            # If timestamp parsing fails, skip this signal deterministically.
            pass

    # 5) impossible_travel (different country within 1 hour)
    if recent_events and event.location and event.location.country:
        try:
            now_ts = _parse_iso(event.timestamp)
            for e in reversed(recent_events):
                if not e.location or not e.location.country:
                    continue
                if event.customer_id and e.customer_id and e.customer_id != event.customer_id:
                    continue
                if event.session_id and e.session_id and e.session_id != event.session_id:
                    continue
                if e.location.country != event.location.country:
                    prev_ts = _parse_iso(e.timestamp)
                    if abs((now_ts - prev_ts).total_seconds()) <= 3600:
                        score += 25
                        reasons.append("impossible_travel")
                    break
        except Exception:
            pass

    # 6) login_then_transfer_spike (login followed by large transfer)
    if recent_events and event.event_type.lower() in {"transfer", "card_payment"} and event.amount >= 25_000:
        try:
            now_ts = _parse_iso(event.timestamp)
            for e in reversed(recent_events):
                if event.customer_id and e.customer_id and e.customer_id != event.customer_id:
                    continue
                if event.session_id and e.session_id and e.session_id != event.session_id:
                    continue
                if e.event_type.lower() == "login":
                    prev_ts = _parse_iso(e.timestamp)
                    if 0 <= (now_ts - prev_ts).total_seconds() <= 300:
                        score += 20
                        reasons.append("login_then_transfer_spike")
                    break
        except Exception:
            pass

    # Clamp and normalize reasons (unique, stable order)
    score = max(0, min(100, int(score)))
    seen: set[str] = set()
    deduped: list[str] = []
    for r in reasons:
        if r not in seen:
            seen.add(r)
            deduped.append(r)

    return RuleResult(score=score, reasons=deduped)


def risk_level_from_score(score: int) -> str:
    if score <= 39:
        return "low"
    if score <= 69:
        return "medium"
    return "high"


def recommended_action_from_level(level: str) -> str:
    if level == "low":
        return "allow"
    if level == "medium":
        return "step_up_verification"
    return "hold_and_review"
