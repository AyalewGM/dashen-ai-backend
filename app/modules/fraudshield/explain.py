from __future__ import annotations

from .models import RiskLevel, TransactionEventModel


_REASON_TEMPLATES: dict[str, str] = {
    "unusually_large_amount": "The transaction amount is unusually large compared to typical activity.",
    "rapid_repeated_transactions": "Multiple similar transactions were detected in a short time window.",
    "new_device_or_ip": "The activity appears to come from a new or unknown device/network.",
    "suspicious_channel_mix": "The channel and amount combination is higher risk (e.g., high-value via ATM/web).",
    "impossible_travel": "The location changed too quickly to be physically plausible.",
    "login_then_transfer_spike": "A large transfer occurred shortly after a login event.",
}


def build_explanation(*, risk_level: RiskLevel, reasons: list[str], event: TransactionEventModel, language: str) -> str:
    # Minimal demo localization. Keep detailed reason templates in English for now.
    if risk_level == "low":
        header_map = {
            "en": "This activity looks normal based on our initial checks.",
            "am": "ይህ እንቅስቃሴ በመጀመሪያ ምርመራችን መሰረት መደበኛ ይመስላል።",
            "om": "Sochiin kun qorannoo jalqabaa keenya irratti hundaa'uun idilee fakkaata.",
            "ti": "እዚ ንቕስቓሴ ብመጀመርታ ምርመራና መሰረት ንቡር ይመስል።",
        }
    elif risk_level == "medium":
        header_map = {
            "en": "This activity shows some risk indicators and may require additional verification.",
            "am": "ይህ እንቅስቃሴ አንዳንድ የአደጋ ምልክቶችን ያሳያል እና ተጨማሪ ማረጋገጫ ሊያስፈልግ ይችላል።",
            "om": "Sochiin kun mallattoolee balaa muraasa agarsiisa; mirkaneessi dabalataa barbaachisuu danda'a.",
            "ti": "እዚ ንቕስቓሴ ገለ መርበብ ሓደጋ የርኢ እና ተወሳኺ ምርግጋጽ ክፈልጥ ይኽእል።",
        }
    else:
        header_map = {
            "en": "This activity shows strong fraud indicators and should be reviewed before processing.",
            "am": "ይህ እንቅስቃሴ ጠንካራ የማጭበርበር ምልክቶችን ያሳያል እና ከመፈጸሙ በፊት መመርመር አለበት።",
            "om": "Sochiin kun mallattoolee soba cimaa agarsiisa; osoo hin raawwatamin dura qoramuu qaba.",
            "ti": "እዚ ንቕስቓሴ ሓያል ምልክታት ምትእትታው የርኢ እና ቅድሚ ምፍጻሙ ክምርመር ይግባእ።",
        }

    header = header_map.get(language, header_map["en"])

    lines: list[str] = [header]

    # Keep it demo-friendly and concise.
    if reasons:
        lines.append("Key signals:")
        for r in reasons[:5]:
            desc = _REASON_TEMPLATES.get(r, r)
            lines.append(f"- {desc}")

    # Add minimal safe context (no IDs).
    lines.append(
        f"Context: eventType={event.event_type}, channel={event.channel}, amount={event.amount:.2f} {event.currency}."
    )

    return "\n".join(lines)
