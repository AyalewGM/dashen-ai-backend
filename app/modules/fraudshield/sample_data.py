from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .models import DeviceModel, LocationModel, TransactionEventModel


def generate_demo_events(*, session_id: str = "demo", customer_id: str = "cust_demo") -> list[TransactionEventModel]:
    now = datetime.now(timezone.utc)

    normal = TransactionEventModel(
        eventId="evt-normal-1",
        sessionId=session_id,
        customerId=customer_id,
        timestamp=(now - timedelta(minutes=30)).isoformat(),
        amount=250.0,
        currency="ETB",
        channel="mobile",
        merchant="Groceries",
        location=LocationModel(country="ET", city="Addis Ababa"),
        device=DeviceModel(deviceId="dev-1", ip="10.0.0.1"),
        eventType="card_payment",
    )

    login = TransactionEventModel(
        eventId="evt-login-1",
        sessionId=session_id,
        customerId=customer_id,
        timestamp=(now - timedelta(minutes=2)).isoformat(),
        amount=0.0,
        currency="ETB",
        channel="web",
        merchant=None,
        location=LocationModel(country="ET", city="Addis Ababa"),
        device=DeviceModel(deviceId="dev-2", ip="203.0.113.10"),
        eventType="login",
    )

    suspicious = TransactionEventModel(
        eventId="evt-susp-1",
        sessionId=session_id,
        customerId=customer_id,
        timestamp=(now - timedelta(minutes=1)).isoformat(),
        amount=120000.0,
        currency="ETB",
        channel="atm",
        merchant=None,
        location=LocationModel(country="ET", city="Addis Ababa"),
        device=DeviceModel(deviceId="dev-2", ip="203.0.113.10"),
        eventType="transfer",
    )

    return [normal, login, suspicious]
