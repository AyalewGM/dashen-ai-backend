from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class InternalKpisResponse(BaseModel):
    deposits_trend: list[float] = Field(..., alias="depositsTrend")
    loans_trend: list[float] = Field(..., alias="loansTrend")
    npl_proxy: float = Field(..., alias="nplProxy")
    digital_adoption: float = Field(..., alias="digitalAdoption")
    fraud_alerts_summary: dict = Field(..., alias="fraudAlertsSummary")
    support_volume: dict = Field(..., alias="supportVolume")

    class Config:
        populate_by_name = True


class TimeRange(BaseModel):
    start: str
    end: str


SegmentType = Literal["region", "product", "channel"]


class InternalQueryRequest(BaseModel):
    metric_name: str = Field(..., alias="metricName")
    time_range: TimeRange = Field(..., alias="timeRange")
    segment: Optional[dict] = None

    class Config:
        populate_by_name = True


class Series(BaseModel):
    name: str
    data: list[float]


class ChartData(BaseModel):
    labels: list[str]
    series: list[Series]


class InternalQueryResponse(BaseModel):
    chart_data: ChartData = Field(..., alias="chartData")
    narrative_summary: Optional[str] = Field(default=None, alias="narrativeSummary")
    metadata: dict = Field(default_factory=dict)

    class Config:
        populate_by_name = True
