from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.modules.insights_customer.models import (
    CustomerInsightsQueryRequest,
    CustomerInsightsQueryResponse,
    CustomerInsightsSummaryResponse,
)
from app.modules.insights_customer.service import CustomerInsightsService
from app.modules.shared.audit import audit_log
from app.modules.shared.auth import get_auth_context
from app.modules.shared.language import resolve_language
from app.modules.shared.policies import get_customer_scope, require_customer


router = APIRouter()
service = CustomerInsightsService()


@router.get("/summary", response_model=CustomerInsightsSummaryResponse)
async def get_customer_summary(request: Request) -> CustomerInsightsSummaryResponse:
    auth = get_auth_context(request)
    try:
        require_customer(auth)
        customer_id = get_customer_scope(auth)
        language = await resolve_language(request)
        resp = service.get_summary(customer_id=customer_id, language=language)
        audit_log(
            event_type="customer_insights_summary",
            actor={"actorType": auth.token_type, "actorId": customer_id},
            resource={"endpoint": "/api/customer/insights/summary"},
            metadata={"outcome": "success", "language": language},
        )
        return resp
    except HTTPException:
        audit_log(
            event_type="customer_insights_summary",
            actor={"actorType": auth.token_type, "actorId": auth.user_id or auth.customer_id},
            resource={"endpoint": "/api/customer/insights/summary"},
            metadata={"outcome": "denied"},
        )
        raise
    except Exception as exc:  # noqa: BLE001
        audit_log(
            event_type="customer_insights_summary",
            actor={"actorType": auth.token_type, "actorId": auth.user_id or auth.customer_id},
            resource={"endpoint": "/api/customer/insights/summary"},
            metadata={"outcome": "error"},
        )
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post("/query", response_model=CustomerInsightsQueryResponse)
async def post_customer_query(request: Request, payload: CustomerInsightsQueryRequest) -> CustomerInsightsQueryResponse:
    auth = get_auth_context(request)
    try:
        require_customer(auth)
        customer_id = get_customer_scope(auth)
        language = await resolve_language(request)
        resp = await service.query(customer_id=customer_id, request=payload, language=language)
        audit_log(
            event_type="customer_insights_query",
            actor={"actorType": auth.token_type, "actorId": customer_id},
            resource={"endpoint": "/api/customer/insights/query"},
            metadata={"outcome": "success", "intent": payload.intent, "language": language},
        )
        return resp
    except HTTPException:
        audit_log(
            event_type="customer_insights_query",
            actor={"actorType": auth.token_type, "actorId": auth.user_id or auth.customer_id},
            resource={"endpoint": "/api/customer/insights/query"},
            metadata={"outcome": "denied"},
        )
        raise
    except Exception as exc:  # noqa: BLE001
        audit_log(
            event_type="customer_insights_query",
            actor={"actorType": auth.token_type, "actorId": auth.user_id or auth.customer_id},
            resource={"endpoint": "/api/customer/insights/query"},
            metadata={"outcome": "error"},
        )
        raise HTTPException(status_code=500, detail="Internal server error") from exc
