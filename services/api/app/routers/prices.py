"""
Prices router — operational queries against the PostgreSQL warehouse.

All endpoints in this module use async psycopg v3 connections from the pool.
"""

from __future__ import annotations

import logging
import time
from datetime import date, timedelta
from decimal import Decimal
from typing import Annotated, Any

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg.rows import dict_row

from app.dependencies import get_pg_conn
from app.models.requests import DEFAULT_LIMIT, MAX_LIMIT, VALID_COMMODITIES
from app.models.responses import ApiResponse, CommodityRecord, MetaInfo, PriceRecord

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Prices (PostgreSQL)"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _to_float(value: Any) -> float | None:
    """Convert Decimal or None to plain float.

    psycopg v3 returns NUMERIC columns as Python Decimal objects.
    Pydantic and FastAPI's JSON encoder need plain float.

    Args:
        value: Value from a database row dict.

    Returns:
        Plain float, or None if value is None.
    """
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def _validate_commodity(commodity: str | None) -> None:
    """Raise 422 if the provided commodity symbol is not in the allowed list.

    Args:
        commodity: Ticker symbol to validate, or None to skip validation.

    Raises:
        HTTPException: 422 if the symbol is not recognised.
    """
    if commodity is not None and commodity not in VALID_COMMODITIES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid commodity '{commodity}'. Must be one of: {VALID_COMMODITIES}",
        )


def _row_to_price(row: dict[str, Any]) -> PriceRecord:
    """Build a PriceRecord from a warehouse query result dict.

    Args:
        row: dict_row result from psycopg cursor.

    Returns:
        PriceRecord with all numeric fields converted to plain float.
    """
    return PriceRecord(
        date=row["full_date"],
        commodity_id=row["commodity_id"],
        commodity_name=row["commodity_name"],
        price_open=_to_float(row.get("price_open")),
        price_high=_to_float(row.get("price_high")),
        price_low=_to_float(row.get("price_low")),
        price_close=_to_float(row["price_close"]),
        adj_close=_to_float(row.get("adj_close")),
        volume=int(row["volume"]) if row.get("volume") is not None else None,
        daily_change=_to_float(row.get("daily_change")),
        daily_change_pct=_to_float(row.get("daily_change_pct")),
    )


# ---------------------------------------------------------------------------
# GET /latest
# ---------------------------------------------------------------------------


@router.get(
    "/latest",
    response_model=ApiResponse,
    summary="Latest price for each commodity (or N most recent for one)",
    description=(
        "With no `commodity` filter: returns the single most recent record for each "
        "of the 4 commodities. With a `commodity` filter: returns the `limit` most "
        "recent records for that symbol."
    ),
)
async def get_latest_prices(
    commodity: Annotated[
        str | None,
        Query(description=f"Ticker symbol. One of: {VALID_COMMODITIES}"),
    ] = None,
    limit: Annotated[
        int,
        Query(ge=1, le=50, description="Max records to return when filtering by commodity"),
    ] = 4,
    conn: psycopg.AsyncConnection = Depends(get_pg_conn),
) -> ApiResponse:
    """Return the latest price record(s) from the warehouse.

    Args:
        commodity: Optional ticker filter.
        limit: Max rows when filtering by commodity (ignored for all-commodities query).
        conn: Injected async PostgreSQL connection.

    Returns:
        ApiResponse wrapping a list of PriceRecord.
    """
    _validate_commodity(commodity)
    t0 = time.perf_counter()

    if commodity is None:
        # One latest row per commodity using DISTINCT ON.
        sql = """
        SELECT DISTINCT ON (dc.commodity_id)
            dd.full_date,
            dc.commodity_id,
            dc.commodity_name,
            f.price_open,
            f.price_high,
            f.price_low,
            f.price_close,
            f.adj_close,
            f.volume,
            f.daily_change,
            f.daily_change_pct
        FROM warehouse.fact_oil_prices f
        JOIN warehouse.dim_commodity dc ON f.commodity_key = dc.commodity_key
        JOIN warehouse.dim_date dd ON f.date_key = dd.date_key
        WHERE dc.is_current = TRUE
        ORDER BY dc.commodity_id, dd.full_date DESC
        """
        params: dict[str, Any] = {}
    else:
        # N most-recent rows for a single commodity.
        sql = """
        SELECT
            dd.full_date,
            dc.commodity_id,
            dc.commodity_name,
            f.price_open,
            f.price_high,
            f.price_low,
            f.price_close,
            f.adj_close,
            f.volume,
            f.daily_change,
            f.daily_change_pct
        FROM warehouse.fact_oil_prices f
        JOIN warehouse.dim_commodity dc ON f.commodity_key = dc.commodity_key
        JOIN warehouse.dim_date dd ON f.date_key = dd.date_key
        WHERE dc.is_current = TRUE
          AND dc.commodity_id = %(commodity)s
        ORDER BY dd.full_date DESC
        LIMIT %(limit)s
        """
        params = {"commodity": commodity, "limit": limit}

    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(sql, params)
        rows = await cur.fetchall()

    query_ms = (time.perf_counter() - t0) * 1000
    records = [_row_to_price(r) for r in rows]

    return ApiResponse(
        data=records,
        meta=MetaInfo(count=len(records), source="postgresql", query_time_ms=round(query_ms, 2)),
    )


