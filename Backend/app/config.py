"""
Application settings.

Loaded from environment variables (and a local .env file during development)
via pydantic-settings. Validation happens once at process start, so a
mis-spelled or missing variable surfaces immediately rather than at the first
request.
"""

from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- PostgreSQL ---
    db_host: str = Field(..., description="PostgreSQL host")
    db_port: int = Field(5432, description="PostgreSQL port")
    db_name: str = Field(..., description="Database name")
    db_user: str = Field(..., description="DB user (use solarmap_api_ro in prod)")
    db_password: str = Field(..., description="DB password")

    # EDIT1: Google Solar API ---
    solar_api_key: str = Field("", description="Google Solar API key")
    # --- Connection pool ---
    db_pool_min_size: int = Field(1, ge=1)
    db_pool_max_size: int = Field(10, ge=1)

    # --- CORS ---
    # Comma-separated list. Empty in production (same-origin behind nginx).
    cors_origins: str = Field("", description="Comma-separated allowed origins")

    # --- Logging ---
    log_level: str = Field("INFO")

    # --- LLM (Qwen via DashScope OpenAI-compatible endpoint) ---
    dashscope_api_key: SecretStr = Field(
        SecretStr(""),
        description="Aliyun DashScope API key. Get from https://dashscope.console.aliyun.com",
    )
    qwen_base_url: str = Field(
        "https://dashscope.aliyuncs.com/compatible-mode/v1",
        description="OpenAI-compatible endpoint for Qwen",
    )
    qwen_model: str = Field(
        "qwen-flash",
        description="Single model used for chat / report / safety self-check",
    )
    ai_max_tokens_per_request: int = Field(4000, ge=256, le=16000)
    ai_max_tool_iterations: int = Field(6, ge=1, le=20)
    ai_rate_limit_per_minute: int = Field(10, ge=1)
    ai_history_window: int = Field(20, ge=2, description="Max messages kept after truncation")
    ai_history_max_tokens: int = Field(4000, ge=256, description="Approx token budget for history")
    ai_enable_self_critique: bool = Field(
        True,
        description="Run a second qwen-flash call to verify the output before returning",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def db_conninfo(self) -> str:
        """psycopg connection string."""
        return (
            f"host={self.db_host} port={self.db_port} "
            f"dbname={self.db_name} user={self.db_user} "
            f"password={self.db_password}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
