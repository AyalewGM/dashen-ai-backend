from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Session:
    id: str
    messages: list[dict[str, Any]] = field(default_factory=list)


def get_session(session_id: str) -> Session:
    """Simple helper for now; later can look up user/profile/state."""
    return Session(id=session_id)
