from .models import MizanScoreRequest, MizanScoreResponse

PRODUCT_THRESHOLDS = {
    "retail": {
        "min_score": 650,
        "min_score_review": 570,
        "max_dti": 0.45,
        "max_dti_review": 0.58,
    },
    "sme": {
        "min_score": 620,
        "min_score_review": 540,
        "max_dti": 0.50,
        "max_dti_review": 0.65,
    },
    "auto": {
        "min_score": 640,
        "min_score_review": 560,
        "max_dti": 0.48,
        "max_dti_review": 0.60,
    },
    "employee": {
        "min_score": 600,
        "min_score_review": 520,
        "max_dti": 0.50,
        "max_dti_review": 0.65,
    },
}


def _grade(score: int) -> str:
    if score >= 720:
        return "A"
    if score >= 650:
        return "B"
    if score >= 580:
        return "C"
    return "D"


def score_application(req: MizanScoreRequest) -> MizanScoreResponse:
    installment = req.amount / req.term * 1.12
    dti = (req.obligations + installment) / max(req.income, 1)
    income_multiple = req.amount / max(req.income, 1)

    score = max(
        420,
        min(820, round(790 - dti * 260 - income_multiple * 3)),
    )
    pd = max(1.2, min(28.0, (820 - score) / 15))
    grade = _grade(score)

    thresholds = PRODUCT_THRESHOLDS.get(req.product, PRODUCT_THRESHOLDS["retail"])

    if dti <= thresholds["max_dti"] and score >= thresholds["min_score"]:
        decision = "APPROVE"
    elif (
        dti <= thresholds["max_dti_review"]
        and score >= thresholds["min_score_review"]
    ):
        decision = "MANUAL REVIEW"
    else:
        decision = "DECLINE"

    positive = []
    risk = []

    if req.income >= 25000:
        positive.append("Verified income capacity")
    if req.obligations <= req.income * 0.2:
        positive.append("Low existing obligation burden")
    if req.term >= 18:
        positive.append("Requested term supports affordability")
    if dti <= 0.35:
        positive.append("Strong debt-service capacity")

    if dti > thresholds["max_dti"]:
        risk.append(
            f"Projected debt-service ratio is {(dti * 100):.1f}%, "
            f"above the {thresholds['max_dti'] * 100:.0f}% approval threshold"
        )
    if score < thresholds["min_score"]:
        risk.append(
            f"Credit score {score} is below the {thresholds['min_score']} "
            f"threshold for {req.product} lending"
        )
    if income_multiple > 6:
        risk.append(
            f"Requested exposure equals {income_multiple:.1f} months of verified income"
        )
    if req.obligations > req.income * 0.3:
        risk.append("Existing obligations consume a large share of income")

    if not positive:
        positive.append("Application received and evaluated")
    if not risk:
        risk.append("No major risk factors identified")

    policy_trace = (
        f"{req.bank_id}-{req.product}-v1 affordability and score threshold evaluation"
    )

    return MizanScoreResponse(
        score=score,
        grade=grade,
        pd=round(pd, 1),
        dti=round(dti, 4),
        installment=round(installment, 2),
        decision=decision,
        positive_factors=positive,
        risk_factors=risk,
        policy_trace=policy_trace,
    )
