import logging
from typing import Any, Optional

from .config import config


logger = logging.getLogger("dashen_ai_platform")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(environment)s] [%(service_module)s] [session=%(session_id)s] %(message)s",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:  # type: ignore[override]
        if not hasattr(record, "environment"):
            record.environment = config.environment
        if not hasattr(record, "session_id"):
            record.session_id = getattr(record, "session_id", "-")
        return True


logger.addFilter(ContextFilter())


def log_request(module: str, session_id: Optional[str], extra: Optional[dict[str, Any]] = None) -> None:
    logger.info("request received", extra={"service_module": module, "session_id": session_id, **(extra or {})})


def log_response(module: str, session_id: Optional[str], extra: Optional[dict[str, Any]] = None) -> None:
    logger.info("response sent", extra={"service_module": module, "session_id": session_id, **(extra or {})})


def log_error(module: str, session_id: Optional[str], error: Exception, extra: Optional[dict[str, Any]] = None) -> None:
    logger.exception(
        "error occurred",
        extra={"service_module": module, "session_id": session_id, "error": str(error), **(extra or {})},
    )
