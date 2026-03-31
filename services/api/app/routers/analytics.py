"""
Analytics router — pre-aggregated queries against the DuckDB gold layer.

All endpoints are defined as regular `def` (not async) because DuckDB is
synchronous. FastAPI automatically runs sync endpoints in a thread pool.
"""

from __future__ import annotations

import logging
import math
import time
from datetime import date
from typing import Annotated, Any

import duckdb
from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import get_duckdb_conn
from app.models.requests import MAX_LIMIT, VALID_COMMODITIES
from app.models.responses import (
    ApiResponse,
    CommodityComparisonRecord,
    MetaInfo,
    MonthlySummaryRecord,
    PriceMetricsRecord,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Analytics (DuckDB/Lakehouse)"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _clean(value: Any) -> Any:
    """Replace NaN floats with None for JSON compatibility.

    DuckDB may return float('nan') for NULL numeric fields. pydantic/JSON
    cannot serialise NaN, so we normalise to None.

    Args:
        value: Any value from a DuckDB result row.

    Returns:
        None if value is NaN, otherwise the original value.
    """
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def _rows_to_dicts(
    conn: duckdb.DuckDBPyConnection,
    sql: str,
    params: list[Any] | None = None,
) -> tuple[list[dict[str, Any]], float]:
    """Execute a DuckDB query and return rows as dicts plus elapsed milliseconds.

    Uses conn.description (available after execute) to map column names.

    Args:
        conn: Open DuckDB connection with gold views registered.
        sql: SQL query string with positional $1, $2, ... placeholders.
        params: Optional list of positional parameters.

    Returns:
        Tuple of (list of row dicts, query_time_ms).
    """
    t0 = time.perf_counter()
    result = conn.execute(sql, params or [])
    raw_rows = result.fetchall()
    col_names = [desc[0] for desc in result.description]
    query_ms = (time.perf_counter() - t0) * 1000

    rows = [{col: _clean(val) for col, val in zip(col_names, row, strict=False)} for row in raw_rows]
    return rows, query_ms


def _validate_commodity(commodity: str | None) -> None:
    """Raise 422 if the commodity symbol is not in the allowed list.

    Args:
        commodity: Symbol to validate, or None to skip.

    Raises:
        HTTPException: 422 if unrecognised.
    """
    if commodity is not None and commodity not in VALID_COMMODITIES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid commodity '{commodity}'. Must be one of: {VALID_COMMODITIES}",
        )


# ---------------------------------------------------------------------------
# GET /monthly-summary
# ---------------------------------------------------------------------------


@router.get(
    "/monthly-summary",
    response_model=ApiResponse,
    summary="Monthly price aggregations per commodity from the gold layer",
    description=(
        "Pre-aggregated monthly statistics: avg/min/max close, stddev, total volume, "
        "and monthly return percentage. Data comes from the DuckDB/Parquet gold layer."
    ),
)
def get_monthly_summary(
    commodity: Annotated[
        str | None,
        Query(description=f"Filter by ticker symbol. One of: {VALID_COMMODITIES}"),
    ] = None,
    year: Annotated[
        int | None,
        Query(ge=2000, le=2100, description="Filter by calendar year"),
    ] = None,
    limit: Annotated[
        int,
        Query(ge=1, le=500, description="Maximum rows to return"),
    ] = 100,
    conn: duckdb.DuckDBPyConnection = Depends(get_duckdb_conn),
) -> ApiResponse:
    """Return monthly price summaries from the gold-layer Parquet file.

    Args:
        commodity: Optional commodity symbol filter.
        year: Optional year filter.
        limit: Max rows returned.
        conn: Injected DuckDB connection with gold views.

    Returns:
        ApiResponse wrapping a list of MonthlySummaryRecord.
    """
    _validate_commodity(commodity)

    conditions: list[str] = []
    params: list[Any] = []

    if commodity is not None:
        conditions.append("symbol = $" + str(len(params) + 1))
        params.append(commodity)

    if year is not None:
        conditions.append("year = $" + str(len(params) + 1))
        params.append(year)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    params.append(limit)

    sql = f"""
    SELECT
        symbol          AS commodity_id,
        commodity_name,
        year,
        month,
        trading_days,
        avg_close,
        min_close,
        max_close,
        stddev_close,
        total_volume,
        monthly_return_pct
    FROM monthly_summary
    {where}
    ORDER BY year DESC, month DESC
    LIMIT ${len(params)}
    """

    try:
        rows, query_ms = _rows_to_dicts(conn, sql, params)
    except Exception as exc:
        logger.error("monthly-summary query failed: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to query gold layer.") from exc

    records = [MonthlySummaryRecord(**row) for row in rows]

    return ApiResponse(
        data=records,
        meta=MetaInfo(count=len(records), source="duckdb", query_time_ms=round(query_ms, 2)),
    )


# ---------------------------------------------------------------------------
# GET /price-metrics
# ---------------------------------------------------------------------------


