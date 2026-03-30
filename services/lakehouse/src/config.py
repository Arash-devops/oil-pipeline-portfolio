"""
Configuration management using pydantic-settings.

Reads values from environment variables first, then falls back to a .env file.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration for the lakehouse service.

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

    # -- Storage ------------------------------------------------------------
    DATA_DIR: str = Field(default="data", description="Root directory for Parquet files")

    # -- Runtime ------------------------------------------------------------
    LOG_LEVEL: str = Field(default="INFO", description="Python logging level")

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
    def data_path(self) -> Path:
        """Return DATA_DIR as a resolved Path object."""
        return Path(self.DATA_DIR).resolve()

    @property
    def raw_path(self) -> Path:
        """Bronze layer root: {DATA_DIR}/raw/oil_prices/"""
        return self.data_path / "raw" / "oil_prices"

    @property
    def curated_path(self) -> Path:
        """Silver layer root: {DATA_DIR}/curated/oil_prices/"""
        return self.data_path / "curated" / "oil_prices"

    @property
    def quality_report_path(self) -> Path:
        """Quality report directory: {DATA_DIR}/curated/_quality_report/"""
        return self.data_path / "curated" / "_quality_report"

    @property
    def serving_path(self) -> Path:
        """Gold layer root: {DATA_DIR}/serving/"""
        return self.data_path / "serving"

    @property
    def db_conninfo(self) -> str:
        """Return a psycopg v3 conninfo string."""
        return (
            f"host={self.DB_HOST} port={self.DB_PORT} "
            f"dbname={self.DB_NAME} user={self.DB_USER} "
            f"password={self.DB_PASSWORD} connect_timeout=10"
        )
