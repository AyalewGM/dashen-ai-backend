from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from app.modules.ingestion.models import DatasetType, IngestionSeedDemoResponse, IngestionUploadResponse
from app.modules.ingestion.service import IngestionService
from app.modules.shared.audit import audit_log
from app.modules.shared.auth import get_auth_context
from app.modules.shared.rbac import require_internal_roles


router = APIRouter()
service = IngestionService()

_ALLOWED_UPLOAD_ROLES = {"ROLE_ANALYTICS", "ROLE_EXECUTIVE"}
_ALLOWED_SEED_ROLES = {"ROLE_ANALYTICS"}


@router.post("/upload", response_model=IngestionUploadResponse)
async def upload_dataset(
    request: Request,
    file: UploadFile = File(...),
    dataset_type: DatasetType = Form(..., alias="datasetType"),
    dataset_name: str = Form(..., alias="datasetName"),
) -> IngestionUploadResponse:
    auth = get_auth_context(request)
    try:
        require_internal_roles(auth, _ALLOWED_UPLOAD_ROLES)
        resp = service.upload_and_ingest(
            file=file,
            dataset_type=dataset_type,
            dataset_name=dataset_name,
            uploaded_by_actor_type=auth.token_type,
            uploaded_by_actor_id=auth.user_id or "-",
        )
        audit_log(
            event_type="dataset_upload",
            actor={"actorType": auth.token_type, "actorId": auth.user_id},
            resource={"endpoint": "/api/internal/ingestion/upload"},
            metadata={
                "outcome": "success",
                "datasetType": dataset_type,
                "datasetName": dataset_name,
                "rowCount": resp.row_count,
                "datasetId": resp.dataset_id,
            },
        )
        return resp
    except HTTPException:
        audit_log(
            event_type="dataset_upload",
            actor={"actorType": auth.token_type, "actorId": auth.user_id or auth.customer_id},
            resource={"endpoint": "/api/internal/ingestion/upload"},
            metadata={"outcome": "denied"},
        )
        raise
    except ValueError as exc:
        audit_log(
            event_type="dataset_upload",
            actor={"actorType": auth.token_type, "actorId": auth.user_id or auth.customer_id},
            resource={"endpoint": "/api/internal/ingestion/upload"},
            metadata={"outcome": "invalid", "error": str(exc)},
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        audit_log(
            event_type="dataset_upload",
            actor={"actorType": auth.token_type, "actorId": auth.user_id or auth.customer_id},
            resource={"endpoint": "/api/internal/ingestion/upload"},
            metadata={"outcome": "error", "error": str(exc)},
        )
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        audit_log(
            event_type="dataset_upload",
            actor={"actorType": auth.token_type, "actorId": auth.user_id or auth.customer_id},
            resource={"endpoint": "/api/internal/ingestion/upload"},
            metadata={"outcome": "error"},
        )
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post("/seed-demo", response_model=IngestionSeedDemoResponse)
async def seed_demo(request: Request) -> IngestionSeedDemoResponse:
    auth = get_auth_context(request)
    try:
        require_internal_roles(auth, _ALLOWED_SEED_ROLES)
        resp = service.seed_demo()
        audit_log(
            event_type="seed_demo",
            actor={"actorType": auth.token_type, "actorId": auth.user_id},
            resource={"endpoint": "/api/internal/ingestion/seed-demo"},
            metadata={"outcome": "success", "counts": resp.counts},
        )
        return resp
    except HTTPException:
        audit_log(
            event_type="seed_demo",
            actor={"actorType": auth.token_type, "actorId": auth.user_id or auth.customer_id},
            resource={"endpoint": "/api/internal/ingestion/seed-demo"},
            metadata={"outcome": "denied"},
        )
        raise
    except RuntimeError as exc:
        audit_log(
            event_type="seed_demo",
            actor={"actorType": auth.token_type, "actorId": auth.user_id or auth.customer_id},
            resource={"endpoint": "/api/internal/ingestion/seed-demo"},
            metadata={"outcome": "error", "error": str(exc)},
        )
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        audit_log(
            event_type="seed_demo",
            actor={"actorType": auth.token_type, "actorId": auth.user_id or auth.customer_id},
            resource={"endpoint": "/api/internal/ingestion/seed-demo"},
            metadata={"outcome": "error"},
        )
        raise HTTPException(status_code=500, detail="Internal server error") from exc
