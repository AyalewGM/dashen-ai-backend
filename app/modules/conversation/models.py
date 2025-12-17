from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(..., alias="sessionId")
    message: str
    language: str = Field(..., pattern="^(am|om|ti|en)$")


class ChatMetadata(BaseModel):
    model: str
    latency_ms: int = Field(..., alias="latencyMs")
    source_docs: Optional[list[str]] = Field(default=None, alias="sourceDocs")

    class Config:
        populate_by_name = True


class ChatResponse(BaseModel):
    reply: str
    language: str
    metadata: ChatMetadata

    class Config:
        populate_by_name = True
