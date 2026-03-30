"""
Health and info router.

Endpoints live directly under /api/v1 (no extra router prefix):
  GET /api/v1/health  — liveness / readiness check
  GET /api/v1/info    — API metadata and data-source statistics
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb
import psycopg
from fastapi import APIRouter, Depends

from app.config import settings
from app.dependencies import APP_START_TIME, get_duckdb_conn, get_pg_conn
from app.models.responses import ApiInfo, HealthCheck

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health & Info"])


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------

@router.get(
    "/health",
    response_model=HealthCheck,
    summary="Liveness and readiness check for both data backends",
)
async def health_check(
    conn: psycopg.AsyncConnection = Depends(get_pg_conn),
    duck: duckdb.DuckDBPyConnection = Depends(get_duckdb_conn),
) -> HealthCheck:
    """Check connectivity to PostgreSQL and DuckDB.

    Always returns HTTP 200. Individual component status is reported in the
    response body so monitoring systems can distinguish partial failures.

    Args:
        conn: Injected async PostgreSQL connection.
        duck: Injected DuckDB connection.

    Returns:
        HealthCheck with per-component status and uptime.
    """
    # PostgreSQL check
    pg_status = "unhealthy"
    try:
        async with conn.cursor() as cur:
            await cur.execute("SELECT 1")
            result = await cur.fetchone()
            if result and result[0] == 1:
                pg_status = "healthy"
    except Exception as exc:
        logger.warning("PostgreSQL health check failed: %s", exc)

    # DuckDB check
    duck_status = "unhealthy"
    try:
        result = duck.execute("SELECT 1").fetchone()
        if result and result[0] == 1:
            duck_status = "healthy"
    except Exception as exc:
        logger.warning("DuckDB health check failed: %s", exc)

    now = datetime.now(timezone.utc)
    uptime = (now - APP_START_TIME).total_seconds()
    overall = "healthy" if pg_status == "healthy" and duck_status == "healthy" else "degraded"

    return HealthCheck(
        status=overall,
        postgresql=pg_status,
        duckdb=duck_status,
        timestamp=now,
        uptime_seconds=round(uptime, 1),
    )


# ---------------------------------------------------------------------------
# GET /info
# ---------------------------------------------------------------------------

@router.get(
    "/info",
    response_model=ApiInfo,
    summary="API metadata, endpoint listing, and data source statistics",
)
async def api_info(
    conn: psycopg.AsyncConnection = Depends(get_pg_conn),
    duck: duckdb.DuckDBPyConnection = Depends(get_duckdb_conn),
) -> ApiInfo:
    """Return API metadata and data-source statistics.

    Queries both PostgreSQL and DuckDB for row counts. Any query failure
    is caught and reported as -1 rather than crashing the endpoint.

    Args:
        conn: Injected async PostgreSQL connection.
        duck: Injected DuckDB connection.

    Returns:
        ApiInfo with version, endpoint list, and source stats.
    """
    # PostgreSQL stats
    pg_price_count = await _pg_count(conn, "SELECT COUNT(*) FROM warehouse.fact_oil_prices")
    pg_commodity_count = await _pg_count(
        conn, "SELECT COUNT(*) FROM warehouse.dim_commodity WHERE is_current = TRUE"
    )

    # DuckDB gold-layer row counts
    duck_monthly = _duck_count(duck, "SELECT COUNT(*) FROM monthly_summary")
    duck_metrics = _duck_count(duck, "SELECT COUNT(*) FROM price_metrics")
    duck_comparison = _duck_count(duck, "SELECT COUNT(*) FROM commodity_comparison")

    gold_path = (Path(settings.lakehouse_base_path) / "data" / "gold").as_posix()

    data_sources: dict[str, Any] = {
        "postgresql": {
            "host": settings.pg_host,
            "port": settings.pg_port,
            "database": settings.pg_database,
            "user": settings.pg_user,
            "fact_oil_prices_rows": pg_price_count,
            "active_commodities": pg_commodity_count,
        },
        "duckdb_lakehouse": {
            "gold_path": gold_path,
            "monthly_summary_rows": duck_monthly,
            "price_metrics_rows": duck_metrics,
            "commodity_comparison_rows": duck_comparison,
        },
    }

    endpoints = [
        {
            "method": "GET",
            "path": f"{settings.api_prefix}/prices/latest",
            "description": "Latest price per commodity (PostgreSQL)",
            "backend": "postgresql",
        },
        {
            "method": "GET",
            "path": f"{settings.api_prefix}/prices/history",
            "description": "Historical OHLCV data with date range filter (PostgreSQL)",
            "backend": "postgresql",
        },
        {
            "method": "GET",
            "path": f"{settings.api_prefix}/prices/commodities",
            "description": "Active commodity dimension records (PostgreSQL)",
            "backend": "postgresql",
        },
        {
            "method": "GET",
            "path": f"{settings.api_prefix}/analytics/monthly-summary",
            "description": "Monthly price aggregations (DuckDB gold layer)",
            "backend": "duckdb",
        },
        {
            "method": "GET",
            "path": f"{settings.api_prefix}/analytics/price-metrics",
            "description": "Rolling MAs, volatility, Bollinger bands (DuckDB gold layer)",
            "backend": "duckdb",
        },
        {
            "method": "GET",
            "path": f"{settings.api_prefix}/analytics/commodity-comparison",
            "description": "WTI vs Brent spread and ratio (DuckDB gold layer)",
            "backend": "duckdb",
        },
        {
            "method": "GET",
            "path": f"{settings.api_prefix}/health",
            "description": "Service health check",
            "backend": "both",
        },
        {
            "method": "GET",
            "path": f"{settings.api_prefix}/info",
            "description": "API metadata and source statistics",
            "backend": "both",
        },
    ]

    return ApiInfo(
        api_version=settings.api_version,
        title=settings.api_title,
        description=settings.api_description,
        data_sources=data_sources,
        endpoints=endpoints,
    )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

async def _pg_count(conn: psycopg.AsyncConnection, sql: str) -> int:
    """Execute a COUNT query against PostgreSQL and return the integer result.

    Args:
        conn: Open async connection.
        sql: A SELECT COUNT(*) query string (no parameters).

    Returns:
        Row count, or -1 on error.
    """
    try:
        async with conn.cursor() as cur:
            await cur.execute(sql)
            row = await cur.fetchone()
            return int(row[0]) if row else 0
    except Exception as exc:
        logger.warning("PostgreSQL count query failed: %s", exc)
        return -1


def _duck_count(conn: duckdb.DuckDBPyConnection, sql: str) -> int:
    """Execute a COUNT query against DuckDB and return the integer result.

    Args:
        conn: Open DuckDB connection.
        sql: A SELECT COUNT(*) query string.

    Returns:
        Row count, or -1 on error.
    """
    try:
        row = conn.execute(sql).fetchone()
        return int(row[0]) if row else 0
    except Exception as exc:
        logger.warning("DuckDB count query failed: %s", exc)
        return -1
