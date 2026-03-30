"""
Configuration management using pydantic-settings.

Reads values from environment variables first, then falls back to a .env file.
All database credentials must be supplied via the environment; never hardcoded.
"""

from __future__ import annotations

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration.

    All fields can be overridden by environment variables of the same name.
    A .env file in the working directory is loaded as a fallback.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # -- Database -----------------------------------------------------------
    DB_HOST: str = Field(default="localhost", description="PostgreSQL host")
    DB_PORT: int = Field(default=5432, description="PostgreSQL port")
    DB_NAME: str = Field(default="oil_warehouse", description="Database name")
    DB_USER: str = Field(default="arash", description="Database user")
    DB_PASSWORD: str = Field(default="warehouse_dev_2026", description="Database password")

    # -- Ingestion ----------------------------------------------------------
    COMMODITIES: str = Field(
        default="CL=F,BZ=F,NG=F,HO=F",
        description="Comma-separated list of Yahoo Finance ticker symbols",
    )
    SOURCE_NAME: str = Field(
        default="Yahoo Finance",
        description="Label written to warehouse.dim_source for every loaded row",
    )

    # -- Runtime ------------------------------------------------------------
    LOG_LEVEL: str = Field(default="INFO", description="Python logging level")
    RETRY_MAX_ATTEMPTS: int = Field(default=3, description="Max retry attempts for network calls")
    RETRY_BASE_DELAY: float = Field(default=2.0, description="Base delay (seconds) between retries")
    BACKFILL_YEARS: int = Field(default=5, description="Years of history to fetch on full backfill")
    BATCH_SIZE: int = Field(default=500, description="Rows per staging INSERT batch")

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Ensure LOG_LEVEL is a recognised Python logging level name."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}, got '{v}'")
        return upper

    @property
    def commodities_list(self) -> list[str]:
        """Return COMMODITIES parsed into a list of stripped ticker strings."""
        return [s.strip() for s in self.COMMODITIES.split(",") if s.strip()]

    @property
    def db_dsn(self) -> str:
        """Return a psycopg2-compatible DSN string (password not included in logs)."""
        return (
            f"host={self.DB_HOST} port={self.DB_PORT} "
            f"dbname={self.DB_NAME} user={self.DB_USER}"
        )
