from __future__ import annotations

from typing import Iterable, List


def normalize_whitespace(text: str) -> str:
    lines = [" ".join(line.split()) for line in text.splitlines()]
    compact = "\n".join(line for line in lines if line)
    return compact.strip()


def chunk_text(text: str, max_chars: int = 1200, overlap: int = 180) -> List[str]:
    """Split long text into overlapping character windows while respecting paragraph breaks."""

    cleaned = normalize_whitespace(text)
    if not cleaned:
        return []

    paragraphs = [p.strip() for p in cleaned.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [cleaned]

    chunks: List[str] = []
    current = ""
    for paragraph in paragraphs:
        addition = paragraph if not current else f"{current}\n\n{paragraph}"
        if len(addition) <= max_chars:
            current = addition
            continue
        if current:
            chunks.append(current)
        if len(paragraph) <= max_chars:
            current = paragraph
            continue
        start = 0
        while start < len(paragraph):
            end = start + max_chars
            piece = paragraph[start:end]
            chunks.append(piece)
            if end >= len(paragraph):
                break
            start = max(0, end - overlap)
        current = ""
    if current:
        chunks.append(current)
    return chunks


def truncate(text: str, limit: int = 280) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def markdown_table(rows: Iterable[Iterable[str]]) -> str:
    rows = [list(row) for row in rows if any(cell is not None and str(cell).strip() for cell in row)]
    if not rows:
        return ""

    width = max(len(row) for row in rows)
    padded = [[str(cell or "").strip() for cell in row] + [""] * (width - len(row)) for row in rows]

    header = padded[0]
    separator = ["---"] * width
    body = padded[1:] if len(padded) > 1 else []

    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join(separator) + " |"]
    lines.extend("| " + " | ".join(row) + " |" for row in body)
    return "\n".join(lines)
