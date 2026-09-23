from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.modules.banking_intelligence.models import (
    BranchAnalysisResponse,
    DecisionSupportRequest,
    DecisionSupportResponse,
    NaturalQueryRequest,
    NaturalQueryResponse,
    PredictiveRequest,
    PredictiveResponse,
    RealTimeIntelligenceResponse,
    UnifiedDashboardRequest,
    UnifiedDashboardResponse,
)
from app.modules.banking_intelligence.service import BankingIntelligenceService
from app.modules.shared.language import resolve_language
from app.modules.shared.logging import log_error

router = APIRouter()
service = BankingIntelligenceService()


@router.post("/dashboard", response_model=UnifiedDashboardResponse)
async def unified_dashboard(
    http_request: Request,
    request: UnifiedDashboardRequest,
    db: Session = Depends(get_db),
) -> UnifiedDashboardResponse:
    try:
        language = await resolve_language(http_request)
        return await service.get_unified_dashboard(request, language=language, db=db)
    except Exception as exc:  # noqa: BLE001
        log_error(module="banking_intelligence", session_id=None, error=exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post("/predict", response_model=PredictiveResponse)
async def predict_metric(http_request: Request, request: PredictiveRequest) -> PredictiveResponse:
    try:
        language = await resolve_language(http_request)
        return await service.predict_metric(request, language=language)
    except ValueError as exc:
        log_error(module="banking_intelligence", session_id=None, error=exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        log_error(module="banking_intelligence", session_id=None, error=exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post("/decision-support", response_model=DecisionSupportResponse)
async def decision_support(http_request: Request, request: DecisionSupportRequest) -> DecisionSupportResponse:
    try:
        language = await resolve_language(http_request)
        return await service.decision_support(request, language=language)
    except ValueError as exc:
        log_error(module="banking_intelligence", session_id=None, error=exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        log_error(module="banking_intelligence", session_id=None, error=exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/realtime", response_model=RealTimeIntelligenceResponse)
async def real_time_intelligence(http_request: Request, bank_id: str = "dashen") -> RealTimeIntelligenceResponse:
    try:
        language = await resolve_language(http_request)
        return await service.real_time_intelligence(bank_id=bank_id, language=language)
    except Exception as exc:  # noqa: BLE001
        log_error(module="banking_intelligence", session_id=None, error=exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post("/natural-query", response_model=NaturalQueryResponse)
async def natural_language_query(http_request: Request, request: NaturalQueryRequest) -> NaturalQueryResponse:
    """
    Process natural language analytics queries
    
    Example queries:
    - "Show me revenue by branch in Addis Ababa for last 3 months as bar chart"
    - "Compare customer growth between Addis and Bahir Dar"
    - "What are the top 5 branches by loan disbursements this quarter?"
    - "Give me analytics of Addis Ababa branches for the last 3 months in bar chart"
    """
    try:
        return await service.process_natural_query(request)
    except ValueError as exc:
        log_error(module="banking_intelligence", session_id=None, error=exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        log_error(module="banking_intelligence", session_id=None, error=exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/branch-performance", response_model=BranchAnalysisResponse)
async def branch_performance_analysis(http_request: Request, bank_id: str = "dashen") -> BranchAnalysisResponse:
    """
    Comprehensive branch performance analysis with predictive and prescriptive insights
    
    Returns:
    - Top 5 and bottom 5 performing branches
    - Detailed analysis of worst performer
    - Specific improvement areas with gap analysis
    - Predictive forecasts (3m, 6m, 12m)
    - Quick wins (immediate actions)
    - Strategic initiatives (long-term improvements)
    - Executive summary and key insights
    """
    try:
        language = await resolve_language(http_request)
        return await service.analyze_branch_performance(bank_id=bank_id, language=language)
    except Exception as exc:  # noqa: BLE001
        log_error(module="banking_intelligence", session_id=None, error=exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc
