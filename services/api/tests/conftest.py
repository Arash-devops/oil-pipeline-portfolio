"""
Shared test fixtures for the Oil Price API test suite.

Strategy:
- PostgreSQL is fully mocked (no real DB connection required).
- DuckDB uses a real in-memory connection with test data registered as views,
  giving accurate query behaviour without Parquet files on disk.
"""

from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, patch

import duckdb
import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_duckdb_conn, get_pg_conn
from app.main import app

# ---------------------------------------------------------------------------
# PostgreSQL mock helpers
# ---------------------------------------------------------------------------


class MockAsyncCursor:
    """Minimal async cursor that returns preconfigured rows."""

    def __init__(self, rows: list | None = None) -> None:
        self._rows = rows or [(1,)]

    async def __aenter__(self) -> MockAsyncCursor:
        return self

    async def __aexit__(self, *_: object) -> None:
        pass

    async def execute(self, sql: str, params: object = None) -> None:  # noqa: ARG002
        pass

    async def fetchone(self) -> tuple | None:
        return self._rows[0] if self._rows else None

    async def fetchall(self) -> list:
        return self._rows


class MockAsyncConnection:
    """Minimal async connection that vends MockAsyncCursor instances."""

    def __init__(self, rows: list | None = None) -> None:
        self._rows = rows

    def cursor(self, row_factory: object = None) -> MockAsyncCursor:  # noqa: ARG002
        return MockAsyncCursor(self._rows)


def _pg_override(rows: list | None = None):
    """Return an async-generator dependency that yields a mock PG connection."""

    async def _dep():
        yield MockAsyncConnection(rows)

    return _dep


def _duck_override(conn: duckdb.DuckDBPyConnection):
    """Return a sync-generator dependency that yields an existing DuckDB connection."""

    def _dep():
        yield conn

    return _dep


# ---------------------------------------------------------------------------
# DuckDB fixture — real in-memory DB with test views
# ---------------------------------------------------------------------------


@pytest.fixture
def duck_conn():
    """In-memory DuckDB connection with serving-layer views pre-populated."""
    conn = duckdb.connect(":memory:")

    conn.execute("""
        CREATE VIEW monthly_summary AS
        SELECT
            'CL=F'           AS symbol,
            'Crude Oil WTI'  AS commodity_name,
            2024             AS year,
            1                AS month,
            20               AS trading_days,
            75.0             AS avg_close,
            73.0             AS min_close,
            77.0             AS max_close,
            1.5              AS stddev_close,
            1000000          AS total_volume,
            2.5              AS monthly_return_pct
    """)

    conn.execute("""
        CREATE VIEW price_metrics AS
        SELECT
            'CL=F'       AS symbol,
            '2024-01-15' AS trade_date,
            75.5         AS close,
            74.0         AS ma7,
            73.5         AS ma30,
            72.0         AS ma90,
            1.2          AS volatility_20d,
            78.0         AS bollinger_upper,
            71.0         AS bollinger_lower
    """)

    conn.execute("""
        CREATE VIEW commodity_comparison AS
        SELECT
            '2024-01-15' AS trade_date,
            75.5         AS wti_close,
            76.0         AS brent_close,
            -0.5         AS spread,
            0.993        AS ratio
    """)

    yield conn
    conn.close()


# ---------------------------------------------------------------------------
# Client fixtures
# ---------------------------------------------------------------------------

_PATCH_INIT = "app.main.init_pg_pool"
_PATCH_CLOSE = "app.main.close_pg_pool"


@pytest.fixture
def client(duck_conn: duckdb.DuckDBPyConnection):
    """TestClient with a health-check PG mock (SELECT 1) and real DuckDB test data."""
    app.dependency_overrides[get_pg_conn] = _pg_override(rows=[(1,)])
    app.dependency_overrides[get_duckdb_conn] = _duck_override(duck_conn)
    with patch(_PATCH_INIT, new=AsyncMock()), patch(_PATCH_CLOSE, new=AsyncMock()), TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def pg_client(duck_conn: duckdb.DuckDBPyConnection):
    """TestClient with PG mocked to return realistic price rows."""
    price_rows = [
        {
            "full_date": date(2024, 1, 15),
            "commodity_id": "CL=F",
            "commodity_name": "Crude Oil WTI",
            "price_open": 75.0,
            "price_high": 76.0,
            "price_low": 74.0,
            "price_close": 75.5,
            "adj_close": 75.5,
            "volume": 100_000,
            "daily_change": 0.5,
            "daily_change_pct": 0.67,
        }
    ]
    app.dependency_overrides[get_pg_conn] = _pg_override(rows=price_rows)
    app.dependency_overrides[get_duckdb_conn] = _duck_override(duck_conn)
    with patch(_PATCH_INIT, new=AsyncMock()), patch(_PATCH_CLOSE, new=AsyncMock()), TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def commodity_client(duck_conn: duckdb.DuckDBPyConnection):
    """TestClient with PG mocked to return commodity dimension rows."""
    commodity_rows = [
        {
            "commodity_id": "CL=F",
            "commodity_name": "Crude Oil WTI",
            "category": "Energy",
            "sub_category": "Crude Oil",
            "currency": "USD",
            "exchange": "NYMEX",
            "unit_of_measure": "Barrels",
        }
    ]
    app.dependency_overrides[get_pg_conn] = _pg_override(rows=commodity_rows)
    app.dependency_overrides[get_duckdb_conn] = _duck_override(duck_conn)
    with patch(_PATCH_INIT, new=AsyncMock()), patch(_PATCH_CLOSE, new=AsyncMock()), TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
