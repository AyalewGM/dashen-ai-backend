import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

load_dotenv()

from app.api.bank_api import router as bank_router
from app.api.banking_intelligence_api import router as banking_intelligence_router
from app.api.conversation_api import router as conversation_router
from app.api.customer_insights_api import router as customer_insights_router
from app.api.customer360_api import router as customer360_router
from app.api.escalation_api import router as escalation_router
from app.api.fraudshield_api import router as fraudshield_router
from app.api.ingestion_api import router as ingestion_router
from app.api.internal_insights_api import router as internal_insights_router
from app.api.mizan_api import router as mizan_router
from app.api.voice_ai_api import router as voice_ai_router
from app.modules.shared.db import ensure_tables_exist


def create_app() -> FastAPI:
    app = FastAPI(title="FraudShield AI Platform", version="0.1.0")

    @app.on_event("startup")
    async def _startup() -> None:
        ensure_tables_exist()

    allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in allowed_origins],
        allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(bank_router, prefix="/api")
    app.include_router(banking_intelligence_router, prefix="/api/banking-intelligence")
    app.include_router(conversation_router, prefix="/api")
    app.include_router(escalation_router)
    app.include_router(ingestion_router, prefix="/api/internal/ingestion")
    app.include_router(internal_insights_router, prefix="/api/internal/insights")
    app.include_router(customer_insights_router, prefix="/api/customer/insights")
    app.include_router(customer360_router, prefix="/api/customer360")
    app.include_router(fraudshield_router, prefix="/api")
    app.include_router(mizan_router, prefix="/api")
    app.include_router(voice_ai_router, prefix="/api")

    # Serve static files (bank logos, etc.)
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if os.path.isdir(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
    

    return app


app = create_app()
