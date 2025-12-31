from fastapi import APIRouter, HTTPException, Request
import logging as logger 
from app.modules.conversation.models import ChatRequest, ChatResponse
from app.modules.conversation.service import ConversationService
from app.modules.shared.logging import log_error
from app.modules.shared.language import resolve_language

router = APIRouter()
service = ConversationService()


@router.post("/chat", response_model=ChatResponse)
async def chat(http_request: Request, request: ChatRequest) -> ChatResponse:
    logger.info(request)
    try:
        language = await resolve_language(http_request)
        return await service.handle_chat(request, language=language)
    except ValueError as exc:
        log_error(module="conversation", session_id=request.session_id, error=exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        log_error(module="conversation", session_id=request.session_id, error=exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc
