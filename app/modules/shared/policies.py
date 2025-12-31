from __future__ import annotations

from fastapi import HTTPException, status

from .auth import AuthContext
from .rbac import require_internal_roles


def require_customer(auth: AuthContext) -> None:
    if auth.token_type != "customer" or not auth.customer_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


def get_customer_scope(auth: AuthContext) -> str:
    require_customer(auth)
    return auth.customer_id or ""


__all__ = [
    "require_internal_roles",
    "require_customer",
    "get_customer_scope",
]
