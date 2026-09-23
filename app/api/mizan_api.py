from fastapi import APIRouter, HTTPException

from app.modules.mizan.models import MizanScoreRequest, MizanScoreResponse
from app.modules.mizan.score_engine import score_application

router = APIRouter()


@router.post("/mizan/score", response_model=MizanScoreResponse)
async def mizan_score(request: MizanScoreRequest) -> MizanScoreResponse:
    """
    Rule-based credit scoring endpoint for Mizan.
    Returns score, grade, probability of default, DSR, and decision.
    """
    try:
        return score_application(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Internal scoring error") from exc