# ---------------------------------------------------------------------------
# GET /history
# ---------------------------------------------------------------------------


@router.get(
    "/history",
    response_model=ApiResponse,
    summary="Historical price data with optional date range and commodity filter",
)
async def get_price_history(
    commodity: Annotated[
        str | None,
        Query(description=f"Ticker symbol. One of: {VALID_COMMODITIES}"),
    ] = None,
    start_date: Annotated[
        date | None,
        Query(description="Inclusive start date (YYYY-MM-DD). Defaults to 30 days ago."),
    ] = None,
    end_date: Annotated[
        date | None,
        Query(description="Inclusive end date (YYYY-MM-DD). Defaults to today."),
    ] = None,
    limit: Annotated[
        int,
        Query(ge=1, le=MAX_LIMIT, description="Maximum number of rows to return"),
    ] = DEFAULT_LIMIT,
    offset: Annotated[
        int,
        Query(ge=0, description="Number of rows to skip (for pagination)"),
    ] = 0,
    conn: psycopg.AsyncConnection = Depends(get_pg_conn),
) -> ApiResponse:
    """Return historical OHLCV price data.

    Args:
        commodity: Optional ticker filter.
        start_date: Lower date bound (defaults to 30 days ago).
        end_date: Upper date bound (defaults to today).
        limit: Max rows returned.
        offset: Pagination offset.
        conn: Injected async PostgreSQL connection.

    Returns:
        ApiResponse wrapping a list of PriceRecord.
    """
    _validate_commodity(commodity)

    effective_start = start_date or (date.today() - timedelta(days=30))
    effective_end = end_date or date.today()

    if effective_start > effective_end:
        raise HTTPException(
            status_code=422,
            detail="start_date must not be after end_date.",
        )

    t0 = time.perf_counter()

    # Build parameterized WHERE clause — never string-format user input into SQL.
    conditions = [
        "dc.is_current = TRUE",
        "dd.full_date >= %(start_date)s",
        "dd.full_date <= %(end_date)s",
    ]
    params: dict[str, Any] = {
        "start_date": effective_start,
        "end_date": effective_end,
        "limit": limit,
        "offset": offset,
    }

    if commodity is not None:
        conditions.append("dc.commodity_id = %(commodity)s")
        params["commodity"] = commodity

    where_clause = " AND ".join(conditions)

    sql = f"""
    SELECT
        dd.full_date,
        dc.commodity_id,
        dc.commodity_name,
        f.price_open,
        f.price_high,
        f.price_low,
        f.price_close,
        f.adj_close,
        f.volume,
        f.daily_change,
        f.daily_change_pct
    FROM warehouse.fact_oil_prices f
    JOIN warehouse.dim_commodity dc ON f.commodity_key = dc.commodity_key
    JOIN warehouse.dim_date dd ON f.date_key = dd.date_key
    WHERE {where_clause}
    ORDER BY dd.full_date DESC, dc.commodity_id
    LIMIT %(limit)s OFFSET %(offset)s
    """

    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(sql, params)
        rows = await cur.fetchall()

    query_ms = (time.perf_counter() - t0) * 1000
    records = [_row_to_price(r) for r in rows]

    return ApiResponse(
        data=records,
        meta=MetaInfo(count=len(records), source="postgresql", query_time_ms=round(query_ms, 2)),
    )


# ---------------------------------------------------------------------------
# GET /commodities
# ---------------------------------------------------------------------------


@router.get(
    "/commodities",
    response_model=ApiResponse,
    summary="List all active commodities from the dimension table",
)
async def get_commodities(
    conn: psycopg.AsyncConnection = Depends(get_pg_conn),
) -> ApiResponse:
    """Return all current commodity records from dim_commodity.

    Args:
        conn: Injected async PostgreSQL connection.

    Returns:
        ApiResponse wrapping a list of CommodityRecord.
    """
    t0 = time.perf_counter()

    sql = """
    SELECT
        commodity_id,
        commodity_name,
        category,
        sub_category,
        currency,
        exchange,
        unit_of_measure
    FROM warehouse.dim_commodity
    WHERE is_current = TRUE
    ORDER BY commodity_id
    """

    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(sql)
        rows = await cur.fetchall()

    query_ms = (time.perf_counter() - t0) * 1000
    records = [CommodityRecord(**row) for row in rows]

    return ApiResponse(
        data=records,
        meta=MetaInfo(count=len(records), source="postgresql", query_time_ms=round(query_ms, 2)),
    )
