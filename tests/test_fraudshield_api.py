from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def _base_event(**overrides):
    event = {
        "eventId": "evt-1",
        "sessionId": "s1",
        "customerId": "c1",
        "timestamp": "2025-01-01T10:00:00+00:00",
        "amount": 100.0,
        "currency": "ETB",
        "channel": "mobile",
        "merchant": "test",
        "location": {"country": "ET", "city": "Addis Ababa"},
        "device": {"deviceId": "dev-1", "ip": "10.0.0.1"},
        "eventType": "transfer",
    }
    event.update(overrides)
    return event


def test_fraud_score_endpoint_shape_and_range():
    payload = {"event": _base_event(amount=250.0)}
    response = client.post("/api/fraud/score", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert 0 <= data["riskScore"] <= 100
    assert data["riskLevel"] in {"low", "medium", "high"}
    assert isinstance(data["reasons"], list)
    assert data["recommendedAction"]
    assert "metadata" in data
    assert data["metadata"]["engine"]
    assert isinstance(data["metadata"]["latencyMs"], int)
    assert "explanation" in data


def test_fraud_score_deterministic_high_risk_for_large_atm_transfer():
    payload = {"event": _base_event(amount=120000.0, channel="atm")}
    response = client.post("/api/fraud/score", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["riskLevel"] == "high"
    assert data["recommendedAction"] == "hold_and_review"
    assert "unusually_large_amount" in data["reasons"]


def test_fraud_alerts_endpoint_returns_list():
    events = [
        _base_event(eventId="evt-a", timestamp="2025-01-01T10:00:00+00:00", amount=200.0),
        _base_event(eventId="evt-b", timestamp="2025-01-01T10:01:00+00:00", amount=60000.0, channel="web"),
        _base_event(eventId="evt-c", timestamp="2025-01-01T10:02:00+00:00", amount=130000.0, channel="atm"),
    ]

    response = client.post("/api/fraud/alerts", json={"events": events})
    assert response.status_code == 200
    data = response.json()

    assert "topAlerts" in data
    assert isinstance(data["topAlerts"], list)
    for alert in data["topAlerts"]:
        assert alert["alertId"]
        assert alert["severity"] in {"low", "medium", "high"}
        assert alert["summary"]
        assert isinstance(alert["supportingSignals"], list)
        assert alert["timestamp"]

    assert "metadata" in data
    assert data["metadata"]["engine"]
    assert isinstance(data["metadata"]["latencyMs"], int)


def test_fraud_score_validation_error_on_missing_event():
    response = client.post("/api/fraud/score", json={})
    assert response.status_code == 422


def test_fraud_score_language_header_amharic_changes_explanation_header():
    payload = {"event": _base_event(amount=250.0)}
    response = client.post("/api/fraud/score", json=payload, headers={"X-Language": "am"})
    assert response.status_code == 200
    data = response.json()
    assert "explanation" in data
    assert data["explanation"].startswith("ይህ")


def test_fraud_invalid_language_header_returns_400():
    payload = {"event": _base_event(amount=250.0)}
    response = client.post("/api/fraud/score", json=payload, headers={"X-Language": "fr"})
    assert response.status_code == 400
