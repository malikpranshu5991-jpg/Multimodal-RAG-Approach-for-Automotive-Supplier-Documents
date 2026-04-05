from __future__ import annotations

import shutil
import time
from collections import Counter
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, UploadFile

from src.config import get_settings
from src.ingestion.parser import PDFParser
from src.models.generator import generate_answer
from src.retrieval.vector_store import VectorStore
from src.schemas import IngestResponse, QueryResponse, SourceReference
from src.utils.files import ensure_directory, unique_document_id
from src.utils.text import truncate


class AppState:
    def __init__(self) -> None:
        self.started_at = time.time()
        self._vector_store: Optional[VectorStore] = None
        self._parser: Optional[PDFParser] = None

    def initialize(self) -> None:
        if self._vector_store is None:
            self._vector_store = VectorStore()
        if self._parser is None:
            self._parser = PDFParser()

    @property
    def vector_store(self) -> VectorStore:
        self.initialize()
        assert self._vector_store is not None
        return self._vector_store

    @property
    def parser(self) -> PDFParser:
        self.initialize()
        assert self._parser is not None
        return self._parser


app_state = AppState()


def ingest_pdf(file: UploadFile) -> IngestResponse:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported.")

    uploads_dir = ensure_directory(Path("data/uploads"))
    document_id = unique_document_id(file.filename)
    target_path = uploads_dir / f"{document_id}.pdf"

    start_time = time.perf_counter()
    with target_path.open("wb") as output:
        shutil.copyfileobj(file.file, output)

    try:
        parsed_document = app_state.parser.parse(target_path)
        if not parsed_document.chunks:
            raise HTTPException(status_code=400, detail="No ingestible text, table, or image content was found in the PDF.")

        chunk_dicts = [
            {
                "chunk_id": chunk.chunk_id,
                "chunk_type": chunk.chunk_type,
                "page": chunk.page,
                "content": chunk.content,
            }
            for chunk in parsed_document.chunks
            if chunk.content and str(chunk.content).strip()
        ]

        app_state.vector_store.add_chunks(
            document_id=document_id,
            filename=file.filename,
            pages=parsed_document.pages,
            chunks=chunk_dicts,
        )

        counts = Counter(chunk["chunk_type"] for chunk in chunk_dicts)
        elapsed = round(time.perf_counter() - start_time, 2)

        return IngestResponse(
            document_id=document_id,
            filename=file.filename,
            pages=parsed_document.pages,
            text_chunks=counts.get("text", 0),
            table_chunks=counts.get("table", 0),
            image_summary_chunks=counts.get("image_summary", 0),
            total_chunks=len(chunk_dicts),
            processing_time_seconds=elapsed,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {exc}") from exc


def _looks_like_demo_prompt_chunk(text: str) -> bool:
    lowered = text.lower()
    markers = [
        "question type",
        "text-focused",
        "table-focused",
        "image-focused",
        "cross-modal",
        "example query",
    ]
    return sum(marker in lowered for marker in markers) >= 2


def _source_priority(question: str, chunk_type: str) -> int:
    q = question.lower()
    if any(word in q for word in ["image", "diagram", "figure", "visual", "illustration", "chart"]):
        order = {"image_summary": 0, "text": 1, "table": 2}
    elif any(word in q for word in ["table", "list", "requirements", "values", "items"]):
        order = {"table": 0, "text": 1, "image_summary": 2}
    else:
        order = {"text": 0, "table": 1, "image_summary": 2}
    return order.get(chunk_type, 3)


def _prepare_sources(question: str, rows: list[dict]) -> list[SourceReference]:
    filtered_rows: list[dict] = []
    for row in rows:
        content = str(row.get("content", "") or "").strip()
        if not content:
            continue
        if _looks_like_demo_prompt_chunk(content):
            continue
        filtered_rows.append(row)

    if not filtered_rows:
        filtered_rows = rows

    filtered_rows.sort(
        key=lambda row: (
            _source_priority(question, str(row["metadata"].get("chunk_type", "text"))),
            float(row.get("distance", 999.0)),
        )
    )

    sources: list[SourceReference] = []
    seen_keys: set[tuple[str, int, str, str]] = set()
    seen_content: set[str] = set()

    for row in filtered_rows:
        metadata = row["metadata"]
        content = truncate(str(row["content"]), 500)
        content_key = " ".join(content.lower().split())
        key = (
            str(metadata["filename"]),
            int(metadata["page"]),
            str(metadata["chunk_type"]),
            str(metadata["chunk_id"]),
        )
        if key in seen_keys or content_key in seen_content:
            continue
        seen_keys.add(key)
        seen_content.add(content_key)
        sources.append(
            SourceReference(
                document_id=str(metadata["document_id"]),
                filename=str(metadata["filename"]),
                page=int(metadata["page"]),
                chunk_type=str(metadata["chunk_type"]),
                chunk_id=str(metadata["chunk_id"]),
                excerpt=content,
            )
        )
        if len(sources) >= 4:
            break

    return sources


def run_query(question: str, top_k: Optional[int] = None) -> QueryResponse:
    settings = get_settings()
    if app_state.vector_store.index_size() == 0:
        raise HTTPException(status_code=404, detail="The vector index is empty. Ingest at least one PDF before querying.")

    retrieval_depth = max(top_k or settings.top_k, 8)
    try:
        rows = app_state.vector_store.query(question, retrieval_depth)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Query failed during retrieval: {exc}") from exc
    if not rows:
        raise HTTPException(status_code=404, detail="No relevant chunks were retrieved for the question.")

    sources = _prepare_sources(question=question, rows=rows)
    if not sources:
        raise HTTPException(status_code=404, detail="Relevant chunks were found, but none were suitable for answer generation.")

    answer = generate_answer(question=question, sources=sources)
    return QueryResponse(question=question, answer=answer, sources=sources, retrieved_chunks=len(sources))
