from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class TimeRange(BaseModel):
    start: str
    end: str


class CategoryAmount(BaseModel):
    category: str
    amount: float


class CustomerInsightsSummaryResponse(BaseModel):
    month_spend: float = Field(..., alias="monthSpend")
    month_income: float = Field(..., alias="monthIncome")
    net_savings: float = Field(..., alias="netSavings")
    top_categories: list[CategoryAmount] = Field(..., alias="topCategories")
    bills_this_month: dict[str, float] = Field(..., alias="billsThisMonth")

    class Config:
        populate_by_name = True


CustomerIntent = Literal["SPENDING_TREND", "BILLS_SUMMARY", "SAVINGS_ADVICE", "CATEGORY_BREAKDOWN"]


class CustomerInsightsQueryRequest(BaseModel):
    # Either structured intent OR free-text question may be provided.
    intent: Optional[CustomerIntent] = None
    question: Optional[str] = None

    time_range: Optional[TimeRange] = Field(default=None, alias="timeRange")
    filters: Optional[dict[str, Any]] = None
    language: Optional[str] = Field(default=None, pattern="^(am|om|ti|en)$")

    # Sent by client but must be ignored; included to allow tests to prove it.
    customer_id: Optional[str] = Field(default=None, alias="customerId")

    class Config:
        populate_by_name = True


class Series(BaseModel):
    name: str
    data: list[float]


class ChartData(BaseModel):
    labels: list[str]
    series: list[Series]


class CustomerInsightsQueryResponse(BaseModel):
    answer_text: str = Field(..., alias="answerText")
    chart_data: Optional[ChartData] = Field(default=None, alias="chartData")
    table_data: Optional[list[dict[str, Any]]] = Field(default=None, alias="tableData")
    metadata: dict[str, Any]

    class Config:
        populate_by_name = True
