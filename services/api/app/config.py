"""
Application configuration via pydantic-settings.

All settings can be overridden with OIL_API_* environment variables or a .env file.
"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """API service configuration.

    Loaded from environment variables (prefix OIL_API_) or .env file.
    All database credentials have sensible local-dev defaults.
    """

    # -- API metadata -------------------------------------------------------
    api_title: str = "Oil Price Data API"
    api_description: str = "REST API serving oil price data from PostgreSQL warehouse and DuckDB/Parquet lakehouse"
    api_version: str = "1.0.0"
    api_prefix: str = "/api/v1"
    debug: bool = True

    # -- PostgreSQL ---------------------------------------------------------
    pg_host: str = "localhost"
    pg_port: int = 5432
    pg_database: str = "oil_warehouse"
    pg_user: str = "arash"
    pg_password: str = "warehouse_dev_2026"
    pg_min_pool_size: int = 2
    pg_max_pool_size: int = 10

    # -- DuckDB / Lakehouse -------------------------------------------------
    # Resolves services/api/app/config.py → up 3 levels → services/ → lakehouse/
    lakehouse_base_path: str = str(Path(__file__).resolve().parent.parent.parent / "lakehouse")

    # -- CORS ---------------------------------------------------------------
    cors_origins: list[str] = ["*"]

    model_config = {
        "env_prefix": "OIL_API_",
        "env_file": ".env",
        "extra": "ignore",
    }

    @property
    def pg_conninfo(self) -> str:
        """Build a psycopg v3 conninfo string (no DSN URL — plain key=value)."""
        return (
            f"host={self.pg_host} port={self.pg_port} "
            f"dbname={self.pg_database} user={self.pg_user} "
            f"password={self.pg_password} connect_timeout=10"
        )


settings = Settings()
