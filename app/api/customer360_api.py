from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.modules.customer360.models import (
    Customer360Request,
    Customer360Response,
    CustomerSearchRequest,
    CustomerSearchResponse,
)
from app.modules.customer360.service import Customer360Service
from app.modules.shared.audit import audit_log
from app.modules.shared.auth import get_auth_context

router = APIRouter()
service = Customer360Service()


@router.post("/profile", response_model=Customer360Response)
async def get_customer_360_profile(
    request: Request, payload: Customer360Request
) -> Customer360Response:
    """Get comprehensive 360-degree customer view with unified profile, insights, and next-best actions"""
    try:
        auth = get_auth_context(request)
        # Internal users can query any customer, customers can only see themselves
        if auth.token_type == "customer" and payload.customer_id != auth.customer_id:
            raise HTTPException(status_code=403, detail="Access denied")
        bank_id = getattr(auth, "bank_id", "dashen")
    except:
        # Allow demo access without auth
        bank_id = "dashen"
        auth = None

    try:
        response = service.get_customer_360(payload, bank_id=bank_id)

        if auth:
            audit_log(
                event_type="customer_360_profile",
                actor={"actorType": auth.token_type, "actorId": auth.user_id or auth.customer_id},
                resource={"endpoint": "/api/customer360/profile", "customerId": payload.customer_id},
                metadata={"outcome": "success"},
            )

        return response

    except HTTPException:
        raise
    except Exception as exc:
        if auth:
            audit_log(
                event_type="customer_360_profile",
                actor={"actorType": auth.token_type, "actorId": auth.user_id or auth.customer_id},
                resource={"endpoint": "/api/customer360/profile"},
                metadata={"outcome": "error"},
            )
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post("/search", response_model=CustomerSearchResponse)
async def search_customers(request: Request, payload: CustomerSearchRequest) -> CustomerSearchResponse:
    """Search customers by name, ID, or other criteria"""
    auth = get_auth_context(request)

    try:
        # Only internal users can search customers
        if auth.token_type != "internal":
            raise HTTPException(status_code=403, detail="Access denied")

        bank_id = getattr(auth, "bank_id", "dashen")
        response = service.search_customers(payload, bank_id=bank_id)

        audit_log(
            event_type="customer_search",
            actor={"actorType": auth.token_type, "actorId": auth.user_id},
            resource={"endpoint": "/api/customer360/search"},
            metadata={"outcome": "success", "query": payload.query, "results": len(response.results)},
        )

        return response

    except HTTPException:
        raise
    except Exception as exc:
        audit_log(
            event_type="customer_search",
            actor={"actorType": auth.token_type, "actorId": auth.user_id or auth.customer_id},
            resource={"endpoint": "/api/customer360/search"},
            metadata={"outcome": "error"},
        )
        raise HTTPException(status_code=500, detail="Internal server error") from exc
