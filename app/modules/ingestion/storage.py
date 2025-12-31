from __future__ import annotations

import os
import re
import uuid
from pathlib import Path

from fastapi import UploadFile


def _safe_name(name: str) -> str:
    base = re.sub(r"[^a-zA-Z0-9._-]+", "_", name).strip("._-")
    return base or "upload.csv"


def get_uploads_dir() -> Path:
    root = os.getenv("UPLOADS_DIR") or os.path.join(os.getcwd(), "data", "uploads")
    path = Path(root)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_upload(file: UploadFile) -> str:
    uploads_dir = get_uploads_dir()
    filename = _safe_name(file.filename or "upload.csv")
    target = uploads_dir / f"{uuid.uuid4()}-{filename}"

    with target.open("wb") as out:
        while True:
            chunk = file.file.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)

    file.file.seek(0)
    return str(target)
