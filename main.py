from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from app.api.conversation_api import router as conversation_router
from app.api.voice_ai_api import router as voice_ai_router


def create_app() -> FastAPI:
    app = FastAPI(title="Dashen AI Platform", version="0.1.0")

    # Allow frontend dev server to access the API
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(conversation_router, prefix="/api")
    app.include_router(voice_ai_router, prefix="/api")
    

    return app


app = create_app()
