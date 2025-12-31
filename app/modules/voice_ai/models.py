from typing import Optional

from pydantic import BaseModel, Field


class VoiceQueryResponse(BaseModel):
    transcript: str
    reply: str
    language: str
    tts_audio_url: Optional[str] = Field(default=None, alias="ttsAudioUrl")

    class Config:
        populate_by_name = True


class NotificationTemplate(BaseModel):
    id: str
    title: str
    body: str


class NotificationSendRequest(BaseModel):
    template_id: str = Field(..., alias="templateId")
    channel: str
    preview_only: bool = Field(default=False, alias="previewOnly")
    language: Optional[str] = None

    class Config:
        populate_by_name = True


class NotificationSendResponse(BaseModel):
    template_id: str = Field(..., alias="templateId")
    channel: str
    preview_only: bool = Field(..., alias="previewOnly")
    language: str
    status: str

    class Config:
        populate_by_name = True
