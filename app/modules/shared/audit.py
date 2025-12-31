from __future__ import annotations

import datetime as dt
from typing import Any, Optional

from .logging import logger


def audit_log(
    event_type: str,
    actor: dict[str, Any],
    resource: dict[str, Any],
    metadata: Optional[dict[str, Any]] = None,
) -> None:
    payload: dict[str, Any] = {
        "eventType": event_type,
        "timestamp": dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc).isoformat(),
        "actor": actor,
        "resource": resource,
        "metadata": metadata or {},
    }

    logger.info("audit", extra={"service_module": "audit", "session_id": "-", "audit": payload})
