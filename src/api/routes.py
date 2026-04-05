from __future__ import annotations

import time
import traceback
from collections import Counter
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from src.config import get_settings
from src.schemas import (
    DeleteDocumentResponse,
    DocumentListResponse,
    DocumentRecord,
    HealthResponse,
    IngestResponse,
    QueryRequest,
)
from src.services import app_state, run_query
from src.utils.files import ensure_directory, unique_document_id

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["System"])
def health() -> HealthResponse:
    settings = get_settings()
    app_state.initialize()
    return HealthResponse(
        status="ok",
        model_ready=bool(settings.openai_api_key and "your_openai_api_key_here" not in settings.openai_api_key.lower()),
        indexed_documents=app_state.vector_store.document_count(),
        index_size=app_state.vector_store.index_size(),
        uptime_seconds=round(time.time() - app_state.started_at, 2),
        chat_model=settings.openai_chat_model,
        vision_model=settings.openai_vision_model,
        embedding_model=settings.openai_embedding_model,
    )


@router.post("/ingest", tags=["Ingestion"])
async def ingest(file: UploadFile = File(...)):
    stage = "validate upload"
    try:
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            return JSONResponse(
                content={"detail": "Only PDF uploads are supported."},
                status_code=400,
            )

        stage = "read upload bytes"
        payload = await file.read()
        if not payload:
            return JSONResponse(
                content={"detail": "Uploaded file is empty."},
                status_code=400,
            )

        stage = "save uploaded file"
        uploads_dir = ensure_directory(Path("data/uploads"))
        document_id = unique_document_id(file.filename)
        target_path = uploads_dir / f"{document_id}.pdf"
        target_path.write_bytes(payload)

        stage = "parse pdf"
        parsed_document = app_state.parser.parse(target_path)
        if not parsed_document.chunks:
            return JSONResponse(
                content={"detail": "No ingestible text, table, or image content was found in the PDF."},
                status_code=400,
            )

        stage = "prepare chunk payload"
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

        if not chunk_dicts:
            return JSONResponse(
                content={"detail": "The PDF was parsed, but no non-empty chunks were produced."},
                status_code=400,
            )

        stage = "index chunks"
        app_state.vector_store.add_chunks(
            document_id=document_id,
            filename=file.filename,
            pages=parsed_document.pages,
            chunks=chunk_dicts,
        )

        counts = Counter(chunk["chunk_type"] for chunk in chunk_dicts)

        result = IngestResponse(
            document_id=document_id,
            filename=file.filename,
            pages=parsed_document.pages,
            text_chunks=counts.get("text", 0),
            table_chunks=counts.get("table", 0),
            image_summary_chunks=counts.get("image_summary", 0),
            total_chunks=len(chunk_dicts),
            processing_time_seconds=0.0,
        )

        return JSONResponse(content=jsonable_encoder(result), status_code=200)

    except Exception as exc:
        traceback.print_exc()
        return JSONResponse(
            content={"detail": f"Ingest failed during '{stage}': {type(exc).__name__}: {exc}"},
            status_code=500,
        )


@router.post("/query", tags=["Retrieval"])
def query(request: QueryRequest):
    try:
        result = run_query(question=request.question, top_k=request.top_k)
        return JSONResponse(content=jsonable_encoder(result), status_code=200)
    except HTTPException as exc:
        return JSONResponse(content={"detail": exc.detail}, status_code=exc.status_code)
    except Exception as exc:
        traceback.print_exc()
        return JSONResponse(
            content={"detail": f"Route caught: {type(exc).__name__}: {exc}"},
            status_code=500,
        )


@router.get("/documents", response_model=DocumentListResponse, tags=["Documents"])
def list_documents() -> DocumentListResponse:
    app_state.initialize()
    records = [DocumentRecord(**record) for record in app_state.vector_store.list_documents()]
    return DocumentListResponse(documents=records)


@router.delete("/documents/{document_id}", response_model=DeleteDocumentResponse, tags=["Documents"])
def delete_document(document_id: str) -> DeleteDocumentResponse:
    app_state.initialize()
    deleted_chunks = app_state.vector_store.delete_document(document_id)
    return DeleteDocumentResponse(document_id=document_id, deleted_chunks=deleted_chunks)
