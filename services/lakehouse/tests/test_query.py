"""
Tests for the DuckDB query engine.

Writes sample Parquet files to a temporary directory and verifies
that the engine's query methods work correctly.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from src.config import Settings
from src.query.duckdb_engine import DuckDBEngine


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def config(tmp_path: Path) -> Settings:
    return Settings(
        DB_HOST="localhost",
        DB_PORT=5432,
        DB_NAME="oil_warehouse",
        DB_USER="arash",
        DB_PASSWORD="warehouse_dev_2026",
        DATA_DIR=str(tmp_path),
    )


def _write_curated_parquet(config: Settings) -> None:
    """Write minimal curated Parquet partitions for testing."""
    rows = [
        {
            "price_key": 1,
            "symbol": "CL=F",
            "commodity_name": "WTI Crude Oil",
            "commodity_type": "energy",
            "trade_date": date(2024, 1, 2),
            "year": 2024,
            "month": 1,
            "day": 2,
            "quarter": 1,
            "is_trading_day": True,
            "open": 70.0,
            "high": 73.0,
            "low": 69.0,
            "close": 71.0,
            "adj_close": 71.0,
            "volume": 1000000,
            "daily_change": 1.0,
            "daily_change_pct": 1.43,
            "daily_return_pct": None,
            "source": "Yahoo Finance",
            "quality_flag": "valid",
        },
        {
            "price_key": 2,
            "symbol": "CL=F",
            "commodity_name": "WTI Crude Oil",
            "commodity_type": "energy",
            "trade_date": date(2024, 1, 3),
            "year": 2024,
            "month": 1,
            "day": 3,
            "quarter": 1,
            "is_trading_day": True,
            "open": 71.0,
            "high": 74.0,
            "low": 70.0,
            "close": 72.0,
            "adj_close": 72.0,
            "volume": 1100000,
            "daily_change": 1.0,
            "daily_change_pct": 1.41,
            "daily_return_pct": 0.014085,
            "source": "Yahoo Finance",
            "quality_flag": "valid",
        },
        {
            "price_key": 3,
            "symbol": "BZ=F",
            "commodity_name": "Brent Crude Oil",
            "commodity_type": "energy",
            "trade_date": date(2024, 1, 2),
            "year": 2024,
            "month": 1,
            "day": 2,
            "quarter": 1,
            "is_trading_day": True,
            "open": 75.0,
            "high": 78.0,
            "low": 74.0,
            "close": 76.0,
            "adj_close": 76.0,
            "volume": 900000,
            "daily_change": 0.5,
            "daily_change_pct": 0.66,
            "daily_return_pct": None,
            "source": "Yahoo Finance",
            "quality_flag": "valid",
        },
    ]
    df = pd.DataFrame(rows)
    out_dir = config.curated_path / "year=2024" / "month=1"
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_dir / "data.parquet", index=False)


def _write_serving_parquet(config: Settings) -> None:
    """Write minimal serving Parquet files for testing."""
    ms_dir = config.serving_path / "monthly_summary"
    ms_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([{
        "symbol": "CL=F",
        "commodity_name": "WTI Crude Oil",
        "year": 2024,
        "month": 1,
        "trading_days": 2,
        "avg_close": 71.5,
        "min_close": 71.0,
        "max_close": 72.0,
        "stddev_close": 0.707,
        "total_volume": 2100000,
        "monthly_return_pct": 1.41,
    }]).to_parquet(ms_dir / "data.parquet", index=False)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestArbitraryQuery:
    """DuckDBEngine.query() should execute arbitrary SQL."""

    def test_query_returns_dataframe(self, config: Settings) -> None:
        _write_curated_parquet(config)
        engine = DuckDBEngine(config)
        df = engine.query("SELECT COUNT(*) AS n FROM curated")
        engine.close()
        assert "n" in df.columns
        assert df.iloc[0]["n"] == 3

    def test_query_invalid_sql_returns_empty(self, config: Settings) -> None:
        engine = DuckDBEngine(config)
        df = engine.query("SELECT * FROM nonexistent_table_xyz")
        engine.close()
        assert df.empty


class TestGetPriceHistory:
    """get_price_history should filter by commodity and date range."""

    def test_filters_by_symbol(self, config: Settings) -> None:
        _write_curated_parquet(config)
        engine = DuckDBEngine(config)
        df = engine.get_price_history("CL=F", date(2024, 1, 1), date(2024, 1, 31))
        engine.close()
        assert len(df) == 2

    def test_filters_by_date_range(self, config: Settings) -> None:
        _write_curated_parquet(config)
        engine = DuckDBEngine(config)
        df = engine.get_price_history("CL=F", date(2024, 1, 3), date(2024, 1, 31))
        engine.close()
        assert len(df) == 1

    def test_unknown_symbol_returns_empty(self, config: Settings) -> None:
        _write_curated_parquet(config)
        engine = DuckDBEngine(config)
        df = engine.get_price_history("XX=F", date(2024, 1, 1), date(2024, 1, 31))
        engine.close()
        assert df.empty


class TestGetMonthlySummary:
    """get_monthly_summary should read from the serving layer."""

    def test_returns_data_when_serving_exists(self, config: Settings) -> None:
        _write_serving_parquet(config)
        engine = DuckDBEngine(config)
        df = engine.get_monthly_summary()
        engine.close()
        assert len(df) >= 1

    def test_filters_by_year(self, config: Settings) -> None:
        _write_serving_parquet(config)
        engine = DuckDBEngine(config)
        df = engine.get_monthly_summary(year=2024)
        engine.close()
        assert all(df["year"] == 2024)

    def test_no_serving_data_returns_empty(self, config: Settings) -> None:
        engine = DuckDBEngine(config)
        df = engine.get_monthly_summary()
        engine.close()
        assert df.empty


class TestLayerStats:
    """layer_stats should return row counts and sizes for all layers."""

    def test_returns_all_layers(self, config: Settings) -> None:
        engine = DuckDBEngine(config)
        stats = engine.layer_stats()
        engine.close()
        expected_keys = {
            "raw", "curated",
            "serving/monthly_summary",
            "serving/price_metrics",
            "serving/commodity_comparison",
        }
        assert expected_keys.issubset(set(stats.keys()))

    def test_empty_layers_have_zero_rows(self, config: Settings) -> None:
        engine = DuckDBEngine(config)
        stats = engine.layer_stats()
        engine.close()
        assert stats["raw"]["rows"] == 0
        assert stats["curated"]["rows"] == 0

    def test_populated_curated_shows_correct_count(self, config: Settings) -> None:
        _write_curated_parquet(config)
        engine = DuckDBEngine(config)
        stats = engine.layer_stats()
        engine.close()
        assert stats["curated"]["rows"] == 3
