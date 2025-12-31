from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from app.api.conversation_api import router as conversation_router
from app.api.customer_insights_api import router as customer_insights_router
from app.api.fraudshield_api import router as fraudshield_router
from app.api.ingestion_api import router as ingestion_router
from app.api.internal_insights_api import router as internal_insights_router
from app.api.voice_ai_api import router as voice_ai_router
from app.modules.shared.db import ensure_tables_exist


def create_app() -> FastAPI:
    app = FastAPI(title="Dashen AI Platform", version="0.1.0")

    @app.on_event("startup")
    async def _startup() -> None:
        ensure_tables_exist()

    # Allow frontend dev server to access the API
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(conversation_router, prefix="/api")
    app.include_router(ingestion_router, prefix="/api/internal/ingestion")
    app.include_router(internal_insights_router, prefix="/api/internal/insights")
    app.include_router(customer_insights_router, prefix="/api/customer/insights")
    app.include_router(fraudshield_router, prefix="/api")
    app.include_router(voice_ai_router, prefix="/api")
    

    return app


app = create_app()
