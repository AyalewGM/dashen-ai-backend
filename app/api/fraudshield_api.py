from fastapi import APIRouter, HTTPException, Request

from app.modules.fraudshield.models import (
    FraudAlertsRequestModel,
    FraudAlertsResponseModel,
    FraudScoreRequestModel,
    FraudScoreResponseModel,
)
from app.modules.fraudshield.service import FraudShieldService
from app.modules.shared.logging import log_error
from app.modules.shared.language import resolve_language

router = APIRouter()
service = FraudShieldService()


@router.post("/fraud/score", response_model=FraudScoreResponseModel)
async def score_fraud(http_request: Request, request: FraudScoreRequestModel) -> FraudScoreResponseModel:
    try:
        language = await resolve_language(http_request)
        return await service.score_event(request, language=language)
    except ValueError as exc:
        log_error(module="fraudshield", session_id=request.event.session_id if request.event else None, error=exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        log_error(module="fraudshield", session_id=request.event.session_id if request.event else None, error=exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post("/fraud/alerts", response_model=FraudAlertsResponseModel)
async def fraud_alerts(http_request: Request, request: FraudAlertsRequestModel) -> FraudAlertsResponseModel:
    try:
        language = await resolve_language(http_request)
        return await service.generate_alerts(request, language=language)
    except ValueError as exc:
        log_error(module="fraudshield", session_id=None, error=exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        log_error(module="fraudshield", session_id=None, error=exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc
