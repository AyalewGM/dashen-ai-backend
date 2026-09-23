from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class UnifiedDashboardRequest(BaseModel):
    bank_id: str = Field(default="dashen", alias="bankId")
    time_range: str = Field(default="30d", alias="timeRange")  # 7d, 30d, 90d, 1y

    class Config:
        populate_by_name = True


class KpiCard(BaseModel):
    title: str
    value: str
    delta: str
    change: str  # duplicate used by some frontend components
    trend: str  # up, down, flat
    severity: str  # success, warning, danger, info


class PerformanceMetric(BaseModel):
    metric_name: str = Field(..., alias="metricName")
    current_value: float = Field(..., alias="currentValue")
    previous_value: float = Field(..., alias="previousValue")
    change_percent: float = Field(..., alias="changePercent")
    trend: str

    class Config:
        populate_by_name = True


class TrendPoint(BaseModel):
    date: str
    value: float


class PerformanceMetrics(BaseModel):
    revenue_trend: list[TrendPoint] = Field(..., alias="revenueTrend")
    customer_growth: list[TrendPoint] = Field(..., alias="customerGrowth")
    transaction_volume: list[TrendPoint] = Field(..., alias="transactionVolume")
    loan_portfolio: list[TrendPoint] = Field(..., alias="loanPortfolio")

    class Config:
        populate_by_name = True


class UnifiedDashboardResponse(BaseModel):
    kpi_cards: list[KpiCard] = Field(..., alias="kpiCards")
    performance_metrics: PerformanceMetrics = Field(..., alias="performanceMetrics")
    insight_narrative: str = Field(..., alias="insightNarrative")
    recommendations: list[str]
    last_updated: str = Field(..., alias="lastUpdated")

    class Config:
        populate_by_name = True


class PredictiveRequest(BaseModel):
    metric_name: str = Field(..., alias="metricName")
    horizon_days: int = Field(default=30, alias="horizonDays")
    bank_id: str = Field(default="dashen", alias="bankId")

    class Config:
        populate_by_name = True


class ForecastPoint(BaseModel):
    date: str
    predicted_value: float = Field(..., alias="predictedValue")
    lower_bound: float = Field(..., alias="lowerBound")
    upper_bound: float = Field(..., alias="upperBound")
    confidence: float

    class Config:
        populate_by_name = True


class PredictiveResponse(BaseModel):
    metric_name: str = Field(..., alias="metricName")
    forecast: list[ForecastPoint]
    trend_direction: str = Field(..., alias="trendDirection")  # increasing, decreasing, stable
    confidence_level: float = Field(..., alias="confidenceLevel")
    narrative: str
    risk_factors: list[str] = Field(..., alias="riskFactors")
    opportunities: list[str]

    class Config:
        populate_by_name = True


class DecisionSupportRequest(BaseModel):
    question: str
    context: Optional[dict] = None
    bank_id: str = Field(default="dashen", alias="bankId")

    class Config:
        populate_by_name = True


class DecisionOption(BaseModel):
    option: str
    impact_score: float = Field(..., alias="impactScore")  # 0-100
    risk_level: str = Field(..., alias="riskLevel")  # low, medium, high
    expected_outcome: str = Field(..., alias="expectedOutcome")
    pros: list[str]
    cons: list[str]

    class Config:
        populate_by_name = True


class DecisionSupportResponse(BaseModel):
    question: str
    analysis: str
    recommended_options: list[DecisionOption] = Field(..., alias="recommendedOptions")
    data_sources: list[str] = Field(..., alias="dataSources")
    confidence: float

    class Config:
        populate_by_name = True


class RealTimeAlert(BaseModel):
    alert_id: str = Field(..., alias="alertId")
    alert_type: str = Field(..., alias="alertType")  # performance, risk, opportunity
    severity: str
    title: str
    message: str
    metric_affected: str = Field(..., alias="metricAffected")
    timestamp: str

    class Config:
        populate_by_name = True


class RealTimeIntelligenceResponse(BaseModel):
    alerts: list[RealTimeAlert]
    system_health: str = Field(..., alias="systemHealth")  # healthy, degraded, critical
    active_trends: list[str] = Field(..., alias="activeTrends")
    summary: str

    class Config:
        populate_by_name = True


# Natural Language Query Models
class NaturalQueryRequest(BaseModel):
    """Request for natural language analytics query"""
    query: str = Field(..., description="Natural language question")
    bank_id: str = Field(default="dashen", alias="bankId")
    language: str = Field(default="en", description="User's language")

    class Config:
        populate_by_name = True


