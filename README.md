# Dashen AI Platform Backend (Modular Monolith)

## Structure

- `main.py` – FastAPI app entrypoint, includes API routers.
- `app/api/` – HTTP layer only (routing, validation, serialization).
  - `conversation_api.py` – `/api/chat/*` endpoints.
  - `voice_ai_api.py` – `/api/voice/*` endpoints.
- `app/modules/` – Internal service-style modules.
  - `conversation/` – Text chatbot domain (models + service).
  - `voice_ai/` – Voice assistant + notifications (models + templates + service).
  - `shared/` – Cross-cutting concerns (config, logging, llm assistant, sessions).
- `tests/` – API-level tests for conversation and voice_ai.

## Adding a New Domain (e.g. Fraud Detection)

1. Create a new folder under `app/modules/`, e.g. `fraud/` with:
   - `__init__.py`
   - `models.py` – request/response/domain models.
   - `service.py` – business logic for the fraud domain.
2. Add a new API file under `app/api/`, e.g. `fraud_api.py` that:
   - Defines a FastAPI `APIRouter`.
   - Validates HTTP input, maps to `fraud.models` types.
   - Calls into `fraud.service` for all business logic.
   - Maps results back to HTTP responses.
3. Wire the new router in `main.py` (or `app/api/__init__.py`) using `include_router`.
4. Reuse shared infrastructure from `app/modules/shared` as needed (config, logging, llm assistant, sessions).

This keeps a **single deployable server** while organizing each domain as its own internal service-style module with clear boundaries.
