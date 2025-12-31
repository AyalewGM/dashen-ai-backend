from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.modules.insights_internal.models import InternalKpisResponse, InternalQueryRequest, InternalQueryResponse
from app.modules.insights_internal.service import InternalInsightsService
from app.modules.shared.audit import audit_log
from app.modules.shared.auth import get_auth_context
from app.modules.shared.language import resolve_language
from app.modules.shared.rbac import require_internal_roles


router = APIRouter()
service = InternalInsightsService()


_ALLOWED_KPIS_ROLES = {"ROLE_EXECUTIVE", "ROLE_ANALYTICS", "ROLE_FINANCE", "ROLE_RISK"}
_ALLOWED_QUERY_ROLES = {"ROLE_EXECUTIVE", "ROLE_ANALYTICS"}


@router.get("/kpis", response_model=InternalKpisResponse)
async def get_internal_kpis(request: Request) -> InternalKpisResponse:
    auth = get_auth_context(request)
    try:
        require_internal_roles(auth, _ALLOWED_KPIS_ROLES)
        language = await resolve_language(request)
        resp = service.get_kpis(language=language)
        audit_log(
            event_type="internal_insights_kpis",
            actor={"actorType": auth.token_type, "actorId": auth.user_id},
            resource={"endpoint": "/api/internal/insights/kpis"},
            metadata={"outcome": "success", "language": language},
        )
        return resp
    except HTTPException as exc:
        audit_log(
            event_type="internal_insights_kpis",
            actor={"actorType": auth.token_type, "actorId": auth.user_id or auth.customer_id},
            resource={"endpoint": "/api/internal/insights/kpis"},
            metadata={"outcome": "denied"},
        )
        raise
    except Exception as exc:  # noqa: BLE001
        audit_log(
            event_type="internal_insights_kpis",
            actor={"actorType": auth.token_type, "actorId": auth.user_id or auth.customer_id},
            resource={"endpoint": "/api/internal/insights/kpis"},
            metadata={"outcome": "error"},
        )
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post("/query", response_model=InternalQueryResponse)
async def post_internal_query(request: Request, payload: InternalQueryRequest) -> InternalQueryResponse:
    auth = get_auth_context(request)
    try:
        require_internal_roles(auth, _ALLOWED_QUERY_ROLES)
        language = await resolve_language(request)
        resp = service.query(payload, language=language)
        audit_log(
            event_type="internal_insights_query",
            actor={"actorType": auth.token_type, "actorId": auth.user_id},
            resource={"endpoint": "/api/internal/insights/query"},
            metadata={"outcome": "success", "metricName": payload.metric_name, "language": language},
        )
        return resp
    except HTTPException:
        audit_log(
            event_type="internal_insights_query",
            actor={"actorType": auth.token_type, "actorId": auth.user_id or auth.customer_id},
            resource={"endpoint": "/api/internal/insights/query"},
            metadata={"outcome": "denied"},
        )
        raise
    except Exception as exc:  # noqa: BLE001
        audit_log(
            event_type="internal_insights_query",
            actor={"actorType": auth.token_type, "actorId": auth.user_id or auth.customer_id},
            resource={"endpoint": "/api/internal/insights/query"},
            metadata={"outcome": "error"},
        )
        raise HTTPException(status_code=500, detail="Internal server error") from exc
