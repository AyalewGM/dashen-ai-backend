from io import BytesIO

import os

import pytest
from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def _token(payload: dict) -> str:
    import json

    return json.dumps(payload)


def test_customer_token_denied_ingestion_seed_demo():
    headers = {"Authorization": f"Bearer {_token({'tokenType': 'customer', 'customerId': 'c1'})}"}
    resp = client.post("/api/internal/ingestion/seed-demo", headers=headers)
    assert resp.status_code == 403


def test_internal_token_missing_role_denied_ingestion_upload():
    headers = {"Authorization": f"Bearer {_token({'tokenType': 'internal', 'userId': 'u1', 'roles': ['ROLE_RISK_INTERN']})}"}

    csv_bytes = b"kpi_date,metric_name,metric_value\n2025-01-01,deposits,100\n"
    files = {"file": ("kpis.csv", BytesIO(csv_bytes), "text/csv")}
    data = {"datasetType": "internal", "datasetName": "kpis"}

    resp = client.post("/api/internal/ingestion/upload", headers=headers, files=files, data=data)
    assert resp.status_code == 403


def test_csv_validator_rejects_wrong_schema_customer():
    from app.modules.ingestion.validators import validate_csv_schema

    bad = BytesIO(b"customer_id,amount\n123,10\n")
    with pytest.raises(ValueError):
        validate_csv_schema(dataset_type="customer", file_obj=bad)


def test_csv_validator_rejects_wrong_schema_internal():
    from app.modules.ingestion.validators import validate_csv_schema

    bad = BytesIO(b"metric_name,metric_value\ndeposits,100\n")
    with pytest.raises(ValueError):
        validate_csv_schema(dataset_type="internal", file_obj=bad)


@pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="DATABASE_URL not configured")
def test_seed_demo_populates_and_customer_summary_non_empty():
    headers_internal = {
        "Authorization": f"Bearer {_token({'tokenType': 'internal', 'userId': 'u1', 'roles': ['ROLE_ANALYTICS']})}"
    }
    resp = client.post("/api/internal/ingestion/seed-demo", headers=headers_internal)
    assert resp.status_code == 200
    counts = resp.json().get("counts")
    assert counts and counts.get("customers", 0) > 0

    headers_customer = {"Authorization": f"Bearer {_token({'tokenType': 'customer', 'customerId': 'cust-demo-001'})}"}
    summary = client.get("/api/customer/insights/summary", headers=headers_customer)
    assert summary.status_code == 200
    body = summary.json()
    assert body["monthSpend"] >= 0
    assert body["monthIncome"] >= 0
