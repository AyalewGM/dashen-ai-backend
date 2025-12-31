from __future__ import annotations

import csv
from io import TextIOWrapper

from .models import DatasetType


def _normalize_headers(headers: list[str]) -> set[str]:
    return {h.strip() for h in headers if h is not None}


def validate_csv_schema(*, dataset_type: DatasetType, file_obj) -> None:
    wrapper = TextIOWrapper(file_obj, encoding="utf-8", newline="")
    reader = csv.reader(wrapper)
    headers = next(reader, None)
    if not headers:
        raise ValueError("CSV is empty or missing header row")

    header_set = _normalize_headers([str(h) for h in headers])

    if dataset_type == "customer":
        required = {"customer_id", "tx_timestamp", "amount", "direction", "category"}
    else:
        required = {"kpi_date", "metric_name", "metric_value"}

    missing = sorted([h for h in required if h not in header_set])
    if missing:
        raise ValueError(f"CSV missing required headers: {', '.join(missing)}")

    file_obj.seek(0)
