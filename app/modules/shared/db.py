from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator, Optional

import psycopg2
from psycopg2.extensions import connection as PgConnection

from .logging import logger


def get_database_url() -> Optional[str]:
    url = os.getenv("DATABASE_URL")
    if not url:
        return None
    return url


def get_db_connection() -> Optional[PgConnection]:
    """Return a raw psycopg2 connection. Caller is responsible for closing it."""
    database_url = get_database_url()
    if not database_url:
        return None
    return psycopg2.connect(database_url)


@contextmanager
def get_db_conn() -> Iterator[PgConnection]:
    database_url = get_database_url()
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    conn = psycopg2.connect(database_url)
    try:
        yield conn
    finally:
        conn.close()


def ensure_tables_exist() -> None:
    database_url = get_database_url()
    if not database_url:
        logger.warning("DATABASE_URL not set; skipping DB table bootstrap")
        return

    ddl_statements = [
        """
        CREATE TABLE IF NOT EXISTS datasets (
            dataset_id UUID PRIMARY KEY,
            dataset_name TEXT NOT NULL,
            dataset_type TEXT NOT NULL CHECK (dataset_type IN ('customer','internal')),
            uploaded_by_actor_type TEXT NOT NULL CHECK (uploaded_by_actor_type IN ('internal','customer')),
            uploaded_by_actor_id TEXT NOT NULL,
            file_path TEXT NOT NULL,
            row_count INTEGER NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS customers (
            customer_id TEXT PRIMARY KEY,
            bank_id TEXT NOT NULL DEFAULT 'dashen',
            name TEXT,
            email TEXT,
            phone TEXT,
            account_type TEXT NOT NULL,
            risk_score INTEGER DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS accounts (
            account_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
            bank_id TEXT NOT NULL DEFAULT 'dashen',
            account_type TEXT NOT NULL,
            balance NUMERIC NOT NULL DEFAULT 0,
            currency TEXT NOT NULL DEFAULT 'ETB',
            status TEXT NOT NULL DEFAULT 'active',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS transactions (
            tx_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
            account_id TEXT REFERENCES accounts(account_id) ON DELETE SET NULL,
            bank_id TEXT NOT NULL DEFAULT 'dashen',
            tx_timestamp TIMESTAMPTZ NOT NULL,
            amount NUMERIC NOT NULL,
            currency TEXT NOT NULL DEFAULT 'ETB',
            direction TEXT NOT NULL CHECK (direction IN ('debit','credit')),
            channel TEXT NOT NULL,
            merchant TEXT,
            category TEXT,
            subcategory TEXT,
            location_country TEXT,
            location_city TEXT,
            region TEXT,
            branch TEXT,
            device_id TEXT,
            ip_address TEXT,
            reference_text TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_transactions_customer_time
        ON transactions(customer_id, tx_timestamp);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_transactions_bank_time
        ON transactions(bank_id, tx_timestamp);
        """,
        """
        CREATE TABLE IF NOT EXISTS internal_kpis (
            kpi_id SERIAL PRIMARY KEY,
            bank_id TEXT NOT NULL DEFAULT 'dashen',
            kpi_date DATE NOT NULL,
            metric_name TEXT NOT NULL,
            metric_value NUMERIC NOT NULL,
            segment_type TEXT,
            segment_value TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE(bank_id, kpi_date, metric_name, segment_type, segment_value)
        );
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_internal_kpis_metric_date
        ON internal_kpis(bank_id, metric_name, kpi_date);
        """,
    ]

    with get_db_conn() as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            for stmt in ddl_statements:
                try:
                    cur.execute(stmt)
                except Exception as e:
                    logger.warning(f"Skipped DDL statement: {e}", extra={"service_module": "db", "session_id": "-"})

    logger.info("DB tables ensured", extra={"service_module": "db", "session_id": "-"})
