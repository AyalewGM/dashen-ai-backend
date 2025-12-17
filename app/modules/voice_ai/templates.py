from .models import NotificationTemplate


TEMPLATES: list[NotificationTemplate] = [
    NotificationTemplate(
        id="loan_payment_reminder",
        title="Loan Payment Reminder",
        body="Dear {name}, your loan payment of {amount} is due on {dueDate}.",
    ),
    NotificationTemplate(
        id="card_usage_alert",
        title="Card Usage Alert",
        body="Dear {name}, your card ending with {cardLast4} was used for {amount} at {merchant}.",
    ),
    NotificationTemplate(
        id="account_activity_alert",
        title="Account Activity Alert",
        body="Dear {name}, there was a {activityType} on your account ending with {accountLast4}.",
    ),
]


def list_templates() -> list[NotificationTemplate]:
    return TEMPLATES


def get_template_by_id(template_id: str) -> NotificationTemplate | None:
    return next((t for t in TEMPLATES if t.id == template_id), None)
