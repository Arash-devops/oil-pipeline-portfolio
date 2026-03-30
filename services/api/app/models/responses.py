"""
Pydantic response models for the Oil Price API.

All API responses are wrapped in ApiResponse except health/info endpoints,
which return their models directly.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Envelope
# ---------------------------------------------------------------------------

class MetaInfo(BaseModel):
    """Metadata attached to every list-style API response."""

    count: int = Field(description="Number of records returned")
    source: str = Field(description="Data source: 'postgresql' or 'duckdb'")
    query_time_ms: float = Field(description="Query execution time in milliseconds")


class ApiResponse(BaseModel):
    """Standard envelope for all list API responses."""

    status: str = Field(default="success", description="Response status")
    data: list[Any] = Field(description="Response payload")
    meta: MetaInfo


# ---------------------------------------------------------------------------
# Price models — PostgreSQL
# ---------------------------------------------------------------------------

class PriceRecord(BaseModel):
    """Single OHLCV price record from the warehouse."""

    date: date
    commodity_id: str
    commodity_name: str
    price_open: float | None = None
    price_high: float | None = None
    price_low: float | None = None
    price_close: float
    adj_close: float | None = None
    volume: int | None = None
    daily_change: float | None = None
    daily_change_pct: float | None = None


class CommodityRecord(BaseModel):
    """Commodity dimension record from dim_commodity."""

    commodity_id: str
    commodity_name: str
    category: str | None = None
    sub_category: str | None = None
    currency: str | None = None
    exchange: str | None = None
    unit_of_measure: str | None = None


# ---------------------------------------------------------------------------
# Analytics models — DuckDB / gold layer
# ---------------------------------------------------------------------------

class MonthlySummaryRecord(BaseModel):
    """Monthly price aggregation from the gold layer."""

    commodity_id: str
    commodity_name: str
    year: int
    month: int
    avg_close: float | None = None
    min_close: float | None = None
    max_close: float | None = None
    stddev_close: float | None = None
    total_volume: int | None = None
    monthly_return_pct: float | None = None
    trading_days: int | None = None


class PriceMetricsRecord(BaseModel):
    """Rolling price metrics (moving averages, Bollinger bands) from gold layer."""

    commodity_id: str
    date: date
    close: float | None = None
    ma_7: float | None = None
    ma_30: float | None = None
    ma_90: float | None = None
    volatility_20d: float | None = None
    bollinger_upper: float | None = None
    bollinger_lower: float | None = None


class CommodityComparisonRecord(BaseModel):
    """WTI vs Brent daily spread and ratio from the gold layer."""

    date: date
    wti_close: float | None = None
    brent_close: float | None = None
    spread: float | None = None
    ratio: float | None = None


# ---------------------------------------------------------------------------
# Health / Info models
# ---------------------------------------------------------------------------

class HealthCheck(BaseModel):
    """Service health status returned by GET /health."""

    status: str
    postgresql: str
    duckdb: str
    timestamp: datetime
    uptime_seconds: float


class ApiInfo(BaseModel):
    """API metadata and data source information returned by GET /info."""

    api_version: str
    title: str
    description: str
    data_sources: dict[str, Any]
    endpoints: list[dict[str, str]]