class ParsedQuery(BaseModel):
    """Structured representation of parsed query"""
    original_query: str = Field(..., alias="originalQuery")
    language: str
    metrics: list[str] = Field(default_factory=list, description="Metrics to analyze")
    chart_type: Optional[str] = Field(None, alias="chartType", description="Visualization type")
    date_range: Optional[dict] = Field(None, alias="dateRange")
    branches: list[str] = Field(default_factory=list, description="Branch filters")
    group_by: Optional[str] = Field(None, alias="groupBy", description="Grouping dimension")
    aggregation: str = Field(default="sum", description="Aggregation function")
    filters: dict = Field(default_factory=dict, description="Additional filters")
    comparison: bool = Field(default=False, description="Is this a comparison query?")
    top_n: Optional[int] = Field(None, alias="topN", description="Limit to top N results")

    class Config:
        populate_by_name = True


class ChartDataPoint(BaseModel):
    """Single data point in a chart"""
    label: str
    value: float
    metadata: Optional[dict] = None


class ChartConfig(BaseModel):
    """Configuration for chart rendering"""
    type: str = Field(..., description="Chart type: bar, line, pie, table, area")
    title: str
    x_axis_label: Optional[str] = Field(None, alias="xAxisLabel")
    y_axis_label: Optional[str] = Field(None, alias="yAxisLabel")
    show_legend: bool = Field(default=True, alias="showLegend")
    show_grid: bool = Field(default=True, alias="showGrid")
    colors: Optional[list[str]] = None

    class Config:
        populate_by_name = True


class NaturalQueryResponse(BaseModel):
    """Response for natural language query"""
    query: str = Field(..., description="Original query")
    interpretation: ParsedQuery = Field(..., description="How the query was interpreted")
    data: list[ChartDataPoint] = Field(..., description="Chart data points")
    chart_config: ChartConfig = Field(..., alias="chartConfig")
    summary: str = Field(..., description="Natural language summary of results")
    insights: list[str] = Field(default_factory=list, description="AI-generated insights")
    sql_query: Optional[str] = Field(None, alias="sqlQuery", description="Generated SQL (for debugging)")

    class Config:
        populate_by_name = True


# Branch Performance Analysis Models
class BranchMetrics(BaseModel):
    """Performance metrics for a single branch"""
    branch_id: str = Field(..., alias="branchId")
    branch_name: str = Field(..., alias="branchName")
    city: str
    region: str
    revenue: float
    customers: int
    transactions: int
    loans_disbursed: float = Field(..., alias="loansDisbursed")
    deposits: float
    customer_satisfaction: float = Field(..., alias="customerSatisfaction")
    digital_adoption: float = Field(..., alias="digitalAdoption")
    performance_score: float = Field(..., alias="performanceScore")
    rank: int

    class Config:
        populate_by_name = True


class ImprovementArea(BaseModel):
    """Specific area for improvement"""
    area: str
    current_value: float = Field(..., alias="currentValue")
    target_value: float = Field(..., alias="targetValue")
    gap_percentage: float = Field(..., alias="gapPercentage")
    priority: str  # high, medium, low
    recommended_actions: list[str] = Field(..., alias="recommendedActions")

    class Config:
        populate_by_name = True


class BranchPrediction(BaseModel):
    """Predictive insights for branch performance"""
    metric: str
    current_value: float = Field(..., alias="currentValue")
    predicted_value_3m: float = Field(..., alias="predictedValue3m")
    predicted_value_6m: float = Field(..., alias="predictedValue6m")
    predicted_value_12m: float = Field(..., alias="predictedValue12m")
    trend: str  # improving, declining, stable
    confidence: float

    class Config:
        populate_by_name = True


class BranchAnalysisResponse(BaseModel):
    """Comprehensive branch performance analysis"""
    bank_id: str = Field(..., alias="bankId")
    analysis_date: str = Field(..., alias="analysisDate")
    total_branches: int = Field(..., alias="totalBranches")
    
    # Top and bottom performers
    top_performers: list[BranchMetrics] = Field(..., alias="topPerformers")
    bottom_performers: list[BranchMetrics] = Field(..., alias="bottomPerformers")
    
    # Detailed analysis for worst performer
    worst_branch: BranchMetrics = Field(..., alias="worstBranch")
    improvement_areas: list[ImprovementArea] = Field(..., alias="improvementAreas")
    predictions: list[BranchPrediction]
    
    # Prescriptive recommendations
    quick_wins: list[str] = Field(..., alias="quickWins", description="Actions with immediate impact")
    strategic_initiatives: list[str] = Field(..., alias="strategicInitiatives", description="Long-term improvements")
    
    # Summary
    executive_summary: str = Field(..., alias="executiveSummary")
    key_insights: list[str] = Field(..., alias="keyInsights")

    class Config:
        populate_by_name = True