@router.get(
    "/price-metrics",
    response_model=ApiResponse,
    summary="Rolling price metrics (moving averages, volatility, Bollinger bands)",
    description=(
        "Daily 7/30/90-day moving averages, 20-day rolling volatility, and "
        "Bollinger band upper/lower bounds per commodity. Gold layer source."
    ),
)
def get_price_metrics(
    commodity: Annotated[
        str | None,
        Query(description=f"Filter by ticker symbol. One of: {VALID_COMMODITIES}"),
    ] = None,
    start_date: Annotated[
        date | None,
        Query(description="Inclusive start date (YYYY-MM-DD)"),
    ] = None,
    end_date: Annotated[
        date | None,
        Query(description="Inclusive end date (YYYY-MM-DD)"),
    ] = None,
    limit: Annotated[
        int,
        Query(ge=1, le=MAX_LIMIT, description="Maximum rows to return"),
    ] = 100,
    conn: duckdb.DuckDBPyConnection = Depends(get_duckdb_conn),
) -> ApiResponse:
    """Return rolling price metrics from the gold-layer Parquet file.

    Args:
        commodity: Optional commodity symbol filter.
        start_date: Optional lower date bound.
        end_date: Optional upper date bound.
        limit: Max rows returned.
        conn: Injected DuckDB connection with gold views.

    Returns:
        ApiResponse wrapping a list of PriceMetricsRecord.
    """
    _validate_commodity(commodity)

    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=422,
            detail="start_date must not be after end_date.",
        )

    conditions: list[str] = []
    params: list[Any] = []

    if commodity is not None:
        conditions.append("symbol = $" + str(len(params) + 1))
        params.append(commodity)

    if start_date is not None:
        conditions.append("trade_date >= $" + str(len(params) + 1))
        params.append(start_date.isoformat())

    if end_date is not None:
        conditions.append("trade_date <= $" + str(len(params) + 1))
        params.append(end_date.isoformat())

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    params.append(limit)

    sql = f"""
    SELECT
        symbol          AS commodity_id,
        trade_date      AS date,
        close,
        ma7             AS ma_7,
        ma30            AS ma_30,
        ma90            AS ma_90,
        volatility_20d,
        bollinger_upper,
        bollinger_lower
    FROM price_metrics
    {where}
    ORDER BY trade_date DESC
    LIMIT ${len(params)}
    """

    try:
        rows, query_ms = _rows_to_dicts(conn, sql, params)
    except Exception as exc:
        logger.error("price-metrics query failed: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to query gold layer.") from exc

    records = [PriceMetricsRecord(**row) for row in rows]

    return ApiResponse(
        data=records,
        meta=MetaInfo(count=len(records), source="duckdb", query_time_ms=round(query_ms, 2)),
    )


# ---------------------------------------------------------------------------
# GET /commodity-comparison
# ---------------------------------------------------------------------------


@router.get(
    "/commodity-comparison",
    response_model=ApiResponse,
    summary="WTI vs Brent daily spread and price ratio",
    description=(
        "Daily WTI crude oil (CL=F) vs Brent crude (BZ=F) spread (WTI minus Brent) "
        "and price ratio (WTI / Brent). Sourced from the DuckDB gold layer."
    ),
)
def get_commodity_comparison(
    start_date: Annotated[
        date | None,
        Query(description="Inclusive start date (YYYY-MM-DD)"),
    ] = None,
    end_date: Annotated[
        date | None,
        Query(description="Inclusive end date (YYYY-MM-DD)"),
    ] = None,
    limit: Annotated[
        int,
        Query(ge=1, le=MAX_LIMIT, description="Maximum rows to return"),
    ] = 100,
    conn: duckdb.DuckDBPyConnection = Depends(get_duckdb_conn),
) -> ApiResponse:
    """Return WTI vs Brent price comparison from the gold-layer Parquet file.

    Args:
        start_date: Optional lower date bound.
        end_date: Optional upper date bound.
        limit: Max rows returned.
        conn: Injected DuckDB connection with gold views.

    Returns:
        ApiResponse wrapping a list of CommodityComparisonRecord.
    """
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=422,
            detail="start_date must not be after end_date.",
        )

    conditions: list[str] = []
    params: list[Any] = []

    if start_date is not None:
        conditions.append("trade_date >= $" + str(len(params) + 1))
        params.append(start_date.isoformat())

    if end_date is not None:
        conditions.append("trade_date <= $" + str(len(params) + 1))
        params.append(end_date.isoformat())

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    params.append(limit)

    sql = f"""
    SELECT
        trade_date  AS date,
        wti_close,
        brent_close,
        spread,
        ratio
    FROM commodity_comparison
    {where}
    ORDER BY trade_date DESC
    LIMIT ${len(params)}
    """

    try:
        rows, query_ms = _rows_to_dicts(conn, sql, params)
    except Exception as exc:
        logger.error("commodity-comparison query failed: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to query gold layer.") from exc

    records = [CommodityComparisonRecord(**row) for row in rows]

    return ApiResponse(
        data=records,
        meta=MetaInfo(count=len(records), source="duckdb", query_time_ms=round(query_ms, 2)),
    )
