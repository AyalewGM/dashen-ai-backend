from typing import Any, Optional

from .llm_assistant import assistant
from .sessions import Session


async def chat_text(
    *,
    session: Session,
    language: str,
    message: str,
    context: Optional[dict[str, Any]] = None,
    bank_id: str = "dashen",
) -> dict[str, Any]:
    """Shared text-assistant entrypoint for all text-based interactions.

    Returns the same structured dict as LlmAssistant.generate_reply.
    """

    return await assistant.generate_reply(
        session=session,
        language=language,
        message=message,
        context=context,
        bank_id=bank_id,
    )
