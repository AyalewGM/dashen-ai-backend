from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Any, Optional

from fastapi import HTTPException, Request, status


@dataclass(frozen=True)
class AuthContext:
    token_type: str
    user_id: Optional[str] = None
    customer_id: Optional[str] = None
    roles: Optional[list[str]] = None


def _base64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _parse_token_payload(token: str) -> dict[str, Any]:
    parts = token.split(".")
    if len(parts) == 3:
        try:
            payload_raw = _base64url_decode(parts[1]).decode("utf-8")
            payload = json.loads(payload_raw)
            if isinstance(payload, dict):
                return payload
        except Exception:
            pass

    try:
        payload = json.loads(token)
        if isinstance(payload, dict):
            return payload
    except Exception:
        pass

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def _extract_bearer_token(request: Request) -> str:
    auth_header = request.headers.get("authorization")
    if not auth_header:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")

    parts = auth_header.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Authorization header")

    return parts[1].strip()


def get_auth_context(request: Request) -> AuthContext:
    token = _extract_bearer_token(request)

    payload = _parse_token_payload(token)
    token_type = payload.get("tokenType")
    if token_type not in {"internal", "customer"}:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid tokenType")

    if token_type == "internal":
        user_id = payload.get("userId")
        roles = payload.get("roles")
        if not isinstance(user_id, str) or not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid internal token")
        if roles is None:
            roles_list: list[str] = []
        elif isinstance(roles, list) and all(isinstance(r, str) for r in roles):
            roles_list = list(roles)
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid roles")

        return AuthContext(token_type="internal", user_id=user_id, roles=roles_list)

    customer_id = payload.get("customerId")
    if not isinstance(customer_id, str) or not customer_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid customer token")

    return AuthContext(token_type="customer", customer_id=customer_id)
