from __future__ import annotations

from typing import List

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.config import Settings as ChromaSettings

from src.config import get_settings
from src.models.embeddings import embed_texts


class VectorStore:
    def __init__(self) -> None:
        settings = get_settings()
        self.client = chromadb.PersistentClient(
            path=str(settings.chroma_path), settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection: Collection = self.client.get_or_create_collection(name=settings.collection_name)

    def add_chunks(self, document_id: str, filename: str, pages: int, chunks: list[dict]) -> None:
        if not chunks:
            return
        sanitized_chunks = [chunk for chunk in chunks if chunk.get("content") and str(chunk.get("content")).strip()]
        if not sanitized_chunks:
            return
        texts = [str(chunk["content"]).strip() for chunk in sanitized_chunks]
        embeddings = embed_texts(texts)
        if len(embeddings) != len(sanitized_chunks):
            raise ValueError(
                f"Embedding count mismatch. Expected {len(sanitized_chunks)} vectors but got {len(embeddings)}."
            )
        ids = [f"{document_id}:{chunk['chunk_id']}" for chunk in sanitized_chunks]
        metadatas = [
            {
                "document_id": str(document_id),
                "filename": str(filename),
                "page": int(chunk["page"]),
                "chunk_type": str(chunk["chunk_type"]),
                "chunk_id": str(chunk["chunk_id"]),
                "pages": int(pages),
            }
            for chunk in sanitized_chunks
        ]
        self.collection.add(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)

    def query(self, question: str, top_k: int) -> list[dict]:
        embeddings = embed_texts([question])
        if not embeddings:
            return []
        result = self.collection.query(
            query_embeddings=embeddings,
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        rows: list[dict] = []
        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        for document, metadata, distance in zip(docs, metas, distances):
            rows.append({"content": document, "metadata": metadata, "distance": distance})
        return rows

    def list_documents(self) -> list[dict]:
        payload = self.collection.get(include=["metadatas"])
        grouped: dict[str, dict] = {}
        for metadata in payload.get("metadatas", []):
            if not metadata:
                continue
            doc_id = metadata["document_id"]
            record = grouped.setdefault(
                doc_id,
                {
                    "document_id": doc_id,
                    "filename": metadata["filename"],
                    "pages": int(metadata.get("pages", 0)),
                    "chunk_count": 0,
                },
            )
            record["chunk_count"] += 1
        return list(grouped.values())

    def delete_document(self, document_id: str) -> int:
        payload = self.collection.get(where={"document_id": document_id}, include=["metadatas"])
        ids = payload.get("ids", [])
        if ids:
            self.collection.delete(ids=ids)
        return len(ids)

    def document_count(self) -> int:
        return len(self.list_documents())

    def index_size(self) -> int:
        return self.collection.count()
