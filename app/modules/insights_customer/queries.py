from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.modules.shared.db import get_database_url, get_db_conn


def has_db() -> bool:
    return bool(get_database_url())


def month_summary(customer_id: str) -> tuple[float, float]:
    if not has_db():
        return (0.0, 0.0)

    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                  COALESCE(SUM(CASE WHEN direction = 'debit' THEN amount ELSE 0 END), 0) AS spend,
                  COALESCE(SUM(CASE WHEN direction = 'credit' THEN amount ELSE 0 END), 0) AS income
                FROM transactions
                WHERE customer_id = %s
                  AND date_trunc('month', tx_timestamp) = date_trunc('month', NOW())
                """,
                (customer_id,),
            )
            row = cur.fetchone() or (0, 0)
            return float(row[0]), float(row[1])


def top_categories(customer_id: str, *, limit: int = 5) -> list[tuple[str, float]]:
    if not has_db():
        return []

    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COALESCE(category, 'unknown') AS category, SUM(amount) AS total
                FROM transactions
                WHERE customer_id = %s
                  AND direction = 'debit'
                  AND date_trunc('month', tx_timestamp) = date_trunc('month', NOW())
                GROUP BY COALESCE(category, 'unknown')
                ORDER BY total DESC
                LIMIT %s
                """,
                (customer_id, limit),
            )
            return [(str(c), float(t)) for c, t in (cur.fetchall() or [])]


def bills_breakdown(customer_id: str) -> dict[str, float]:
    if not has_db():
        return {"water": 0.0, "electricity": 0.0, "telecom": 0.0}

    bills = {"water": 0.0, "electricity": 0.0, "telecom": 0.0}
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT LOWER(COALESCE(subcategory, '')) AS subcat, SUM(amount) AS total
                FROM transactions
                WHERE customer_id = %s
                  AND direction = 'debit'
                  AND COALESCE(category,'') = 'utilities'
                  AND date_trunc('month', tx_timestamp) = date_trunc('month', NOW())
                GROUP BY LOWER(COALESCE(subcategory, ''))
                """,
                (customer_id,),
            )
            for subcat, total in cur.fetchall() or []:
                if subcat in bills:
                    bills[subcat] = float(total)

    return bills


def weekly_spend_series(customer_id: str, *, start: str, end: str) -> tuple[list[str], list[float]]:
    if not has_db():
        return ([], [])

    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT date_trunc('week', tx_timestamp) AS wk, SUM(amount) AS total
                FROM transactions
                WHERE customer_id = %s
                  AND direction = 'debit'
                  AND tx_timestamp >= %s
                  AND tx_timestamp <= %s
                GROUP BY date_trunc('week', tx_timestamp)
                ORDER BY wk ASC
                """,
                (customer_id, start, end),
            )
            rows = cur.fetchall() or []

    labels = [wk.strftime("%Y-%m-%d") if isinstance(wk, datetime) else str(wk) for wk, _ in rows]
    data = [float(total) for _, total in rows]
    return labels, data
