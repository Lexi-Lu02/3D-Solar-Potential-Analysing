"""
Application settings.

Loaded from environment variables (and a local .env file during development)
via pydantic-settings. Validation happens once at process start, so a
mis-spelled or missing variable surfaces immediately rather than at the first
request.
"""

from functools import lru_cache

from pydantic import Field
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

    # --- Connection pool ---
    db_pool_min_size: int = Field(1, ge=1)
    db_pool_max_size: int = Field(10, ge=1)

    # --- CORS ---
    # Comma-separated list. Empty in production (same-origin behind nginx).
    cors_origins: str = Field("", description="Comma-separated allowed origins")

    # --- Logging ---
    log_level: str = Field("INFO")

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
