from typing import List, Optional

from pydantic import BaseModel, Field


class MizanScoreRequest(BaseModel):
    income: float = Field(..., gt=0, description="Monthly gross income")
    obligations: float = Field(..., ge=0, description="Monthly existing obligations")
    amount: float = Field(..., gt=0, description="Requested loan amount")
    term: int = Field(..., gt=0, description="Term in months")
    product: str = Field(default="retail", description="retail | sme | auto | employee")
    bank_id: str = Field(default="dashen")
    customer_id: Optional[str] = None


class MizanScoreResponse(BaseModel):
    score: int
    grade: str
    pd: float
    dti: float
    installment: float
    decision: str
    positive_factors: List[str]
    risk_factors: List[str]
    policy_trace: str
