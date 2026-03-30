"""
Tests for the silver layer SilverTransformer.

Uses real Parquet files written to a temporary directory.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from src.config import Settings
from src.transformer.silver_transformer import SilverTransformer


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


def _write_raw_partition(config: Settings, rows: list[dict], year: int, month: int) -> None:
    """Write a list of row dicts as a raw Parquet partition."""
    df = pd.DataFrame(rows)
    out_dir = config.raw_path / f"year={year}" / f"month={month}"
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_dir / "data.parquet", index=False)


def _base_row(
    symbol: str = "CL=F",
    trade_date: date = date(2024, 1, 2),
    close: float = 71.0,
    high: float = 73.0,
    low: float = 69.0,
    year: int = 2024,
    month: int = 1,
) -> dict:
    return {
        "price_key": 1,
        "symbol": symbol,
        "commodity_name": "WTI Crude Oil",
        "commodity_type": "energy",
        "trade_date": trade_date,
        "year": year,
        "month": month,
        "day": trade_date.day,
        "quarter": 1,
        "day_of_week": "Tuesday",
        "is_trading_day": True,
        "open": 70.0,
        "high": high,
        "low": low,
        "close": close,
        "adj_close": close,
        "volume": 1000000,
        "daily_change": 1.0,
        "daily_change_pct": 1.43,
        "source": "Yahoo Finance",
        "created_at": pd.Timestamp("2024-01-02 10:00:00", tz="UTC"),
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestNullRemoval:
    """Rows with null close price must be filtered out."""

    def test_null_close_is_removed(self, config: Settings) -> None:
        row_null = _base_row(close=None)
        row_valid = _base_row(trade_date=date(2024, 1, 3))
        _write_raw_partition(config, [row_null, row_valid], 2024, 1)

        transformer = SilverTransformer(config)
        stats = transformer.transform()

        assert stats["rows_filtered"] >= 1
        assert stats["rows_out"] == 1


class TestPositivePriceFilter:
    """Rows with zero or negative close price must be filtered out."""

    def test_zero_close_is_removed(self, config: Settings) -> None:
        _write_raw_partition(config, [_base_row(close=0.0)], 2024, 1)
        transformer = SilverTransformer(config)
        stats = transformer.transform()
        assert stats["rows_out"] == 0

    def test_negative_close_is_removed(self, config: Settings) -> None:
        _write_raw_partition(config, [_base_row(close=-5.0)], 2024, 1)
        transformer = SilverTransformer(config)
        stats = transformer.transform()
        assert stats["rows_out"] == 0

    def test_positive_close_is_kept(self, config: Settings) -> None:
        _write_raw_partition(config, [_base_row(close=71.0)], 2024, 1)
        transformer = SilverTransformer(config)
        stats = transformer.transform()
        assert stats["rows_out"] == 1


class TestQualityFlagging:
    """Price sanity checks should produce suspect flags, not removal."""

    def test_extreme_price_is_suspect(self, config: Settings) -> None:
        _write_raw_partition(config, [_base_row(close=9999.0)], 2024, 1)
        transformer = SilverTransformer(config)
        transformer.transform()

        curated_file = config.curated_path / "year=2024" / "month=1" / "data.parquet"
        assert curated_file.exists()
        df = pd.read_parquet(curated_file)
        assert df.iloc[0]["quality_flag"] == "suspect"

    def test_normal_price_is_valid(self, config: Settings) -> None:
        _write_raw_partition(config, [_base_row(close=71.0)], 2024, 1)
        transformer = SilverTransformer(config)
        transformer.transform()

        curated_file = config.curated_path / "year=2024" / "month=1" / "data.parquet"
        df = pd.read_parquet(curated_file)
        assert df.iloc[0]["quality_flag"] == "valid"

    def test_high_less_than_low_is_suspect(self, config: Settings) -> None:
        _write_raw_partition(
            config, [_base_row(close=71.0, high=68.0, low=73.0)], 2024, 1
        )
        transformer = SilverTransformer(config)
        transformer.transform()

        curated_file = config.curated_path / "year=2024" / "month=1" / "data.parquet"
        df = pd.read_parquet(curated_file)
        assert df.iloc[0]["quality_flag"] == "suspect"


class TestDailyReturnComputation:
    """daily_return_pct should be computed correctly."""

    def test_return_computed_for_consecutive_days(self, config: Settings) -> None:
        rows = [
            _base_row(trade_date=date(2024, 1, 2), close=100.0),
            _base_row(trade_date=date(2024, 1, 3), close=110.0),
        ]
        _write_raw_partition(config, rows, 2024, 1)
        transformer = SilverTransformer(config)
        transformer.transform()

        curated_file = config.curated_path / "year=2024" / "month=1" / "data.parquet"
        df = pd.read_parquet(curated_file).sort_values("trade_date")
        # First row has no previous day, so NaN
        assert pd.isna(df.iloc[0]["daily_return_pct"]) or df.iloc[0]["daily_return_pct"] != df.iloc[0]["daily_return_pct"]
        # Second row: (110 - 100) / 100 = 0.1
        assert abs(df.iloc[1]["daily_return_pct"] - 0.1) < 1e-4


class TestQualityReport:
    """Quality report Parquet should always be written."""

    def test_quality_report_written(self, config: Settings) -> None:
        _write_raw_partition(config, [_base_row()], 2024, 1)
        transformer = SilverTransformer(config)
        transformer.transform()

        report_path = config.quality_report_path / "report.parquet"
        assert report_path.exists()

    def test_empty_raw_data_writes_nothing(self, config: Settings) -> None:
        transformer = SilverTransformer(config)
        stats = transformer.transform()
        assert stats["rows_in"] == 0
        assert stats["rows_out"] == 0
