from pathlib import Path
from collections import Counter
import traceback

from src.ingestion.parser import PDFParser
from src.retrieval.vector_store import VectorStore

pdf_path = Path("sample_documents/continental_supplier_requirements_manual_2024.pdf")

try:
    print("STEP 1: parsing PDF...")
    parsed = PDFParser().parse(pdf_path)
    print("pages =", parsed.pages)
    print("chunk_count =", len(parsed.chunks))
    print("chunk_types =", Counter(chunk.chunk_type for chunk in parsed.chunks))

    chunk_dicts = [
        {
            "chunk_id": chunk.chunk_id,
            "chunk_type": chunk.chunk_type,
            "page": chunk.page,
            "content": chunk.content,
        }
        for chunk in parsed.chunks
        if chunk.content and str(chunk.content).strip()
    ]

    print("STEP 2: creating vector store...")
    store = VectorStore()

    print("STEP 3: adding chunks...")
    store.add_chunks(
        document_id="debug_continental_supplier_manual",
        filename=pdf_path.name,
        pages=parsed.pages,
        chunks=chunk_dicts,
    )

    print("SUCCESS")
    print("index_size =", store.index_size())

except Exception:
    traceback.print_exc()
