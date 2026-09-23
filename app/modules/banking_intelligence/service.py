from __future__ import annotations

import hashlib
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session as DBSession

from app.modules.shared.bank_config import get_bank_config
from app.modules.shared.sessions import Session

from .models import (
    BranchAnalysisResponse,
    BranchMetrics,
    BranchPrediction,
    ChartConfig,
    ChartDataPoint,
    DecisionOption,
    DecisionSupportRequest,
    DecisionSupportResponse,
    ForecastPoint,
    ImprovementArea,
    KpiCard,
    NaturalQueryRequest,
    NaturalQueryResponse,
    ParsedQuery,
    PerformanceMetric,
    PerformanceMetrics,
    PredictiveRequest,
    PredictiveResponse,
    RealTimeAlert,
    RealTimeIntelligenceResponse,
    TrendPoint,
    UnifiedDashboardRequest,
    UnifiedDashboardResponse,
)
from .query_parser import query_parser


def _stable_hash(value: str | int) -> int:
    """Return a stable integer hash that survives process restarts.

    Python's built-in hash() is randomized per process, which makes demo
    branch/chart data change every time the server restarts. SHA-256 is
    deterministic, so the same input always produces the same output.
    """
    return int(hashlib.sha256(str(value).encode()).hexdigest(), 16)


def _build_insights(
    data: list,
    max_point,
    min_point,
    avg: float,
    total: float,
    parsed_query: dict,
) -> list[str]:
    """Build useful insights without redundant highest/lowest for single results."""
    if len(data) == 1:
        metric = parsed_query.get("metrics", ["value"])[0]
        group = parsed_query.get("group_by", "result")
        return [
            f"Total {metric}: {total:,.2f}",
            f"Only one {group} in this query: {data[0].label}",
            f"Average value: {avg:,.2f}",
        ]

    if max_point.value == min_point.value:
        return [
            f"All {len(data)} results have the same value: {max_point.value:,.2f}",
            f"Average: {avg:,.2f}",
            f"Total: {total:,.2f}",
        ]

    return [
        f"Highest: {max_point.label} ({max_point.value:,.2f})",
        f"Lowest: {min_point.label} ({min_point.value:,.2f})",
        f"Average: {avg:,.2f}",
    ]


_KPI_METRIC_MAP = {
    "Total Deposits": ("deposits", "currency"),
    "Active Customers": ("customer_count", "count"),
    "Digital Adoption": ("digital_adoption", "percent"),
    "Loan Portfolio": ("loans", "currency"),
    "NPL Ratio": ("npl_proxy", "percent"),
}


def _format_metric(value: float, kind: str) -> str:
    if kind == "currency":
        if value >= 1_000_000_000:
            return f"{value / 1_000_000_000:.1f}B ETB"
        if value >= 1_000_000:
            return f"{value / 1_000_000:.1f}M ETB"
        return f"{value:,.0f} ETB"
    if kind == "percent":
        return f"{value * 100:.1f}%"
    return f"{value:,.0f}"


def _delta_and_trend(current: float, previous: float | None, kind: str) -> tuple[str, str, str, float]:
    if previous is None or previous == 0:
        return ("0.0%", "flat", "info", 0.0)
    change = current - previous
    pct = (change / previous) * 100
    delta_str = f"{pct:+.1f}%"
    if kind == "percent" and current < previous:
        # For NPL, decreasing is good
        return (delta_str, "down", "success", round(pct, 1))
    if kind == "percent" and current > previous:
        return (delta_str, "up", "warning", round(pct, 1))
    if pct > 0:
        return (delta_str, "up", "success", round(pct, 1))
    if pct < 0:
        return (delta_str, "down", "danger", round(pct, 1))
    return (delta_str, "flat", "info", round(pct, 1))


def _load_internal_kpis(db: DBSession, bank_id: str) -> dict[str, dict]:
    """Load latest and previous internal KPI values keyed by metric_name."""
    if db is None:
        return {}
    try:
        date_rows = db.execute(
            text("""
                SELECT DISTINCT kpi_date
                FROM internal_kpis
                WHERE bank_id = :bank_id
                ORDER BY kpi_date DESC
                LIMIT 2
            """),
            {"bank_id": bank_id},
        ).fetchall()

        if not date_rows:
            return {}

        latest_date = date_rows[0][0]
        previous_date = date_rows[1][0] if len(date_rows) > 1 else None

        latest_rows = db.execute(
            text("""
                SELECT metric_name, metric_value
                FROM internal_kpis
                WHERE bank_id = :bank_id AND kpi_date = :date
            """),
            {"bank_id": bank_id, "date": latest_date},
        ).fetchall()

        previous_rows = []
        if previous_date:
            previous_rows = db.execute(
                text("""
                    SELECT metric_name, metric_value
                    FROM internal_kpis
                    WHERE bank_id = :bank_id AND kpi_date = :date
                """),
                {"bank_id": bank_id, "date": previous_date},
            ).fetchall()

        metrics = {}
        for metric_name, value in latest_rows:
            metrics[metric_name] = {"current": float(value), "previous": None}
        for metric_name, value in previous_rows:
            if metric_name in metrics:
                metrics[metric_name]["previous"] = float(value)

        return metrics
    except Exception:
        return {}


def _load_fraud_alert_count(db: DBSession, bank_id: str, days: int = 30) -> int:
    if db is None:
        return 0
    try:
        result = db.execute(
            text("""
                SELECT COUNT(*)
                FROM fraud_events
                WHERE bank_id = :bank_id
                  AND event_timestamp >= NOW() - INTERVAL '1 day' * :days
                  AND risk_level IN ('high', 'medium')
            """),
            {"bank_id": bank_id, "days": days},
        ).scalar()
        return int(result or 0)
    except Exception:
        return 0


def _load_metric_trend(
    db: DBSession, bank_id: str, metric_name: str, limit: int = 12
) -> list[TrendPoint]:
    """Load the most recent data points for a metric as a trend series."""
    if db is None:
        return []
    try:
        rows = db.execute(
            text("""
                SELECT kpi_date, metric_value
                FROM internal_kpis
                WHERE bank_id = :bank_id AND metric_name = :metric_name
                ORDER BY kpi_date DESC
                LIMIT :limit
            """),
            {"bank_id": bank_id, "metric_name": metric_name, "limit": limit},
        ).fetchall()

        points: list[TrendPoint] = []
        for row in reversed(rows):
            date_value, metric_value = row
            label = date_value.strftime("%b %d") if hasattr(date_value, "strftime") else str(date_value)
            points.append(TrendPoint(date=label, value=float(metric_value or 0)))
        return points
    except Exception:
        return []


