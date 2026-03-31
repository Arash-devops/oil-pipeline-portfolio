"""
Shared FastAPI dependencies for database connections.

- PostgreSQL: AsyncConnectionPool (psycopg v3) — created once at startup.
- DuckDB: one in-memory connection per request with serving-layer views registered.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator, Generator
from datetime import UTC, datetime
from pathlib import Path

import duckdb
import psycopg
from psycopg_pool import AsyncConnectionPool

from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App-level state
# ---------------------------------------------------------------------------

APP_START_TIME: datetime = datetime.now(UTC)

# Module-level pool — None until init_pg_pool() is called during lifespan startup.
_pg_pool: AsyncConnectionPool | None = None


# ---------------------------------------------------------------------------
# PostgreSQL pool lifecycle
# ---------------------------------------------------------------------------


async def init_pg_pool() -> None:
    """Create the async PostgreSQL connection pool.

    Called once during application startup from the lifespan context manager.
    """
    global _pg_pool
    logger.info(
        "Initialising PostgreSQL pool (min=%d, max=%d) at %s:%d/%s",
        settings.pg_min_pool_size,
        settings.pg_max_pool_size,
        settings.pg_host,
        settings.pg_port,
        settings.pg_database,
    )
    _pg_pool = AsyncConnectionPool(
        conninfo=settings.pg_conninfo,
        min_size=settings.pg_min_pool_size,
        max_size=settings.pg_max_pool_size,
        open=False,
    )
    await _pg_pool.open(wait=True, timeout=30.0)
    logger.info("PostgreSQL pool ready.")


async def close_pg_pool() -> None:
    """Close the async PostgreSQL connection pool.

    Called once during application shutdown from the lifespan context manager.
    """
    global _pg_pool
    if _pg_pool is not None:
        await _pg_pool.close()
        _pg_pool = None
        logger.info("PostgreSQL pool closed.")


# ---------------------------------------------------------------------------
# FastAPI dependency: PostgreSQL connection
# ---------------------------------------------------------------------------


async def get_pg_conn() -> AsyncGenerator[psycopg.AsyncConnection]:
    """FastAPI dependency that yields a pooled async PostgreSQL connection.

    The connection is automatically returned to the pool after the request.

    Yields:
        An open psycopg.AsyncConnection from the pool.

    Raises:
        RuntimeError: If the pool has not been initialised.
    """
    if _pg_pool is None:
        raise RuntimeError("PostgreSQL pool is not initialised. Check app lifespan.")
    async with _pg_pool.connection() as conn:
        yield conn


# ---------------------------------------------------------------------------
# FastAPI dependency: DuckDB connection (sync — runs in thread pool)
# ---------------------------------------------------------------------------


def _serving_path() -> Path:
    """Return the path to the serving-layer Parquet directory."""
    return Path(settings.lakehouse_base_path) / "data" / "serving"


def get_duckdb_conn() -> Generator[duckdb.DuckDBPyConnection]:
    """FastAPI dependency that yields a DuckDB in-memory connection.

    Registers serving-layer Parquet files as DuckDB views on each call.
    A fresh connection is created per request because DuckDB connections
    are not thread-safe for concurrent access.

    Yields:
        A duckdb.DuckDBPyConnection with views pre-created over the serving layer.
    """
    serving = _serving_path()
    conn = duckdb.connect(":memory:")
    try:
        _register_serving_views(conn, serving)
        yield conn
    finally:
        conn.close()


def _register_serving_views(conn: duckdb.DuckDBPyConnection, serving: Path) -> None:
    """Register each serving-layer Parquet file as a DuckDB view.

    Uses .as_posix() on all paths so Windows backslashes never reach DuckDB.

    Args:
        conn: Open DuckDB connection.
        serving: Path to the serving-layer directory (data/serving/).
    """
    datasets = {
        "monthly_summary": serving / "monthly_summary" / "data.parquet",
        "price_metrics": serving / "price_metrics" / "data.parquet",
        "commodity_comparison": serving / "commodity_comparison" / "data.parquet",
    }

    for view_name, parquet_path in datasets.items():
        if parquet_path.exists():
            posix = parquet_path.as_posix()
            conn.execute(f"CREATE OR REPLACE VIEW {view_name} AS SELECT * FROM read_parquet('{posix}')")
            logger.debug("DuckDB view registered: %s → %s", view_name, posix)
        else:
            # Create an empty view so queries fail gracefully instead of crashing.
            logger.warning(
                "serving layer file not found, skipping view '%s': %s",
                view_name,
                parquet_path,
            )
            conn.execute(f"CREATE OR REPLACE VIEW {view_name} AS SELECT 1 WHERE FALSE")
