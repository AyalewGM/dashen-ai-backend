from __future__ import annotations

from datetime import date
from typing import Optional

from app.modules.shared.db import get_database_url, get_db_conn


def has_db() -> bool:
    return bool(get_database_url())


def fetch_latest_scalar_metric(metric_name: str) -> Optional[float]:
    if not has_db():
        return None

    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT metric_value
                FROM internal_kpis
                WHERE metric_name = %s
                ORDER BY kpi_date DESC
                LIMIT 1
                """,
                (metric_name,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return float(row[0])


def fetch_metric_trend(metric_name: str, *, limit: int = 4) -> list[float]:
    if not has_db():
        return []

    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT kpi_date, metric_value
                FROM internal_kpis
                WHERE metric_name = %s
                  AND segment_type IS NULL
                  AND segment_value IS NULL
                ORDER BY kpi_date DESC
                LIMIT %s
                """,
                (metric_name, limit),
            )
            rows = cur.fetchall() or []

    return [float(v) for _, v in reversed(rows)]


def fetch_metric_series(
    metric_name: str,
    *,
    start: date,
    end: date,
    segment_type: Optional[str] = None,
    segment_value: Optional[str] = None,
) -> tuple[list[str], list[float]]:
    if not has_db():
        return ([], [])

    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT kpi_date, metric_value
                FROM internal_kpis
                WHERE metric_name = %s
                  AND kpi_date >= %s
                  AND kpi_date <= %s
                  AND (%s IS NULL OR segment_type = %s)
                  AND (%s IS NULL OR segment_value = %s)
                ORDER BY kpi_date ASC
                """,
                (metric_name, start, end, segment_type, segment_type, segment_value, segment_value),
            )
            rows = cur.fetchall() or []

    labels = [str(d) for d, _ in rows]
    data = [float(v) for _, v in rows]
    return labels, data
