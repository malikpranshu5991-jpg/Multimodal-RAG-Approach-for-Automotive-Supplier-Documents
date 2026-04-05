from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

import fitz
import pdfplumber

from src.models.vision import fallback_visual_summary, summarize_image
from src.utils.text import chunk_text, markdown_table, normalize_whitespace


@dataclass
class ParsedChunk:
    chunk_id: str
    chunk_type: str
    page: int
    content: str


@dataclass
class ParsedDocument:
    pages: int
    chunks: List[ParsedChunk]


class PDFParser:
    """Extract text, tables, and image summaries from a PDF."""

    def parse(self, pdf_path: Path) -> ParsedDocument:
        chunks: List[ParsedChunk] = []

        with fitz.open(pdf_path) as doc, pdfplumber.open(str(pdf_path)) as plumber_doc:
            total_pages = len(doc)
            for page_index in range(total_pages):
                page_number = page_index + 1
                page = doc.load_page(page_index)
                plumber_page = plumber_doc.pages[page_index]

                page_text = page.get_text("text")
                chunks.extend(self._extract_text_chunks(page_text, page_number))
                chunks.extend(self._extract_table_chunks(plumber_page, page_number))
                image_chunks = self._extract_image_chunks(page, page_number)
                if image_chunks:
                    chunks.extend(image_chunks)
                else:
                    visual_chunk = self._extract_page_visual_chunk(page, page_text, page_number)
                    if visual_chunk is not None:
                        chunks.append(visual_chunk)

        return ParsedDocument(pages=total_pages, chunks=chunks)

    def _extract_text_chunks(self, page_text: str, page_number: int) -> List[ParsedChunk]:
        normalized = normalize_whitespace(page_text)
        text_chunks = chunk_text(normalized)
        return [
            ParsedChunk(
                chunk_id=f"page_{page_number}_text_{index}",
                chunk_type="text",
                page=page_number,
                content=chunk,
            )
            for index, chunk in enumerate(text_chunks, start=1)
            if chunk.strip()
        ]

    def _extract_table_chunks(self, plumber_page: pdfplumber.page.Page, page_number: int) -> List[ParsedChunk]:
        parsed: List[ParsedChunk] = []
        tables = plumber_page.extract_tables() or []
        for index, table in enumerate(tables, start=1):
            table_md = markdown_table(table)
            if not table_md.strip():
                continue
            parsed.append(
                ParsedChunk(
                    chunk_id=f"page_{page_number}_table_{index}",
                    chunk_type="table",
                    page=page_number,
                    content=table_md,
                )
            )
        return parsed

    def _extract_image_chunks(self, page: fitz.Page, page_number: int) -> List[ParsedChunk]:
        parsed: List[ParsedChunk] = []
        for index, image_info in enumerate(page.get_images(full=True), start=1):
            xref = image_info[0]
            image_data = page.parent.extract_image(xref)
            image_bytes = image_data.get("image")
            if not image_bytes:
                continue
            try:
                summary = summarize_image(image_bytes)
            except Exception:
                summary = fallback_visual_summary(page.get_text("text"), page_number)
            if not summary:
                continue
            parsed.append(
                ParsedChunk(
                    chunk_id=f"page_{page_number}_image_{index}",
                    chunk_type="image_summary",
                    page=page_number,
                    content=summary,
                )
            )
        return parsed

    def _extract_page_visual_chunk(self, page: fitz.Page, page_text: str, page_number: int) -> ParsedChunk | None:
        try:
            pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            image_bytes = pixmap.tobytes("png")
            summary = summarize_image(image_bytes)
        except Exception:
            summary = fallback_visual_summary(page_text, page_number)
        if not summary:
            return None
        return ParsedChunk(
            chunk_id=f"page_{page_number}_image_page_snapshot",
            chunk_type="image_summary",
            page=page_number,
            content=summary,
        )
