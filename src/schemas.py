from typing import List, Literal, Optional

from pydantic import BaseModel, Field

ChunkType = Literal["text", "table", "image_summary"]


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, description="Natural language question to ask over indexed documents.")
    top_k: Optional[int] = Field(None, ge=1, le=20, description="Optional override for retrieval depth.")


class SourceReference(BaseModel):
    document_id: str
    filename: str
    page: int
    chunk_type: ChunkType
    chunk_id: str
    excerpt: str


class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: List[SourceReference]
    retrieved_chunks: int


class IngestResponse(BaseModel):
    document_id: str
    filename: str
    pages: int
    text_chunks: int
    table_chunks: int
    image_summary_chunks: int
    total_chunks: int
    processing_time_seconds: float


class HealthResponse(BaseModel):
    status: Literal["ok"]
    model_ready: bool
    indexed_documents: int
    index_size: int
    uptime_seconds: float
    chat_model: str
    vision_model: str
    embedding_model: str


class DocumentRecord(BaseModel):
    document_id: str
    filename: str
    pages: int
    chunk_count: int


class DocumentListResponse(BaseModel):
    documents: List[DocumentRecord]


class DeleteDocumentResponse(BaseModel):
    document_id: str
    deleted_chunks: int
