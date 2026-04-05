from __future__ import annotations

import hashlib
import math
import re
from typing import Iterable, List

from src.config import get_settings
from src.models.openai_client import get_openai_client

TOKEN_RE = re.compile(r"[A-Za-z0-9_./-]+")
FALLBACK_DIMENSION = 256


def _normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def _local_embed(text: str, dimension: int = FALLBACK_DIMENSION) -> list[float]:
    vector = [0.0] * dimension
    for token in TOKEN_RE.findall(text.lower()):
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimension
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign
    return _normalize(vector)


def embed_texts(texts: Iterable[str]) -> List[List[float]]:
    text_list = [str(text).strip() for text in texts if text and str(text).strip()]
    if not text_list:
        return []

    settings = get_settings()
    try:
        client = get_openai_client()
        response = client.embeddings.create(model=settings.openai_embedding_model, input=text_list)
        return [item.embedding for item in response.data]
    except Exception:
        return [_local_embed(text) for text in text_list]
