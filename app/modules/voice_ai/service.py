from fastapi import UploadFile

from app.modules.shared.sessions import get_session
from app.modules.shared.text_assistant import chat_text

from .models import (
    NotificationSendRequest,
    NotificationSendResponse,
    NotificationTemplate,
    VoiceQueryResponse,
)
from .templates import get_template_by_id, list_templates


class VoiceAIService:
    async def handle_voice_query(
        self,
        *,
        session_id: str,
        language: str,
        audio_file: UploadFile,
    ) -> VoiceQueryResponse:
        # In a real system, decode audio_file and send to STT engine.
        # For now, we simulate transcription using the filename.
        simulated_transcript = f"Transcribed text from {audio_file.filename}"

        return VoiceQueryResponse(
            transcript=simulated_transcript,
            reply=(
                await chat_text(
                    session=get_session(session_id),
                    language=language,
                    message=simulated_transcript,
                    context=None,
                )
            )["reply"],
            language=language,
            ttsAudioUrl=None,
        )

    def list_notification_templates(self) -> list[NotificationTemplate]:
        return list_templates()

    def send_notification(self, request: NotificationSendRequest, *, language: str) -> NotificationSendResponse:
        template = get_template_by_id(request.template_id)
        if not template:
            raise ValueError("Template not found")

        # Simulate sending: in real system, integrate with SMS/IVR/push provider
        _session = get_session("notification")
        status = "preview" if request.preview_only else "sent"
        return NotificationSendResponse(
            templateId=request.template_id,
            channel=request.channel,
            previewOnly=request.preview_only,
            language=language,
            status=status,
        )
