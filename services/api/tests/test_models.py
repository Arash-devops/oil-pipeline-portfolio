"""Unit tests for Pydantic response models."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from app.models.responses import (
    ApiInfo,
    ApiResponse,
    CommodityComparisonRecord,
    CommodityRecord,
    HealthCheck,
    MetaInfo,
    MonthlySummaryRecord,
    PriceMetricsRecord,
    PriceRecord,
)

# ---------------------------------------------------------------------------
# ApiResponse / MetaInfo
# ---------------------------------------------------------------------------


def test_api_response_default_status() -> None:
    meta = MetaInfo(count=0, source="postgresql", query_time_ms=1.0)
    r = ApiResponse(data=[], meta=meta)
    assert r.status == "success"


def test_api_response_wraps_data() -> None:
    meta = MetaInfo(count=2, source="duckdb", query_time_ms=5.0)
    r = ApiResponse(data=[{"a": 1}, {"b": 2}], meta=meta)
    assert len(r.data) == 2
    assert r.meta.count == 2


# ---------------------------------------------------------------------------
# PriceRecord
# ---------------------------------------------------------------------------


def test_price_record_required_fields() -> None:
    r = PriceRecord(
        date=date(2024, 1, 15),
        commodity_id="CL=F",
        commodity_name="Crude Oil WTI",
        price_close=75.5,
    )
    assert r.price_close == 75.5


def test_price_record_optional_fields_default_none() -> None:
    r = PriceRecord(
        date=date(2024, 1, 15),
        commodity_id="CL=F",
        commodity_name="Crude Oil WTI",
        price_close=75.5,
    )
    assert r.price_open is None
    assert r.price_high is None
    assert r.volume is None
    assert r.daily_change_pct is None


# ---------------------------------------------------------------------------
# CommodityRecord
# ---------------------------------------------------------------------------


def test_commodity_record_required_fields() -> None:
    r = CommodityRecord(commodity_id="BZ=F", commodity_name="Brent Crude")
    assert r.commodity_id == "BZ=F"
    assert r.category is None


# ---------------------------------------------------------------------------
# MonthlySummaryRecord
# ---------------------------------------------------------------------------


def test_monthly_summary_record_required_fields() -> None:
    r = MonthlySummaryRecord(
        commodity_id="CL=F",
        commodity_name="Crude Oil WTI",
        year=2024,
        month=3,
    )
    assert r.year == 2024
    assert r.avg_close is None


def test_monthly_summary_record_with_values() -> None:
    r = MonthlySummaryRecord(
        commodity_id="CL=F",
        commodity_name="Crude Oil WTI",
        year=2024,
        month=1,
        avg_close=75.0,
        trading_days=20,
    )
    assert r.avg_close == 75.0
    assert r.trading_days == 20


# ---------------------------------------------------------------------------
# PriceMetricsRecord
# ---------------------------------------------------------------------------


def test_price_metrics_record_defaults() -> None:
    r = PriceMetricsRecord(commodity_id="CL=F", date=date(2024, 1, 15))
    assert r.ma_7 is None
    assert r.volatility_20d is None
    assert r.bollinger_upper is None


def test_price_metrics_record_with_values() -> None:
    r = PriceMetricsRecord(
        commodity_id="CL=F",
        date=date(2024, 1, 15),
        close=75.5,
        ma_7=74.0,
        ma_30=73.5,
    )
    assert r.close == 75.5
    assert r.ma_7 == 74.0


# ---------------------------------------------------------------------------
# CommodityComparisonRecord
# ---------------------------------------------------------------------------


def test_commodity_comparison_record_defaults() -> None:
    r = CommodityComparisonRecord(date=date(2024, 1, 15))
    assert r.wti_close is None
    assert r.spread is None


def test_commodity_comparison_record_with_values() -> None:
    r = CommodityComparisonRecord(
        date=date(2024, 1, 15),
        wti_close=75.5,
        brent_close=76.0,
        spread=-0.5,
        ratio=0.993,
    )
    assert r.spread == pytest.approx(-0.5)


# ---------------------------------------------------------------------------
# HealthCheck
# ---------------------------------------------------------------------------


def test_health_check_model() -> None:
    r = HealthCheck(
        status="healthy",
        postgresql="healthy",
        duckdb="healthy",
        timestamp=datetime.now(UTC),
        uptime_seconds=42.0,
    )
    assert r.status == "healthy"
    assert r.uptime_seconds == 42.0


def test_health_check_degraded_status() -> None:
    r = HealthCheck(
        status="degraded",
        postgresql="unhealthy",
        duckdb="healthy",
        timestamp=datetime.now(UTC),
        uptime_seconds=5.0,
    )
    assert r.postgresql == "unhealthy"


# ---------------------------------------------------------------------------
# ApiInfo
# ---------------------------------------------------------------------------


def test_api_info_model() -> None:
    r = ApiInfo(
        api_version="1.0.0",
        title="Test API",
        description="desc",
        data_sources={"pg": {"rows": 100}},
        endpoints=[{"method": "GET", "path": "/health", "description": "health", "backend": "both"}],
    )
    assert r.api_version == "1.0.0"
    assert len(r.endpoints) == 1
