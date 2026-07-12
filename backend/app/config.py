from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables / .env file."""

    openai_api_key: str = ""
    openai_chat_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    database_url: str = "sqlite:///./knowledge_inbox.db"
    # Cosine similarity cutoff for text-embedding-3-small. Unrelated content
    # typically scores ~0.0-0.2; genuinely relevant matches are usually >=0.3.
    # Override via SIMILARITY_THRESHOLD in .env.
    similarity_threshold: float = 0.30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
