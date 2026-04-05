from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    openai_chat_model: str = Field("gpt-4.1-mini", alias="OPENAI_CHAT_MODEL")
    openai_vision_model: str = Field("gpt-4.1-mini", alias="OPENAI_VISION_MODEL")
    openai_embedding_model: str = Field("text-embedding-3-small", alias="OPENAI_EMBEDDING_MODEL")
    chroma_persist_dir: str = Field("data/chroma_db", alias="CHROMA_PERSIST_DIR")
    collection_name: str = Field("supplier_quality_chunks", alias="COLLECTION_NAME")
    top_k: int = Field(6, alias="TOP_K")
    image_summary_max_tokens: int = Field(220, alias="IMAGE_SUMMARY_MAX_TOKENS")
    answer_max_tokens: int = Field(900, alias="ANSWER_MAX_TOKENS")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def chroma_path(self) -> Path:
        path = Path(self.chroma_persist_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
