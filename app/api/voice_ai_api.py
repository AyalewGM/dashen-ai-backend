from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from app.modules.voice_ai.models import (
    NotificationSendRequest,
    NotificationSendResponse,
    NotificationTemplate,
    VoiceQueryResponse,
)
from app.modules.voice_ai.service import VoiceAIService
from app.modules.shared.logging import log_request, log_response, log_error
from app.modules.shared.language import resolve_language

router = APIRouter()
service = VoiceAIService()


@router.post("/query", response_model=VoiceQueryResponse)
async def voice_query(
    http_request: Request,
    session_id: str = Form(...),
    language: str | None = Form(default=None),
    audio_file: UploadFile = File(...),
) -> VoiceQueryResponse:
    resolved_language = await resolve_language(http_request)
    log_request(module="voice_ai", session_id=session_id, extra={"language": resolved_language})
    try:
        response = await service.handle_voice_query(
            session_id=session_id,
            language=resolved_language,
            audio_file=audio_file,
        )
        log_response(module="voice_ai", session_id=session_id)
        return response
    except Exception as exc:  # noqa: BLE001
        log_error(module="voice_ai", session_id=session_id, error=exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/templates", response_model=list[NotificationTemplate])
async def list_templates(_http_request: Request) -> list[NotificationTemplate]:
    return service.list_notification_templates()


@router.post("/send", response_model=NotificationSendResponse)
async def send_notification(http_request: Request, request: NotificationSendRequest) -> NotificationSendResponse:
    resolved_language = await resolve_language(http_request)
    log_request(
        module="voice_ai",
        session_id=None,
        extra={"template_id": request.template_id, "language": resolved_language},
    )
    try:
        response = service.send_notification(request, language=resolved_language)
        log_response(module="voice_ai", session_id=None)
        return response
    except ValueError as exc:
        log_error(module="voice_ai", session_id=None, error=exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        log_error(module="voice_ai", session_id=None, error=exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc
