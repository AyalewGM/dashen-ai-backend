from fastapi import APIRouter

from .conversation_api import router as conversation_router
from .voice_ai_api import router as voice_ai_router

api_router = APIRouter()
api_router.include_router(conversation_router, prefix="/chat", tags=["conversation"])
api_router.include_router(voice_ai_router, prefix="/voice", tags=["voice_ai"])
