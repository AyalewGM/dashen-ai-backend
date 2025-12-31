from __future__ import annotations

from fastapi import HTTPException, status

from .auth import AuthContext


def has_any_role(auth: AuthContext, allowed_roles: set[str]) -> bool:
    if not auth.roles:
        return False
    return any(r in allowed_roles for r in auth.roles)


def require_internal_roles(auth: AuthContext, allowed_roles: set[str]) -> None:
    if auth.token_type != "internal" or not auth.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    if not has_any_role(auth, allowed_roles):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
