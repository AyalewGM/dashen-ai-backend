from __future__ import annotations

import hashlib
import time
from datetime import date
from typing import Optional

from .models import ChartData, InternalKpisResponse, InternalQueryRequest, InternalQueryResponse, Series
from .queries import fetch_latest_scalar_metric, fetch_metric_series, fetch_metric_trend, has_db


class InternalInsightsService:
    def get_kpis(self, *, language: str) -> InternalKpisResponse:
        # Prefer DB-backed values; fall back to stable stub values.
        deposits = fetch_metric_trend("deposits", limit=4) if has_db() else []
        loans = fetch_metric_trend("loans", limit=4) if has_db() else []

        if not deposits:
            deposits = [100.0, 103.0, 106.5, 110.2]
        if not loans:
            loans = [80.0, 81.5, 83.0, 85.0]

        npl_proxy = fetch_latest_scalar_metric("npl_proxy") if has_db() else None
        digital_adoption = fetch_latest_scalar_metric("digital_adoption") if has_db() else None

        return InternalKpisResponse(
            depositsTrend=deposits,
            loansTrend=loans,
            nplProxy=float(npl_proxy) if npl_proxy is not None else 2.4,
            digitalAdoption=float(digital_adoption) if digital_adoption is not None else 0.62,
            fraudAlertsSummary={"open": 12, "critical": 2},
            supportVolume={"tickets": 340, "avgHandleTimeSec": 290},
        )

    def query(self, request: InternalQueryRequest, *, language: str) -> InternalQueryResponse:
        start_t = time.monotonic()

        labels: list[str]
        data: list[float]

        if has_db():
            try:
                start = date.fromisoformat(request.time_range.start)
                end = date.fromisoformat(request.time_range.end)
            except Exception:
                start = date.today().replace(day=1)
                end = date.today()

            segment_type = None
            segment_value = None
            if request.segment and isinstance(request.segment, dict):
                segment_type = request.segment.get("type")
                segment_value = request.segment.get("value")

            labels, data = fetch_metric_series(
                request.metric_name,
                start=start,
                end=end,
                segment_type=segment_type,
                segment_value=segment_value,
            )
        else:
            labels, data = ([], [])

        if not labels:
            # Deterministic pseudo-data based on metricName
            seed = int(hashlib.sha256(request.metric_name.encode("utf-8")).hexdigest(), 16) % 1000
            labels = ["W1", "W2", "W3", "W4"]
            base = (seed % 50) + 50
            data = [float(base), float(base + 2), float(base + 1), float(base + 3)]

        summary_map = {
            "en": f"Showing {request.metric_name} for the selected time range.",
            "am": f"ለተመረጠው የጊዜ ክልል {request.metric_name} እየታየ ነው።",
            "om": f"Yeroo filatameef {request.metric_name} agarsiisaa jira.",
            "ti": f"ንተመረጸ ናይ ግዜ ክልል {request.metric_name} የርኢ ኣሎ።",
        }

        latency_ms = int((time.monotonic() - start_t) * 1000)
        return InternalQueryResponse(
            chartData=ChartData(labels=labels, series=[Series(name=request.metric_name, data=data)]),
            narrativeSummary=summary_map.get(language, summary_map["en"]),
            metadata={"latencyMs": latency_ms},
        )
