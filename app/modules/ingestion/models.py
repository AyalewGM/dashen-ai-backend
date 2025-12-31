from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


DatasetType = Literal["customer", "internal"]


class IngestionUploadResponse(BaseModel):
    dataset_id: str = Field(..., alias="datasetId")
    row_count: int = Field(..., alias="rowCount")
    status: str

    class Config:
        populate_by_name = True


class IngestionSeedDemoResponse(BaseModel):
    status: str
    counts: dict[str, int]
