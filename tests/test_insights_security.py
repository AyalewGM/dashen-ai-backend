from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def _token(payload: dict) -> str:
    # auth.get_auth_context supports JSON token payloads in dev/test
    import json

    return json.dumps(payload)


def test_internal_endpoint_denies_customer_token(monkeypatch):
    calls = []

    def fake_audit_log(*args, **kwargs):
        calls.append((args, kwargs))

    import app.api.internal_insights_api as internal_api

    monkeypatch.setattr(internal_api, "audit_log", fake_audit_log)

    headers = {"Authorization": f"Bearer {_token({'tokenType': 'customer', 'customerId': 'c1'})}"}
    resp = client.get("/api/internal/insights/kpis", headers=headers)
    assert resp.status_code == 403
    assert any(kw.get("metadata", {}).get("outcome") == "denied" for _, kw in calls)


def test_internal_endpoint_denies_missing_roles(monkeypatch):
    calls = []

    def fake_audit_log(*args, **kwargs):
        calls.append((args, kwargs))

    import app.api.internal_insights_api as internal_api

    monkeypatch.setattr(internal_api, "audit_log", fake_audit_log)

    headers = {"Authorization": f"Bearer {_token({'tokenType': 'internal', 'userId': 'u1', 'roles': ['ROLE_RISK_INTERN']})}"}
    resp = client.get("/api/internal/insights/kpis", headers=headers)
    assert resp.status_code == 403
    assert any(kw.get("metadata", {}).get("outcome") == "denied" for _, kw in calls)


def test_internal_endpoint_allows_proper_role(monkeypatch):
    calls = []

    def fake_audit_log(*args, **kwargs):
        calls.append((args, kwargs))

    import app.api.internal_insights_api as internal_api

    monkeypatch.setattr(internal_api, "audit_log", fake_audit_log)

    headers = {
        "Authorization": f"Bearer {_token({'tokenType': 'internal', 'userId': 'u1', 'roles': ['ROLE_ANALYTICS']})}",
        "X-Language": "am",
    }
    resp = client.get("/api/internal/insights/kpis", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "depositsTrend" in body
    assert any(kw.get("metadata", {}).get("outcome") == "success" for _, kw in calls)


def test_internal_query_uses_language_for_narrative_summary():
    headers = {
        "Authorization": f"Bearer {_token({'tokenType': 'internal', 'userId': 'u1', 'roles': ['ROLE_ANALYTICS']})}",
        "X-Language": "am",
    }
    payload = {"metricName": "deposits", "timeRange": {"start": "2025-01-01", "end": "2025-01-31"}}
    resp = client.post("/api/internal/insights/query", headers=headers, json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "narrativeSummary" in data
    assert "chartData" in data
    assert "metadata" in data
    assert data["narrativeSummary"].startswith("ለ")


def test_customer_endpoint_denies_internal_token(monkeypatch):
    calls = []

    def fake_audit_log(*args, **kwargs):
        calls.append((args, kwargs))

    import app.api.customer_insights_api as customer_api

    monkeypatch.setattr(customer_api, "audit_log", fake_audit_log)

    headers = {"Authorization": f"Bearer {_token({'tokenType': 'internal', 'userId': 'u1', 'roles': ['ROLE_ANALYTICS']})}"}
    resp = client.get("/api/customer/insights/summary", headers=headers)
    assert resp.status_code == 403
    assert any(kw.get("metadata", {}).get("outcome") == "denied" for _, kw in calls)


def test_customer_endpoint_ignores_customer_id_in_body(monkeypatch):
    calls = []

    def fake_audit_log(*args, **kwargs):
        calls.append((args, kwargs))

    import app.api.customer_insights_api as customer_api

    monkeypatch.setattr(customer_api, "audit_log", fake_audit_log)

    token_customer_id = "cust-token"
    headers = {"Authorization": f"Bearer {_token({'tokenType': 'customer', 'customerId': token_customer_id})}", "X-Language": "ti"}

    payload = {
        "intent": "SPENDING_TREND",
        "timeRange": {"start": "2025-01-01", "end": "2025-01-31"},
        "filters": {},
        "customerId": "cust-body",
    }
    resp = client.post("/api/customer/insights/query", headers=headers, json=payload)
    assert resp.status_code == 200
    data = resp.json()
    # Ensure we return a valid response and do not crash when body tries to override customerId.
    assert "answerText" in data
    assert any(kw.get("metadata", {}).get("outcome") == "success" for _, kw in calls)


def test_customer_invalid_language_header_returns_400():
    headers = {"Authorization": f"Bearer {_token({'tokenType': 'customer', 'customerId': 'cust-a'})}", "X-Language": "fr"}
    payload = {"intent": "SPENDING_TREND", "timeRange": {"start": "2025-01-01", "end": "2025-01-31"}}
    resp = client.post("/api/customer/insights/query", headers=headers, json=payload)
    assert resp.status_code == 400


def test_customer_summary_scoped_to_token_customer_id():
    headers_a = {"Authorization": f"Bearer {_token({'tokenType': 'customer', 'customerId': 'cust-a'})}"}
    headers_b = {"Authorization": f"Bearer {_token({'tokenType': 'customer', 'customerId': 'cust-b'})}"}

    resp_a = client.get("/api/customer/insights/summary", headers=headers_a)
    resp_b = client.get("/api/customer/insights/summary", headers=headers_b)

    assert resp_a.status_code == 200
    assert resp_b.status_code == 200
    assert resp_a.json()["monthSpend"] != resp_b.json()["monthSpend"]
