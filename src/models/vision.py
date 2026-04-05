from __future__ import annotations

import base64

from src.config import get_settings
from src.models.openai_client import get_openai_client
from src.utils.text import normalize_whitespace, truncate


VISION_PROMPT = (
    "You are summarising an image extracted from an automotive supplier quality PDF. "
    "Describe only what is visibly present and useful for retrieval. Include labels, phases, dates, arrows, "
    "tables, milestone relationships, and any PPAP/APQP terminology. Keep the summary factual and concise."
)


def summarize_image(image_bytes: bytes) -> str:
    settings = get_settings()
    client = get_openai_client()
    encoded = base64.b64encode(image_bytes).decode("utf-8")

    response = client.responses.create(
        model=settings.openai_vision_model,
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": VISION_PROMPT},
                    {
                        "type": "input_image",
                        "image_url": f"data:image/png;base64,{encoded}",
                        "detail": "high",
                    },
                ],
            }
        ],
        max_output_tokens=settings.image_summary_max_tokens,
    )
    return (response.output_text or "").strip()


def fallback_visual_summary(page_text: str, page_number: int) -> str:
    cleaned = normalize_whitespace(page_text)
    if not cleaned:
        return f"Fallback visual summary for page {page_number}: page contains visual layout but no extractable image labels were available."
    return (
        f"Fallback visual summary for page {page_number}. The page contains a visual layout or diagram related to automotive supplier quality. "
        f"Visible or associated labels from the page text include: {truncate(cleaned, 700)}"
    )
