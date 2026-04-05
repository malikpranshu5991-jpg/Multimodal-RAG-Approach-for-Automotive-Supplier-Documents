from __future__ import annotations

from pathlib import Path
from uuid import uuid4


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def unique_document_id(filename: str) -> str:
    stem = Path(filename).stem.replace(" ", "_").replace("-", "_")
    stem = "".join(ch for ch in stem if ch.isalnum() or ch == "_").lower().strip("_")
    stem = stem[:40] or "document"
    return f"{stem}_{uuid4().hex[:8]}"
