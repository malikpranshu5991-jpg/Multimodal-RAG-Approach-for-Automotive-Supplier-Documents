from __future__ import annotations

import re
from typing import Iterable, Sequence

from src.config import get_settings
from src.models.openai_client import get_openai_client
from src.schemas import SourceReference


SYSTEM_PROMPT = """You are a grounded assistant for automotive supplier quality documentation.
Answer only from the retrieved context.
Write a direct, understandable answer first.
Then add a short 'Key evidence' section with 2-4 bullets.
Do not mention internal implementation details.
Do not say 'Source 1 says' unless absolutely necessary.
Do not invent requirements, document names, page numbers, or standards.
If the context is insufficient, say that clearly.
"""


_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how", "in", "is", "it", "of",
    "on", "or", "that", "the", "their", "this", "to", "what", "when", "which", "with", "would", "does",
    "do", "about", "across", "according", "regarding", "regard", "into", "must", "should", "can", "could",
}


def build_context(sources: Sequence[SourceReference]) -> str:
    blocks: list[str] = []
    for index, source in enumerate(sources, start=1):
        blocks.append(
            f"[Source {index}]\n"
            f"Filename: {source.filename}\n"
            f"Page: {source.page}\n"
            f"Chunk Type: {source.chunk_type}\n"
            f"Content:\n{source.excerpt}\n"
        )
    return "\n".join(blocks)


def _question_terms(question: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-zA-Z0-9@_-]+", question.lower())
        if len(token) > 2 and token not in _STOPWORDS
    }


def _clean_sentence(sentence: str) -> str:
    sentence = sentence.replace("\n", " ").strip(" -•\t")
    sentence = re.sub(r"\s+", " ", sentence)
    return sentence


def _split_candidate_sentences(text: str) -> list[str]:
    rough_parts = re.split(r"(?<=[.!?])\s+|\n+|[•▪]\s*", text)
    cleaned = []
    for part in rough_parts:
        part = _clean_sentence(part)
        if len(part) < 25:
            continue
        if part.lower().startswith(("source 1", "source 2", "source 3")):
            continue
        cleaned.append(part)
    return cleaned


def _rank_sentences(question: str, sources: Sequence[SourceReference]) -> list[tuple[float, str]]:
    terms = _question_terms(question)
    ranked: list[tuple[float, str]] = []

    for source in sources:
        base_weight = {"text": 1.0, "table": 0.95, "image_summary": 0.9}.get(source.chunk_type, 1.0)
        for sentence in _split_candidate_sentences(source.excerpt):
            sentence_terms = set(re.findall(r"[a-zA-Z0-9@_-]+", sentence.lower()))
            overlap = len(terms & sentence_terms)
            score = overlap * 3.0 + base_weight
            if any(term in sentence.lower() for term in terms):
                score += 1.0
            if source.chunk_type == "table" and any(k in question.lower() for k in ["table", "list", "values", "requirements"]):
                score += 1.0
            if source.chunk_type == "image_summary" and any(k in question.lower() for k in ["image", "diagram", "figure", "chart", "visual", "illustration"]):
                score += 1.0
            ranked.append((score, sentence))

    ranked.sort(key=lambda item: item[0], reverse=True)
    return ranked


def _dedupe_preserve_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        key = re.sub(r"\W+", " ", item.lower()).strip()
        if key in seen:
            continue
        seen.add(key)
        output.append(item)
    return output


def _fallback_answer(question: str, sources: Sequence[SourceReference]) -> str:
    if not sources:
        return "The available context is insufficient to answer the question."

    ranked = _rank_sentences(question, sources)
    selected_sentences = _dedupe_preserve_order([sentence for score, sentence in ranked if score > 1.0])[:4]
    if not selected_sentences:
        selected_sentences = _dedupe_preserve_order([_clean_sentence(source.excerpt) for source in sources if source.excerpt])[:3]

    primary = selected_sentences[0] if selected_sentences else "The retrieved context is relevant but not detailed enough to produce a clear answer."
    evidence = selected_sentences[1:4]

    answer_lines = [primary]
    if evidence:
        answer_lines.append("")
        answer_lines.append("Key evidence:")
        for item in evidence:
            answer_lines.append(f"- {item}")

    answer_lines.append("")
    answer_lines.append("Sources used:")
    for source in sources[:4]:
        answer_lines.append(f"- {source.filename}, page {source.page}, {source.chunk_type}")

    return "\n".join(answer_lines)


def generate_answer(question: str, sources: Sequence[SourceReference]) -> str:
    settings = get_settings()
    client = get_openai_client()
    context = build_context(sources)

    user_prompt = (
        f"Question: {question}\n\n"
        f"Retrieved Context:\n{context}\n\n"
        "Write the answer in this exact structure:\n"
        "1. A direct answer in 1 short paragraph.\n"
        "2. A heading: Key evidence\n"
        "3. 2 to 4 concise bullet points drawn only from the retrieved context.\n"
        "4. Mention relevant source numbers inline like [Source 1] or [Source 2].\n"
        "Do not repeat the full source excerpts. Do not mention system limitations."
    )

    try:
        response = client.responses.create(
            model=settings.openai_chat_model,
            input=[
                {"role": "system", "content": [{"type": "input_text", "text": SYSTEM_PROMPT}]},
                {"role": "user", "content": [{"type": "input_text", "text": user_prompt}]},
            ],
            max_output_tokens=settings.answer_max_tokens,
        )
        text = (getattr(response, "output_text", "") or "").strip()
        if text:
            return text
    except Exception:
        pass

    return _fallback_answer(question, sources)
