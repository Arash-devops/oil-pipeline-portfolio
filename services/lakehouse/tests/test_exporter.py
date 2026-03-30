"""
Tests for the bronze layer PgExporter.

Mocks the PostgreSQL connection pool so no real database is needed.
"""

from __future__ import annotations

import tempfile
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch, contextmanager

import pandas as pd
import pyarrow.parquet as pq
import pytest

from src.config import Settings
from src.exporter.pg_exporter import PgExporter


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def config(tmp_path: Path) -> Settings:
    """Settings pointing to a temporary directory."""
    return Settings(
        DB_HOST="localhost",
        DB_PORT=5432,
        DB_NAME="oil_warehouse",
        DB_USER="arash",
        DB_PASSWORD="warehouse_dev_2026",
        DATA_DIR=str(tmp_path),
    )


def _make_sample_rows() -> list[tuple]:
    """Return a minimal set of fake warehouse rows."""
    return [
        (
            1, "CL=F", "WTI Crude Oil", "energy",
            date(2024, 1, 2), 2024, 1, 2, 1, "Tuesday", True,
            70.0, 72.0, 69.5, 71.0, 71.0, 1000000,
            1.0, 1.43, "Yahoo Finance",
            pd.Timestamp("2024-01-02 10:00:00", tz="UTC"),
        ),
        (
            2, "CL=F", "WTI Crude Oil", "energy",
            date(2024, 1, 3), 2024, 1, 3, 1, "Wednesday", True,
            71.0, 73.0, 70.0, 72.0, 72.0, 1100000,
            1.0, 1.41, "Yahoo Finance",
            pd.Timestamp("2024-01-03 10:00:00", tz="UTC"),
        ),
        (
            3, "BZ=F", "Brent Crude Oil", "energy",
            date(2024, 2, 1), 2024, 2, 1, 1, "Thursday", True,
            75.0, 77.0, 74.0, 76.0, 76.0, 900000,
            0.5, 0.66, "Yahoo Finance",
            pd.Timestamp("2024-02-01 10:00:00", tz="UTC"),
        ),
    ]


def _make_pool_mock(rows: list[tuple]) -> MagicMock:
    """Build a MagicMock pool that returns *rows* from cursor.fetchall()."""
    pool = MagicMock()
    cursor_mock = MagicMock()
    cursor_mock.fetchall.return_value = rows
    cursor_mock.description = [
        (col,) for col in [
            "price_key", "symbol", "commodity_name", "commodity_type",
            "trade_date", "year", "month", "day", "quarter", "day_of_week",
            "is_trading_day", "open", "high", "low", "close", "adj_close",
            "volume", "daily_change", "daily_change_pct", "source", "created_at",
        ]
    ]
    cursor_mock.__enter__ = MagicMock(return_value=cursor_mock)
    cursor_mock.__exit__ = MagicMock(return_value=False)

    conn_mock = MagicMock()
    conn_mock.cursor.return_value = cursor_mock
    conn_mock.__enter__ = MagicMock(return_value=conn_mock)
    conn_mock.__exit__ = MagicMock(return_value=False)

    from contextlib import contextmanager

    @contextmanager
    def fake_get_connection():
        yield conn_mock

    pool.get_connection = fake_get_connection
    return pool


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestFullExport:
    """Tests for PgExporter.export_full()."""

    def test_creates_parquet_files(self, config: Settings) -> None:
        """export_full should create one Parquet file per (year, month) partition."""
        pool = _make_pool_mock(_make_sample_rows())
        exporter = PgExporter(config, pool)
        stats = exporter.export_full()

        # Two distinct (year, month) partitions in sample data: (2024,1) and (2024,2)
        assert stats["partitions_written"] == 2
        assert stats["total_rows"] == 3

    def test_parquet_files_exist_at_expected_paths(self, config: Settings) -> None:
        """Parquet files should exist at the Hive-style partition paths."""
        pool = _make_pool_mock(_make_sample_rows())
        exporter = PgExporter(config, pool)
        exporter.export_full()

        jan = config.raw_path / "year=2024" / "month=1" / "data.parquet"
        feb = config.raw_path / "year=2024" / "month=2" / "data.parquet"
        assert jan.exists(), f"Expected {jan}"
        assert feb.exists(), f"Expected {feb}"

    def test_parquet_schema_contains_required_columns(self, config: Settings) -> None:
        """Exported Parquet must contain required columns."""
        pool = _make_pool_mock(_make_sample_rows())
        exporter = PgExporter(config, pool)
        exporter.export_full()

        jan = config.raw_path / "year=2024" / "month=1" / "data.parquet"
        table = pq.read_table(jan)
        required = {"symbol", "trade_date", "close", "volume", "source"}
        assert required.issubset(set(table.schema.names))

    def test_empty_result_returns_zero_stats(self, config: Settings) -> None:
        """No rows from PostgreSQL should yield zero stats without writing files."""
        pool = _make_pool_mock([])
        exporter = PgExporter(config, pool)
        stats = exporter.export_full()

        assert stats["total_rows"] == 0
        assert stats["partitions_written"] == 0

    def test_parquet_metadata_contains_source(self, config: Settings) -> None:
        """Each Parquet file should embed source metadata in its schema."""
        pool = _make_pool_mock(_make_sample_rows())
        exporter = PgExporter(config, pool)
        exporter.export_full()

        jan = config.raw_path / "year=2024" / "month=1" / "data.parquet"
        table = pq.read_table(jan)
        metadata = table.schema.metadata or {}
        assert b"source" in metadata


class TestIncrementalExport:
    """Tests for PgExporter.export_incremental()."""

    def test_incremental_returns_stats(self, config: Settings) -> None:
        """Incremental export should produce correct stats."""
        pool = _make_pool_mock(_make_sample_rows()[:2])
        exporter = PgExporter(config, pool)
        stats = exporter.export_incremental(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )
        assert stats["total_rows"] == 2
        assert stats["partitions_written"] == 1
