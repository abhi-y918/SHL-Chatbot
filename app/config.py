"""Application configuration loaded from environment via pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All runtime configuration values."""

    app_env: str = "development"
    log_level: str = "INFO"

    # OpenRouter / LLM
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    llm_model: str = "meta-llama/llama-3.3-70b-instruct"
    llm_temperature: float = 0.4
    llm_max_tokens: int = 2048

    # Catalog
    catalog_url: str = (
        "https://tcp-us-prod-rnd.shl.com/voiceRater/shl-ai-hiring/"
        "shl_product_catalog.json"
    )

    # Retrieval
    retrieval_top_k: int = 20

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached singleton Settings instance."""
    return Settings()
