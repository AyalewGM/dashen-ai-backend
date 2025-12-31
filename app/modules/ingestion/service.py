from __future__ import annotations

import csv
import uuid
from datetime import date
from decimal import Decimal
from io import TextIOWrapper
from typing import Any

from fastapi import UploadFile

from app.modules.shared.db import get_database_url, get_db_conn

from .models import DatasetType, IngestionSeedDemoResponse, IngestionUploadResponse
from .storage import save_upload
from .validators import validate_csv_schema


class IngestionService:
    def upload_and_ingest(
        self,
        *,
        file: UploadFile,
        dataset_type: DatasetType,
        dataset_name: str,
        uploaded_by_actor_type: str,
        uploaded_by_actor_id: str,
    ) -> IngestionUploadResponse:
        if not get_database_url():
            raise RuntimeError("DATABASE_URL is not configured")

        validate_csv_schema(dataset_type=dataset_type, file_obj=file.file)
        file_path = save_upload(file)

        if dataset_type == "customer":
            row_count = self._ingest_customer_csv(file)
        else:
            row_count = self._ingest_internal_csv(file)

        dataset_id = str(uuid.uuid4())
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO datasets (
                        dataset_id, dataset_name, dataset_type,
                        uploaded_by_actor_type, uploaded_by_actor_id,
                        file_path, row_count
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        dataset_id,
                        dataset_name,
                        dataset_type,
                        uploaded_by_actor_type,
                        uploaded_by_actor_id,
                        file_path,
                        row_count,
                    ),
                )
            conn.commit()

        return IngestionUploadResponse(datasetId=dataset_id, rowCount=row_count, status="ok")

    def seed_demo(self) -> IngestionSeedDemoResponse:
        if not get_database_url():
            raise RuntimeError("DATABASE_URL is not configured")

        customers = [
            {"customer_id": "cust-demo-001", "name": "Abel T."},
            {"customer_id": "cust-demo-002", "name": "Hanna M."},
            {"customer_id": "cust-demo-003", "name": "Sami K."},
        ]

        accounts = [
            {"account_id": "acc-001", "customer_id": "cust-demo-001", "account_type": "checking"},
            {"account_id": "acc-002", "customer_id": "cust-demo-002", "account_type": "checking"},
            {"account_id": "acc-003", "customer_id": "cust-demo-003", "account_type": "savings"},
        ]

        txs = [
            {
                "tx_id": "tx-001",
                "customer_id": "cust-demo-001",
                "account_id": "acc-001",
                "tx_timestamp": "2025-12-01T10:00:00Z",
                "amount": Decimal("450"),
                "currency": "ETB",
                "direction": "debit",
                "merchant": "Dashen Utilities",
                "category": "utilities",
                "subcategory": "electricity",
                "channel": "mobile",
                "reference_text": "Electric bill",
            },
            {
                "tx_id": "tx-002",
                "customer_id": "cust-demo-001",
                "account_id": "acc-001",
                "tx_timestamp": "2025-12-05T14:00:00Z",
                "amount": Decimal("820"),
                "currency": "ETB",
                "direction": "debit",
                "merchant": "Fresh Market",
                "category": "groceries",
                "subcategory": None,
                "channel": "pos",
                "reference_text": "Groceries",
            },
            {
                "tx_id": "tx-003",
                "customer_id": "cust-demo-002",
                "account_id": "acc-002",
                "tx_timestamp": "2025-12-03T09:30:00Z",
                "amount": Decimal("3200"),
                "currency": "ETB",
                "direction": "credit",
                "merchant": "Employer",
                "category": "salary",
                "subcategory": None,
                "channel": "transfer",
                "reference_text": "Salary",
            },
        ]

        kpis = [
            {"kpi_date": date(2025, 11, 1), "metric_name": "deposits", "metric_value": Decimal("100")},
            {"kpi_date": date(2025, 11, 15), "metric_name": "deposits", "metric_value": Decimal("106")},
            {"kpi_date": date(2025, 12, 1), "metric_name": "deposits", "metric_value": Decimal("112")},
            {"kpi_date": date(2025, 12, 15), "metric_name": "deposits", "metric_value": Decimal("118")},
            {"kpi_date": date(2025, 11, 1), "metric_name": "loans", "metric_value": Decimal("80")},
            {"kpi_date": date(2025, 12, 15), "metric_name": "loans", "metric_value": Decimal("86")},
            {"kpi_date": date(2025, 12, 15), "metric_name": "digital_adoption", "metric_value": Decimal("0.62")},
            {"kpi_date": date(2025, 12, 15), "metric_name": "npl_proxy", "metric_value": Decimal("2.4")},
        ]

        with get_db_conn() as conn:
            with conn.cursor() as cur:
                for c in customers:
                    cur.execute(
                        """
                        INSERT INTO customers (customer_id, name)
                        VALUES (%s,%s)
                        ON CONFLICT (customer_id) DO UPDATE SET name = EXCLUDED.name
                        """,
                        (c["customer_id"], c["name"]),
                    )

                for a in accounts:
                    cur.execute(
                        """
                        INSERT INTO accounts (account_id, customer_id, account_type)
                        VALUES (%s,%s,%s)
                        ON CONFLICT (account_id) DO UPDATE
                        SET customer_id = EXCLUDED.customer_id,
                            account_type = EXCLUDED.account_type
                        """,
                        (a["account_id"], a["customer_id"], a["account_type"]),
                    )

                for t in txs:
                    cur.execute(
                        """
                        INSERT INTO transactions (
                            tx_id, customer_id, account_id, tx_timestamp,
                            amount, currency, direction,
                            merchant, category, subcategory, channel, reference_text
                        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (tx_id) DO NOTHING
                        """,
                        (
                            t["tx_id"],
                            t["customer_id"],
                            t["account_id"],
                            t["tx_timestamp"],
                            t["amount"],
                            t["currency"],
                            t["direction"],
                            t["merchant"],
                            t["category"],
                            t["subcategory"],
                            t["channel"],
                            t["reference_text"],
                        ),
                    )

                for k in kpis:
                    cur.execute(
                        """
                        INSERT INTO internal_kpis (
                            kpi_date, metric_name, metric_value, segment_type, segment_value
                        ) VALUES (%s,%s,%s,NULL,NULL)
                        ON CONFLICT (kpi_date, metric_name, segment_type, segment_value)
                        DO UPDATE SET metric_value = EXCLUDED.metric_value
                        """,
                        (k["kpi_date"], k["metric_name"], k["metric_value"]),
                    )
            conn.commit()

        return IngestionSeedDemoResponse(
            status="ok",
            counts={
                "customers": len(customers),
                "accounts": len(accounts),
                "transactions": len(txs),
                "internal_kpis": len(kpis),
            },
        )

    def _ingest_customer_csv(self, file: UploadFile) -> int:
        wrapper = TextIOWrapper(file.file, encoding="utf-8", newline="")
        reader = csv.DictReader(wrapper)

        rows: list[dict[str, Any]] = [r for r in reader]
        file.file.seek(0)

        with get_db_conn() as conn:
            with conn.cursor() as cur:
                for r in rows:
                    customer_id = (r.get("customer_id") or "").strip()
                    if not customer_id:
                        continue

                    cur.execute(
                        """
                        INSERT INTO customers (customer_id, name)
                        VALUES (%s,%s)
                        ON CONFLICT (customer_id) DO NOTHING
                        """,
                        (customer_id, r.get("name")),
                    )

                    tx_id = (r.get("tx_id") or "").strip() or str(uuid.uuid4())
                    account_id = (r.get("account_id") or "").strip() or None
                    cur.execute(
                        """
                        INSERT INTO transactions (
                            tx_id, customer_id, account_id, tx_timestamp,
                            amount, currency, direction,
                            merchant, category, subcategory, channel, reference_text
                        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (tx_id) DO NOTHING
                        """,
                        (
                            tx_id,
                            customer_id,
                            account_id,
                            r.get("tx_timestamp"),
                            Decimal(str(r.get("amount") or "0")),
                            (r.get("currency") or "ETB"),
                            (r.get("direction") or "").strip().lower(),
                            r.get("merchant"),
                            r.get("category"),
                            r.get("subcategory"),
                            r.get("channel"),
                            r.get("reference_text"),
                        ),
                    )
            conn.commit()

        return len(rows)

    def _ingest_internal_csv(self, file: UploadFile) -> int:
        wrapper = TextIOWrapper(file.file, encoding="utf-8", newline="")
        reader = csv.DictReader(wrapper)

        rows: list[dict[str, Any]] = [r for r in reader]
        file.file.seek(0)

        with get_db_conn() as conn:
            with conn.cursor() as cur:
                for r in rows:
                    cur.execute(
                        """
                        INSERT INTO internal_kpis (
                            kpi_date, metric_name, metric_value, segment_type, segment_value
                        ) VALUES (%s,%s,%s,%s,%s)
                        ON CONFLICT (kpi_date, metric_name, segment_type, segment_value)
                        DO UPDATE SET metric_value = EXCLUDED.metric_value
                        """,
                        (
                            r.get("kpi_date"),
                            r.get("metric_name"),
                            Decimal(str(r.get("metric_value") or "0")),
                            r.get("segment_type"),
                            r.get("segment_value"),
                        ),
                    )
            conn.commit()

        return len(rows)
