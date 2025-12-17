from dataclasses import dataclass


@dataclass(frozen=True)
class Session:
    id: str


def get_session(session_id: str) -> Session:
    """Simple helper for now; later can look up user/profile/state."""
    return Session(id=session_id)