class BankingIntelligenceService:
    """Enterprise intelligence platform with unified analytics and AI-driven decision support."""

    async def get_unified_dashboard(
        self,
        request: UnifiedDashboardRequest,
        *,
        language: str = "en",
        db: DBSession | None = None,
    ) -> UnifiedDashboardResponse:
        """Unified dashboard with real-time KPIs and performance metrics."""
        bank_config = get_bank_config(request.bank_id)

        kpi_cards: list[KpiCard] = []
        performance_metrics: PerformanceMetrics | None = None
        data_source = "live database"

        metrics = _load_internal_kpis(db, request.bank_id)

        if metrics:
            # Build KPI cards from internal_kpis table
            for title, (metric_name, kind) in _KPI_METRIC_MAP.items():
                current = metrics.get(metric_name, {}).get("current")
                previous = metrics.get(metric_name, {}).get("previous")
                if current is None:
                    continue
                delta, trend, severity, _ = _delta_and_trend(current, previous, kind)
                kpi_cards.append(
                    KpiCard(
                        title=title,
                        value=_format_metric(current, kind),
                        delta=delta,
                        change=delta,
                        trend=trend,
                        severity=severity,
                    )
                )

            # Fraud alerts from fraud_events table
            alert_count = _load_fraud_alert_count(db, request.bank_id)
            alert_delta = "last 30 days"
            kpi_cards.append(
                KpiCard(
                    title="Fraud Alerts",
                    value=str(alert_count),
                    delta=alert_delta,
                    change=alert_delta,
                    trend="flat",
                    severity="warning" if alert_count > 10 else "info",
                )
            )

            # Build chart trend series from internal_kpis
            performance_metrics = PerformanceMetrics(
                revenueTrend=_load_metric_trend(db, request.bank_id, "revenue"),
                customerGrowth=_load_metric_trend(db, request.bank_id, "customer_count"),
                transactionVolume=_load_metric_trend(db, request.bank_id, "transaction_volume"),
                loanPortfolio=_load_metric_trend(db, request.bank_id, "loans"),
            )
        else:
            # Fallback to deterministic demo data when no DB rows exist
            data_source = "simulated demo data"
            seed = int(hashlib.sha256(f"{request.bank_id}-{datetime.now(timezone.utc).strftime('%Y%m%d')}".encode()).hexdigest(), 16)
            kpi_cards = [
                KpiCard(
                    title="Total Deposits",
                    value=f"{45.2 + (seed % 20):.1f}B ETB",
                    delta=f"+{3 + (seed % 5):.1f}%",
                    change=f"+{3 + (seed % 5):.1f}%",
                    trend="up",
                    severity="success",
                ),
                KpiCard(
                    title="Active Customers",
                    value=f"{1.2 + (seed % 8) / 10:.1f}M",
                    delta=f"+{2 + (seed % 3):.1f}%",
                    change=f"+{2 + (seed % 3):.1f}%",
                    trend="up",
                    severity="success",
                ),
                KpiCard(
                    title="Digital Adoption",
                    value=f"{62 + (seed % 15)}%",
                    delta=f"+{5 + (seed % 8)}%",
                    change=f"+{5 + (seed % 8)}%",
                    trend="up",
                    severity="info",
                ),
                KpiCard(
                    title="Loan Portfolio",
                    value=f"{32.5 + (seed % 15):.1f}B ETB",
                    delta=f"+{1 + (seed % 4):.1f}%",
                    change=f"+{1 + (seed % 4):.1f}%",
                    trend="up",
                    severity="success",
                ),
                KpiCard(
                    title="NPL Ratio",
                    value=f"{2.1 + (seed % 10) / 10:.1f}%",
                    delta=f"-{0.2 + (seed % 5) / 10:.1f}%",
                    change=f"-{0.2 + (seed % 5) / 10:.1f}%",
                    trend="down",
                    severity="success",
                ),
                KpiCard(
                    title="Fraud Alerts",
                    value=f"{12 + (seed % 20)}",
                    delta="2 critical" if (seed % 3) == 0 else "stable",
                    change="2 critical" if (seed % 3) == 0 else "stable",
                    trend="flat" if (seed % 2) == 0 else "down",
                    severity="warning" if (seed % 3) == 0 else "info",
                ),
            ]

            def _fallback_trend(base: float, variance: float, count: int = 7) -> list[TrendPoint]:
                points: list[TrendPoint] = []
                noise_scale = max(1.0, variance * 2)
                for i in range(count):
                    value = base + (i * variance) + ((seed + i * 13) % max(1, int(noise_scale)))
                    points.append(
                        TrendPoint(
                            date=(datetime.now(timezone.utc) - timedelta(days=count - i - 1)).strftime("%b %d"),
                            value=round(value, 2),
                        )
                    )
                return points

            performance_metrics = PerformanceMetrics(
                revenueTrend=_fallback_trend(2.3, 0.08),
                customerGrowth=_fallback_trend(1200000, 5000),
                transactionVolume=_fallback_trend(52000, 1200),
                loanPortfolio=_fallback_trend(32.0, 0.5),
            )

        # AI-generated insights
        narrative_map = {
            "en": f"{bank_config.bank_name} dashboard is powered by {data_source}. Latest KPIs show {kpi_cards[0].value} in total deposits ({kpi_cards[0].delta}), {kpi_cards[2].value} digital adoption ({kpi_cards[2].delta}), and an NPL ratio of {kpi_cards[4].value} ({kpi_cards[4].delta}). There are {kpi_cards[5].value} fraud alerts in the last 30 days.",
            "am": f"የ{bank_config.bank_name} ዳሽቦርድ በ{data_source} የተደገፈ ነው። የቅርብ ጊዜ ዋና ዋና የማየታት ውጤቶች፡ {kpi_cards[0].value} ጠቅላላ ተቀማጭ ({kpi_cards[0].delta})፣ {kpi_cards[2].value} ዲጂታል ተቀባይነት ({kpi_cards[2].delta})፣ እና {kpi_cards[4].value} NPL ጥምርታ ({kpi_cards[4].delta}) ያሳያል። በመጨረሻው 30 ቀናት ውስጥ {kpi_cards[5].value} የማጭበርበር ማስጠንቀቂያዎች አሉ።",
            "om": f"Daashboordii {bank_config.bank_name} {data_source} irradee hojjetama. Alaanoon gurguddoo {kpi_cards[0].value} qarshii seffamee ({kpi_cards[0].delta}) fi {kpi_cards[2].value} fudhatamuu dijitaalaa ({kpi_cards[2].delta}) fi reeshiyoonii NPL {kpi_cards[4].value} ({kpi_cards[4].delta}) agarsiisa. Torbanoota 30 darbanii keessaa akeekkachiisa gowwoomsaa {kpi_cards[5].value} jira.",
            "ti": f"ቦርድ {bank_config.bank_name} ብ{data_source} ዝተደገፈ እዩ። ዝቐርበ ገደስቲ ጸቕጥታት፡ {kpi_cards[0].value} ድማ ተቀማጢ ገንዘብ ({kpi_cards[0].delta})፣ {kpi_cards[2].value} ዲጂታላዊ ተቀባልነት ({kpi_cards[2].delta})፣ እና {kpi_cards[4].value} ናይ NPL ጥምርታ ({kpi_cards[4].delta}) የርኢ። ኣብ ዝሓለፉ 30 መዓልታት {kpi_cards[5].value} ናይ ምትላል ማስጠንቀቚታት ኣለዉ።",
            "so": f"Daashboorka {bank_config.bank_name} waxaa ku shaqada {data_source}. Calaamadaha ugu muhiimsan ee ugu dambeeyay waxay muujinayaan {kpi_cards[0].value} lacag la dhigay ({kpi_cards[0].delta}), {kpi_cards[2].value} aqbashada dhijitaalka ({kpi_cards[2].delta}), iyo heerka NPL {kpi_cards[4].value} ({kpi_cards[4].delta}). 30 cisho ee ugu dambeysay waxaa jira digniin {kpi_cards[5].value} oo khiyaanad ah.",
        }

        recommendations = [
            "Accelerate digital banking adoption through targeted campaigns",
            "Optimize loan portfolio mix to improve yield",
            "Implement advanced fraud detection for high-value transactions",
            "Expand mobile banking features based on customer feedback",
        ]

        return UnifiedDashboardResponse(
            kpiCards=kpi_cards,
            performanceMetrics=performance_metrics,
            insightNarrative=narrative_map.get(language, narrative_map["en"]),
            recommendations=recommendations,
            lastUpdated=datetime.now(timezone.utc).isoformat(),
        )

    async def predict_metric(
        self, request: PredictiveRequest, *, language: str = "en"
    ) -> PredictiveResponse:
        """Predictive analytics with forecasting and trend analysis."""
        bank_config = get_bank_config(request.bank_id)
        seed = int(hashlib.sha256(f"{request.metric_name}-{request.bank_id}".encode()).hexdigest(), 16) % 1000

        # Generate forecast points
        base_value = 50 + (seed % 50)
        trend_factor = (seed % 10) - 5  # -5 to +4
        forecast: list[ForecastPoint] = []

        for day in range(1, min(request.horizon_days, 90) + 1):
            # Simulate realistic growth/decline with noise
            predicted = base_value + (day * trend_factor * 0.1) + ((day * seed) % 7 - 3)
            confidence = max(0.6, 0.95 - (day * 0.005))  # Confidence decreases over time
            uncertainty = predicted * (1 - confidence) * 0.5

            forecast.append(
                ForecastPoint(
                    date=(datetime.now(timezone.utc) + timedelta(days=day)).strftime("%Y-%m-%d"),
                    predictedValue=round(predicted, 2),
                    lowerBound=round(predicted - uncertainty, 2),
                    upperBound=round(predicted + uncertainty, 2),
                    confidence=round(confidence, 2),
                )
            )

        # Determine trend direction
        if trend_factor > 1:
            trend_direction = "increasing"
        elif trend_factor < -1:
            trend_direction = "decreasing"
        else:
            trend_direction = "stable"

        # Risk factors and opportunities
        risk_factors = []
        opportunities = []

        if trend_direction == "decreasing":
            risk_factors.extend([
                "Declining trend may impact revenue targets",
                "Market competition intensifying",
                "Customer churn risk elevated",
            ])
            opportunities.extend([
                "Opportunity to implement retention strategies",
                "Potential for product innovation",
            ])
        elif trend_direction == "increasing":
            opportunities.extend([
                "Strong growth momentum to capitalize on",
                "Expand market share in high-growth segments",
                "Scale operations to meet demand",
            ])
            risk_factors.extend([
                "Operational capacity constraints",
                "Quality control during rapid growth",
            ])
        else:
            opportunities.extend([
                "Stable environment for strategic planning",
                "Focus on efficiency improvements",
            ])
            risk_factors.extend([
                "Market saturation risk",
                "Need for innovation to drive growth",
            ])

        narrative_map = {
            "en": f"Forecast for {request.metric_name} at {bank_config.bank_name} shows {trend_direction} trend over {request.horizon_days} days with {int(forecast[0].confidence * 100)}% initial confidence. {risk_factors[0] if risk_factors else 'Outlook is positive.'}",
            "am": f"የ{bank_config.bank_name} {request.metric_name} ትንበያ በ{request.horizon_days} ቀናት ውስጥ {trend_direction} አዝማሚያ በ{int(forecast[0].confidence * 100)}% የመጀመሪያ እምነት ያሳያል። {risk_factors[0] if risk_factors else 'ተስፋ ሰጪ ነው።'}",
            "om": f"Tilmaama {request.metric_name} {bank_config.bank_name}f guyyoota {request.horizon_days} keessatti kallattii {trend_direction} amantaa jalqabaa %{int(forecast[0].confidence * 100)}n agarsiisa. {risk_factors[0] if risk_factors else 'Ilaalchi gaarii dha.'}",
            "ti": f"ትንበያ {request.metric_name} ናይ {bank_config.bank_name} ኣብ {request.horizon_days} መዓልታት ኣንፈት {trend_direction} ብ{int(forecast[0].confidence * 100)}% ናይ መጀመርታ እምነት የርኢ። {risk_factors[0] if risk_factors else 'ተስፋ ዘለዎ እዩ።'}",
        }

        return PredictiveResponse(
            metricName=request.metric_name,
            forecast=forecast,
            trendDirection=trend_direction,
            confidenceLevel=round(sum(f.confidence for f in forecast) / len(forecast), 2),
            narrative=narrative_map.get(language, narrative_map["en"]),
            riskFactors=risk_factors[:3],
            opportunities=opportunities[:3],
        )

    async def decision_support(
        self, request: DecisionSupportRequest, *, language: str = "en"
    ) -> DecisionSupportResponse:
        """AI-driven decision support with scenario analysis."""
        bank_config = get_bank_config(request.bank_id)
        seed = int(hashlib.sha256(request.question.encode()).hexdigest(), 16) % 1000

        # Analyze question and generate options
        question_lower = request.question.lower()
        
        options: list[DecisionOption] = []

        if "loan" in question_lower or "credit" in question_lower:
            options = [
                DecisionOption(
                    option="Expand SME lending program",
                    impactScore=75.0 + (seed % 15),
                    riskLevel="medium",
                    expectedOutcome="15-20% increase in loan portfolio over 12 months",
                    pros=[
                        "High demand segment",
                        "Better risk-adjusted returns",
                        "Supports economic growth",
                    ],
                    cons=[
                        "Higher default risk than corporate",
                        "Requires specialized underwriting",
                        "Longer processing times",
                    ],
                ),
                DecisionOption(
                    option="Focus on secured lending",
                    impactScore=65.0 + (seed % 10),
                    riskLevel="low",
                    expectedOutcome="10-12% portfolio growth with lower NPL",
                    pros=[
                        "Lower risk profile",
                        "Easier to manage",
                        "Regulatory compliance",
                    ],
                    cons=[
                        "Lower margins",
                        "Slower growth",
                        "Limited market",
                    ],
                ),
                DecisionOption(
                    option="Digital-first lending platform",
                    impactScore=85.0 + (seed % 10),
                    riskLevel="medium",
                    expectedOutcome="25-30% increase in applications, faster processing",
                    pros=[
                        "Competitive advantage",
                        "Lower operational costs",
                        "Better customer experience",
                    ],
                    cons=[
                        "High initial investment",
                        "Technology risk",
                        "Change management required",
                    ],
                ),
            ]
        elif "digital" in question_lower or "mobile" in question_lower:
            options = [
                DecisionOption(
                    option="Launch super-app with financial services",
                    impactScore=80.0 + (seed % 15),
                    riskLevel="high",
                    expectedOutcome="40-50% increase in digital engagement",
                    pros=[
                        "Market differentiation",
                        "Revenue diversification",
                        "Customer stickiness",
                    ],
                    cons=[
                        "High development cost",
                        "Complex partnerships",
                        "Regulatory uncertainty",
                    ],
                ),
                DecisionOption(
                    option="Enhance existing mobile banking",
                    impactScore=70.0 + (seed % 10),
                    riskLevel="low",
                    expectedOutcome="20-25% improvement in user satisfaction",
                    pros=[
                        "Lower risk",
                        "Faster time to market",
                        "Builds on existing platform",
                    ],
                    cons=[
                        "Incremental improvement only",
                        "May not match competition",
                        "Limited innovation",
                    ],
                ),
            ]
        else:
            # Generic options
            options = [
                DecisionOption(
                    option="Data-driven approach",
                    impactScore=70.0 + (seed % 20),
                    riskLevel="low",
                    expectedOutcome="Informed decision with measurable outcomes",
                    pros=[
                        "Evidence-based",
                        "Lower risk",
                        "Trackable results",
                    ],
                    cons=[
                        "Requires data infrastructure",
                        "Time to gather insights",
                        "May miss qualitative factors",
                    ],
                ),
                DecisionOption(
                    option="Pilot program first",
                    impactScore=65.0 + (seed % 15),
                    riskLevel="low",
                    expectedOutcome="Validated approach before full rollout",
                    pros=[
                        "Risk mitigation",
                        "Learning opportunity",
                        "Stakeholder buy-in",
                    ],
                    cons=[
                        "Slower execution",
                        "Resource intensive",
                        "Competitor advantage",
                    ],
                ),
            ]

        analysis_map = {
            "en": f"Analysis for {bank_config.bank_name}: {request.question}. Based on current market conditions, customer behavior data, and regulatory environment, we recommend a balanced approach considering both growth and risk management.",
            "am": f"ለ{bank_config.bank_name} ትንታኔ፡ {request.question}። በአሁኑ የገበያ ሁኔታ፣ የደንበኛ ባህሪ መረጃ እና የቁጥጥር አካባቢ ላይ በመመርኮዝ ዕድገትን እና የአደጋ አስተዳደርን በማገናዘብ ሚዛናዊ አቀራረብን እንመክራለን።",
            "om": f"Xiinxala {bank_config.bank_name}f: {request.question}. Haala gabaa ammaa, daataa amala maamilaa fi naannoo to'annoo irratti hundaa'uun mala madaalawaa guddina fi bulchiinsa balaa tilmaamuun ni gorsina.",
            "ti": f"ትንታነ ንባንክ {bank_config.bank_name}: {request.question}። ኣብ ህሉው ኩነታት ዕዳጋ፣ ዳታ ባህሪ ዓማዊልን ሃዋሁው ቁጽጽርን ተመርኲስና፣ ዕብየትን ምሕደራ ሓደጋን ኣብ ግምት ብምእታው ሚዛናዊ ኣገባብ ንመኽር።",
        }

        return DecisionSupportResponse(
            question=request.question,
            analysis=analysis_map.get(language, analysis_map["en"]),
            recommendedOptions=sorted(options, key=lambda x: x.impactScore, reverse=True),
            dataSources=[
                "Internal KPI database",
                "Customer transaction history",
                "Market research reports",
                "Regulatory guidelines",
                "Industry benchmarks",
            ],
            confidence=0.75 + (seed % 20) / 100,
        )

    async def real_time_intelligence(self, bank_id: str = "dashen", *, language: str = "en") -> RealTimeIntelligenceResponse:
        """Real-time intelligence with alerts and system health monitoring."""
        bank_config = get_bank_config(bank_id)
        seed = int(hashlib.sha256(f"{bank_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H')}".encode()).hexdigest(), 16)

        alerts: list[RealTimeAlert] = []

        # Generate real-time alerts based on conditions
        if (seed % 5) == 0:
            alerts.append(
                RealTimeAlert(
                    alertId=f"alert-perf-{seed}",
                    alertType="performance",
                    severity="warning",
                    title="Transaction Volume Spike",
                    message="Transaction volume increased by 35% in the last hour",
                    metricAffected="transaction_volume",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
            )

        if (seed % 7) == 0:
            alerts.append(
                RealTimeAlert(
                    alertId=f"alert-risk-{seed}",
                    alertType="risk",
                    severity="high",
                    title="Elevated Fraud Risk",
                    message="Multiple high-risk transactions detected in the last 30 minutes",
                    metricAffected="fraud_score",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
            )

        if (seed % 3) == 0:
            alerts.append(
                RealTimeAlert(
                    alertId=f"alert-opp-{seed}",
                    alertType="opportunity",
                    severity="info",
                    title="Cross-Sell Opportunity",
                    message="250 customers eligible for premium account upgrade",
                    metricAffected="customer_lifetime_value",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
            )

        # System health
        health_score = 85 + (seed % 15)
        if health_score >= 90:
            system_health = "healthy"
        elif health_score >= 70:
            system_health = "degraded"
        else:
            system_health = "critical"

        active_trends = [
            "Digital banking adoption accelerating",
            "SME loan demand increasing",
            "Mobile transactions growing 15% MoM",
        ]

        summary_map = {
            "en": f"{bank_config.bank_name} real-time intelligence: {len(alerts)} active alerts, system health is {system_health}. {len(active_trends)} positive trends detected.",
            "am": f"{bank_config.bank_name} የእውነተኛ ጊዜ የማሰብ ችሎታ፡ {len(alerts)} ንቁ ማስጠንቀቂያዎች፣ የስርዓት ጤንነት {system_health} ነው። {len(active_trends)} አዎንታዊ አዝማሚያዎች ተገኝተዋል።",
            "om": f"Hubannoo yeroo qabatamaa {bank_config.bank_name}: Akeekkachiisa sochii {len(alerts)}, fayyaan sirna {system_health} dha. Adeemsi gaarii {len(active_trends)} argame.",
            "ti": f"ናይ ሓቂ ግዜ ብልሒ {bank_config.bank_name}: {len(alerts)} ንጡፍ ምጠንቃቕታት፣ ጥዕና ስርዓት {system_health} እዩ። {len(active_trends)} ኣወንታዊ ኣንፈታት ተረኺቦም።",
        }

        return RealTimeIntelligenceResponse(
            alerts=alerts,
            systemHealth=system_health,
            activeTrends=active_trends,
            summary=summary_map.get(language, summary_map["en"]),
        )
    
    async def process_natural_query(
        self, request: NaturalQueryRequest
    ) -> NaturalQueryResponse:
        """
        Process natural language analytics query
        
        Example queries:
        - "Show me revenue by branch in Addis Ababa for last 3 months as bar chart"
        - "Compare customer growth between Addis and Bahir Dar"
        - "What are the top 5 branches by loan disbursements?"
        """
        # Step 1: Parse the natural language query
        parsed = await query_parser.parse_query(
            request.query,
            request.language,
            request.bank_id
        )
        
        # Step 1b: Normalize group_by for yearly trends (treat "year" as monthly)
        if parsed.get("group_by") == "year":
            parsed["group_by"] = "month"
        
        # Step 1c: Override for Customer 360 questions only when not already a comparison
        query_lower = request.query.lower()
        is_comparison = parsed.get("comparison") or "between" in query_lower
        customer_keywords = ["customer", "customers", "profile", "profiles", "behavior", "behaviour", "360"]
        if not is_comparison and any(kw in query_lower for kw in customer_keywords):
            if any(kw in query_lower for kw in ["transaction", "transactions"]):
                parsed["metrics"] = ["transactions"]
                parsed["group_by"] = "month"
            elif any(kw in query_lower for kw in ["interaction", "interactions", "channel", "touchpoint"]):
                parsed["metrics"] = ["interactions"]
                parsed["group_by"] = "channel"
            else:
                parsed["metrics"] = ["customers"]
                parsed["group_by"] = "customer_segment"
        
        # Step 2: Generate data based on parsed query
        data = await self._generate_query_data(request.bank_id, parsed)
        
        # Step 3: Create chart configuration
        chart_config = self._create_chart_config(parsed, request.language)
        
        # Step 4: Generate summary and insights
        summary, insights = await self._generate_insights(
            request.query,
            parsed,
            data,
            request.language
        )
        
        # Step 5: Return response
        return NaturalQueryResponse(
            query=request.query,
            interpretation=ParsedQuery(**parsed),
            data=data,
            chartConfig=chart_config,
            summary=summary,
            insights=insights,
            sqlQuery=None  # Could add actual SQL for debugging
        )
    
    async def _generate_query_data(
        self, bank_id: str, parsed_query: dict
    ) -> list[ChartDataPoint]:
        """Generate data points based on parsed query"""
        # For demo, generate realistic data based on query parameters
        # In production, this would query the actual database
        
        bank_config = get_bank_config(bank_id)
        seed = int(hashlib.sha256(f"{bank_id}-{parsed_query.get('metrics', ['revenue'])[0]}".encode()).hexdigest(), 16)
        
        data_points = []
        
        # Generate data based on group_by
        group_by = parsed_query.get("group_by") or "month"
        
        if group_by == "branch":
            # Branch-level data
            bank_branches = bank_config.branches
            requested_branches = parsed_query.get("branches", [])

            if parsed_query.get("comparison") and len(requested_branches) > 1:
                # Comparing cities/locations directly, keep them as labels
                branches = requested_branches[:15]
            elif requested_branches:
                # If the user mentions a city like "Addis Ababa", expand to real branches
                normalized = [b.strip().lower() for b in requested_branches]
                if any(city in normalized for city in ["addis ababa", "addis", "addisabeba"]):
                    branches = bank_branches or ["Addis Ababa"]
                else:
                    branches = requested_branches
            else:
                branches = bank_branches or ["Addis Ababa", "Bahir Dar", "Mekelle", "Hawassa", "Gondar"]
            
            # Limit to top 15 to keep charts readable
            branches = branches[:15]
            
            for i, branch in enumerate(branches):
                base_value = 1000000 + (seed % 5000000)
                value = base_value * (1 + i * 0.2) * (0.8 + (_stable_hash(branch) % 40) / 100)
                
                data_points.append(ChartDataPoint(
                    label=branch,
                    value=round(value, 2),
                    metadata={"branch": branch, "rank": i + 1}
                ))
        
        elif group_by in ["date", "month", "quarter"]:
            # Time-series data
            date_range = parsed_query.get("date_range", {})
            start_date = datetime.strptime(date_range.get("start", "2024-01-01"), "%Y-%m-%d")
            end_date = datetime.strptime(date_range.get("end", "2024-12-31"), "%Y-%m-%d")
            
            # Generate monthly data points (always start on the 1st to avoid invalid day overflow)
            current_date = start_date.replace(day=1)
            month_count = 0
            
            while current_date <= end_date and month_count < 12:
                base_value = 5000000 + (seed % 10000000)
                # Add some growth trend
                growth_factor = 1 + (month_count * 0.05)
                # Add some randomness
                random_factor = 0.9 + ((_stable_hash(current_date.strftime("%Y-%m")) + seed) % 20) / 100
                value = base_value * growth_factor * random_factor
                
                data_points.append(ChartDataPoint(
                    label=current_date.strftime("%b %Y"),
                    value=round(value, 2),
                    metadata={"date": current_date.strftime("%Y-%m-%d"), "month": month_count + 1}
                ))
                
                # Move to next month
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1)
                month_count += 1
        
        elif group_by == "product":
            # Product-level data
            products = ["Savings Account", "Current Account", "Loans", "Mobile Banking", "Cards"]
            for i, product in enumerate(products):
                base_value = 2000000 + (seed % 8000000)
                value = base_value * (1 + i * 0.15) * (0.85 + (_stable_hash(product) % 30) / 100)
                
                data_points.append(ChartDataPoint(
                    label=product,
                    value=round(value, 2),
                    metadata={"product": product, "category": "banking"}
                ))
        
        elif group_by == "customer_segment":
            # Customer 360: segments/profiles
            segments = ["Active", "New", "Dormant", "VIP", "SME", "At Risk"]
            for i, segment in enumerate(segments):
                base_value = 50000 + (seed % 900000)
                value = base_value * (1 + i * 0.25) * (0.8 + (_stable_hash(segment) % 40) / 100)
                
                data_points.append(ChartDataPoint(
                    label=segment,
                    value=round(value, 2),
                    metadata={"segment": segment, "category": "customer"}
                ))
        
        elif group_by == "channel":
            # Customer 360: interaction channels
            channels = ["Mobile App", "Branch", "Call Center", "ATM", "Web", "USSD"]
            for i, channel in enumerate(channels):
                base_value = 10000 + (seed % 500000)
                value = base_value * (1 + i * 0.2) * (0.8 + (_stable_hash(channel) % 40) / 100)
                
                data_points.append(ChartDataPoint(
                    label=channel,
                    value=round(value, 2),
                    metadata={"channel": channel, "category": "interaction"}
                ))
        
        # Apply top_n filter if specified
        top_n = parsed_query.get("top_n")
        if top_n and len(data_points) > top_n:
            # Sort by value descending and take top N
            data_points.sort(key=lambda x: x.value, reverse=True)
            data_points = data_points[:top_n]
        
        return data_points
    
    def _create_chart_config(self, parsed_query: dict, language: str) -> ChartConfig:
        """Create chart configuration based on parsed query"""
        chart_type = parsed_query.get("chart_type", "bar")
        metrics = parsed_query.get("metrics", ["revenue"])
        group_by = parsed_query.get("group_by") or "month"
        if parsed_query.get("comparison"):
            group_by = "city"
        
        # Metric labels
        metric_labels = {
            "en": {
                "revenue": "Revenue",
                "customers": "Customers",
                "transactions": "Transactions",
                "loans": "Loans",
                "deposits": "Deposits",
                "interactions": "Interactions"
            },
            "am": {
                "revenue": "ገቢ",
                "customers": "ደንበኞች",
                "transactions": "ግብይቶች",
                "loans": "ብድር",
                "deposits": "ተቀማጭ",
                "interactions": "ግንኙነቶች"
            },
            "om": {
                "revenue": "Gatii",
                "customers": "Maamila",
                "transactions": "Tamsa'onni",
                "loans": "Kaffaltiiwwan",
                "deposits": "Qarshiiwwan Seffaman",
                "interactions": "Mariiwwan"
            }
        }
        
        # Group by labels
        groupby_labels = {
            "en": {
                "branch": "Branch",
                "month": "Month",
                "product": "Product",
                "date": "Date",
                "city": "City",
                "customer_segment": "Customer Segment",
                "channel": "Channel",
            },
            "am": {
                "branch": "ቅርንጫፍ",
                "month": "ወር",
                "product": "ምርት",
                "date": "ቀን",
                "city": "ከተማ",
                "customer_segment": "የደንበኛ ክፍል",
                "channel": "ሰርጥ",
            },
            "om": {
                "branch": "Daldaloota",
                "month": "Ji'a",
                "product": "Oomishoota",
                "date": "Guyyaa",
                "city": "Magaalota",
                "customer_segment": "Kuta Maamilaa",
                "channel": "Karaa",
            }
        }
        
        lang_metrics = metric_labels.get(language, metric_labels["en"])
        lang_groupby = groupby_labels.get(language, groupby_labels["en"])

        metric_label = lang_metrics.get(metrics[0], metrics[0].title())
        groupby_label = lang_groupby.get(group_by, group_by.title())

        title_templates = {
            "en": f"{metric_label} by {groupby_label}",
            "am": f"{metric_label} በ{groupby_label}",
            "om": f"{metric_label} {groupby_label}",
            "ti": f"{metric_label} by {groupby_label}",
            "so": f"{metric_label} by {groupby_label}",
        }
        title = title_templates.get(language, title_templates["en"])

        return ChartConfig(
            type=chart_type,
            title=title,
            xAxisLabel=groupby_label,
            yAxisLabel=metric_label,
            showLegend=True,
            showGrid=True,
            colors=None  # Will use bank's theme colors
        )
    
    async def _generate_insights(
        self, query: str, parsed_query: dict, data: list[ChartDataPoint], language: str
    ) -> tuple[str, list[str]]:
        """Generate natural language summary and insights"""
        from app.modules.shared.llm_assistant import llm_assistant
        
        # Calculate basic statistics
        if not data:
            return ("No data available for this query.", [])
        
        values = [d.value for d in data]
        total = sum(values)
        avg = total / len(values) if values else 0
        max_point = max(data, key=lambda x: x.value)
        min_point = min(data, key=lambda x: x.value)
        
        # Create summary prompt
        prompt = f"""
Based on this analytics query and data, provide a brief summary and 3 key insights.

Query: "{query}"
Metrics: {parsed_query.get('metrics')}
Group by: {parsed_query.get('group_by')}
Data points: {len(data)}
Total: {total:,.2f}
Average: {avg:,.2f}
Highest: {max_point.label} ({max_point.value:,.2f})
Lowest: {min_point.label} ({min_point.value:,.2f})

Provide response in {language} language.

Format:
Summary: [One sentence summary]
Insights:
1. [First insight]
2. [Second insight]
3. [Third insight]
"""
        
        try:
            dummy_session = Session(id="maya-insights")
            result = await llm_assistant.generate_reply(
                session=dummy_session, language=language, message=prompt
            )
            response = result.get("reply", "")
            
            # Parse response
            lines = response.strip().split('\n')
            summary = ""
            insights = []
            
            for line in lines:
                if line.startswith("Summary:"):
                    summary = line.replace("Summary:", "").strip()
                elif line.strip() and (line[0].isdigit() or line.startswith("-")):
                    insight = line.strip().lstrip("0123456789.-) ")
                    if insight:
                        insights.append(insight)
            
            if not summary:
                summary = f"Analysis of {parsed_query.get('metrics', ['data'])[0]} across {len(data)} {parsed_query.get('group_by', 'items')}."
            
            if not insights:
                insights = _build_insights(data, max_point, min_point, avg, total, parsed_query)
            
            return (summary, insights[:3])
            
        except Exception as e:
            print(f"Error generating insights: {e}")
            # Fallback to basic summary
            summary = f"Analysis of {parsed_query.get('metrics', ['data'])[0]} showing {len(data)} results."
            insights = _build_insights(data, max_point, min_point, avg, total, parsed_query)
            return (summary, insights)
    
    async def analyze_branch_performance(
        self, bank_id: str, language: str = "en"
    ) -> BranchAnalysisResponse:
        """
        Comprehensive branch performance analysis with:
        - Top and bottom performers
        - Detailed analysis of worst performer
        - Predictive insights (3m, 6m, 12m forecasts)
        - Prescriptive recommendations (quick wins + strategic)
        """
        from app.modules.shared.llm_assistant import llm_assistant
        
        bank_config = get_bank_config(bank_id)
        seed = int(hashlib.sha256(f"{bank_id}-branches".encode()).hexdigest(), 16)
        
        # Generate branch data for Ethiopian cities
        ethiopian_cities = [
            ("Addis Ababa", "Addis Ababa", "Central"),
            ("Bahir Dar", "Bahir Dar", "Amhara"),
            ("Mekelle", "Mekelle", "Tigray"),
            ("Hawassa", "Hawassa", "SNNPR"),
            ("Gondar", "Gondar", "Amhara"),
            ("Dire Dawa", "Dire Dawa", "Dire Dawa"),
            ("Adama", "Adama", "Oromia"),
            ("Jimma", "Jimma", "Oromia"),
            ("Dessie", "Dessie", "Amhara"),
            ("Shashamane", "Shashamane", "Oromia"),
            ("Arba Minch", "Arba Minch", "SNNPR"),
            ("Harar", "Harar", "Harari"),
        ]
        
        branches = []
        for idx, (city, branch_name, region) in enumerate(ethiopian_cities):
            # Generate deterministic but varied metrics
            city_seed = seed + _stable_hash(city)
            
            revenue = 1_000_000 + (city_seed % 5_000_000) * (0.5 + idx * 0.1)
            customers = 5_000 + (city_seed % 20_000)
            transactions = customers * (50 + (city_seed % 100))
            loans = revenue * (0.6 + (city_seed % 40) / 100)
            deposits = revenue * (1.2 + (city_seed % 50) / 100)
            satisfaction = 60 + (city_seed % 35)
            digital = 40 + (city_seed % 50)
            
            # Calculate performance score (weighted average)
            perf_score = (
                (revenue / 6_000_000) * 30 +  # 30% weight
                (customers / 25_000) * 20 +    # 20% weight
                (satisfaction / 100) * 25 +     # 25% weight
                (digital / 100) * 15 +          # 15% weight
                (loans / 3_000_000) * 10        # 10% weight
            )
            
            branches.append(BranchMetrics(
                branchId=f"{bank_id}_{city.lower().replace(' ', '_')}",
                branchName=f"{branch_name} Branch",
                city=city,
                region=region,
                revenue=round(revenue, 2),
                customers=customers,
                transactions=transactions,
                loansDisbursed=round(loans, 2),
                deposits=round(deposits, 2),
                customerSatisfaction=round(satisfaction, 1),
                digitalAdoption=round(digital, 1),
                performanceScore=round(perf_score, 2),
                rank=0  # Will be set after sorting
            ))
        
        # Sort by performance score and assign ranks
        branches.sort(key=lambda x: x.performance_score, reverse=True)
        for idx, branch in enumerate(branches):
            branch.rank = idx + 1
        
        # Get top 5 and bottom 5
        top_performers = branches[:5]
        bottom_performers = branches[-5:]
        worst_branch = branches[-1]
        
        # Calculate average metrics for comparison
        avg_revenue = sum(b.revenue for b in branches) / len(branches)
        avg_customers = sum(b.customers for b in branches) / len(branches)
        avg_satisfaction = sum(b.customer_satisfaction for b in branches) / len(branches)
        avg_digital = sum(b.digital_adoption for b in branches) / len(branches)
        avg_loans = sum(b.loans_disbursed for b in branches) / len(branches)
        
        # Identify improvement areas for worst branch
        improvement_areas = []
        
        # Revenue gap
        if worst_branch.revenue < avg_revenue * 0.7:
            revenue_gap = ((avg_revenue - worst_branch.revenue) / avg_revenue) * 100
            improvement_areas.append(ImprovementArea(
                area="Revenue Generation",
                currentValue=worst_branch.revenue,
                targetValue=avg_revenue,
                gapPercentage=round(revenue_gap, 1),
                priority="high",
                recommendedActions=[
                    "Launch targeted marketing campaigns in the local area",
                    "Introduce promotional offers for new account openings",
                    "Partner with local businesses for corporate banking",
                    "Increase cross-selling of banking products"
                ]
            ))
        
        # Customer acquisition gap
        if worst_branch.customers < avg_customers * 0.7:
            customer_gap = ((avg_customers - worst_branch.customers) / avg_customers) * 100
            improvement_areas.append(ImprovementArea(
                area="Customer Acquisition",
                currentValue=float(worst_branch.customers),
                targetValue=avg_customers,
                gapPercentage=round(customer_gap, 1),
                priority="high",
                recommendedActions=[
                    "Conduct community outreach programs",
                    "Offer referral bonuses to existing customers",
                    "Improve branch visibility and signage",
                    "Host financial literacy workshops"
                ]
            ))
        
        # Customer satisfaction gap
        if worst_branch.customer_satisfaction < avg_satisfaction - 10:
            satisfaction_gap = ((avg_satisfaction - worst_branch.customer_satisfaction) / avg_satisfaction) * 100
            improvement_areas.append(ImprovementArea(
                area="Customer Satisfaction",
                currentValue=worst_branch.customer_satisfaction,
                targetValue=avg_satisfaction,
                gapPercentage=round(satisfaction_gap, 1),
                priority="high",
                recommendedActions=[
                    "Implement staff training on customer service excellence",
                    "Reduce wait times through better queue management",
                    "Gather and act on customer feedback regularly",
                    "Upgrade branch facilities and ambiance"
                ]
            ))
        
        # Digital adoption gap
        if worst_branch.digital_adoption < avg_digital - 15:
            digital_gap = ((avg_digital - worst_branch.digital_adoption) / avg_digital) * 100
            improvement_areas.append(ImprovementArea(
                area="Digital Banking Adoption",
                currentValue=worst_branch.digital_adoption,
                targetValue=avg_digital,
                gapPercentage=round(digital_gap, 1),
                priority="medium",
                recommendedActions=[
                    "Conduct mobile banking training sessions for customers",
                    "Offer incentives for using digital channels",
                    "Deploy digital banking ambassadors in the branch",
                    "Improve internet connectivity in the branch"
                ]
            ))
        
        # Loan disbursement gap
        if worst_branch.loans_disbursed < avg_loans * 0.6:
            loan_gap = ((avg_loans - worst_branch.loans_disbursed) / avg_loans) * 100
            improvement_areas.append(ImprovementArea(
                area="Loan Disbursement",
                currentValue=worst_branch.loans_disbursed,
                targetValue=avg_loans,
                gapPercentage=round(loan_gap, 1),
                priority="medium",
                recommendedActions=[
                    "Simplify loan application processes",
                    "Offer competitive interest rates for local businesses",
                    "Create specialized loan products for the region",
                    "Increase loan officer capacity and training"
                ]
            ))
        
        # Generate predictions for worst branch (3m, 6m, 12m)
        predictions = []
        
        # Revenue prediction
        current_revenue = worst_branch.revenue
        # Assume 5% quarterly growth if improvements are implemented
        predictions.append(BranchPrediction(
            metric="Revenue",
            currentValue=current_revenue,
            predictedValue3m=round(current_revenue * 1.05, 2),
            predictedValue6m=round(current_revenue * 1.10, 2),
            predictedValue12m=round(current_revenue * 1.22, 2),
            trend="improving",
            confidence=0.75
        ))
        
        # Customer growth prediction
        current_customers = float(worst_branch.customers)
        predictions.append(BranchPrediction(
            metric="Customers",
            currentValue=current_customers,
            predictedValue3m=round(current_customers * 1.08, 2),
            predictedValue6m=round(current_customers * 1.15, 2),
            predictedValue12m=round(current_customers * 1.30, 2),
            trend="improving",
            confidence=0.80
        ))
        
        # Customer satisfaction prediction
        current_satisfaction = worst_branch.customer_satisfaction
        predictions.append(BranchPrediction(
            metric="Customer Satisfaction",
            currentValue=current_satisfaction,
            predictedValue3m=round(min(current_satisfaction + 5, 95), 1),
            predictedValue6m=round(min(current_satisfaction + 10, 95), 1),
            predictedValue12m=round(min(current_satisfaction + 18, 95), 1),
            trend="improving",
            confidence=0.70
        ))
        
        # Digital adoption prediction
        current_digital = worst_branch.digital_adoption
        predictions.append(BranchPrediction(
            metric="Digital Adoption",
            currentValue=current_digital,
            predictedValue3m=round(min(current_digital + 8, 90), 1),
            predictedValue6m=round(min(current_digital + 15, 90), 1),
            predictedValue12m=round(min(current_digital + 25, 90), 1),
            trend="improving",
            confidence=0.85
        ))
        
        # Generate quick wins (immediate impact, low effort)
        quick_wins = [
            f"Deploy 2 additional staff to {worst_branch.branch_name} during peak hours to reduce wait times",
            "Launch a 30-day promotional campaign offering fee waivers for new account openings",
            "Install digital signage in the branch to promote mobile banking features",
            "Organize a weekend financial literacy event to attract new customers",
            "Implement a customer feedback kiosk to identify and address pain points quickly"
        ]
        
        # Generate strategic initiatives (long-term, high impact)
        strategic_initiatives = [
            f"Renovate {worst_branch.branch_name} to create a modern, welcoming environment",
            "Establish partnerships with 5-10 local businesses for corporate banking relationships",
            "Deploy a dedicated relationship manager for high-value customers in the area",
            "Create region-specific loan products tailored to local economic activities",
            "Implement a comprehensive staff development program focused on sales and service",
            "Install ATMs in 3 strategic locations around the city to increase accessibility"
        ]
        
        # Generate executive summary using AI
        summary_prompt = f"""
Generate a concise executive summary for branch performance analysis.

Bank: {bank_config.bank_name}
Total Branches: {len(branches)}
Best Performer: {top_performers[0].branch_name} (Score: {top_performers[0].performance_score:.1f})
Worst Performer: {worst_branch.branch_name} (Score: {worst_branch.performance_score:.1f})
Performance Gap: {top_performers[0].performance_score - worst_branch.performance_score:.1f} points

Key Issues in {worst_branch.branch_name}:
{', '.join([area.area for area in improvement_areas[:3]])}

Language: {language}

Provide a 2-3 sentence executive summary highlighting the performance gap and opportunity for improvement.
"""
        
        try:
            dummy_session = Session(id="maya-branch-summary")
            result = await llm_assistant.generate_reply(
                session=dummy_session, language=language, message=summary_prompt
            )
            executive_summary = result.get("reply", "").strip()
        except Exception:
            executive_summary = f"{worst_branch.branch_name} ranks last among {len(branches)} branches with significant gaps in {', '.join([area.area for area in improvement_areas[:2]])}. With targeted interventions, the branch can improve performance by 20-30% within 12 months."
        
        # Generate key insights
        key_insights = [
            f"{top_performers[0].branch_name} leads with a performance score of {top_performers[0].performance_score:.1f}, {((top_performers[0].performance_score - worst_branch.performance_score) / worst_branch.performance_score * 100):.0f}% higher than the lowest performer",
            f"{worst_branch.branch_name} has the greatest improvement potential, particularly in {improvement_areas[0].area if improvement_areas else 'customer service'}",
            f"Implementing recommended actions could increase {worst_branch.branch_name} revenue by {((predictions[0].predicted_value_12m - predictions[0].current_value) / predictions[0].current_value * 100):.0f}% within 12 months",
            f"Top 5 branches generate {sum(b.revenue for b in top_performers) / sum(b.revenue for b in branches) * 100:.0f}% of total revenue across {len(branches)} branches",
            f"Average customer satisfaction gap between top and bottom performers is {top_performers[0].customer_satisfaction - worst_branch.customer_satisfaction:.1f} points"
        ]
        
        return BranchAnalysisResponse(
            bankId=bank_id,
            analysisDate=datetime.now(timezone.utc).isoformat(),
            totalBranches=len(branches),
            topPerformers=top_performers,
            bottomPerformers=bottom_performers,
            worstBranch=worst_branch,
            improvementAreas=improvement_areas,
            predictions=predictions,
            quickWins=quick_wins,
            strategicInitiatives=strategic_initiatives,
            executiveSummary=executive_summary,
            keyInsights=key_insights
        )
