"""
Unit tests for YahooFinanceExtractor.

yfinance network calls are mocked so tests run offline and quickly.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import date
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.extractor.yahoo_finance import STANDARD_COLUMNS, YahooFinanceExtractor


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

def _make_mock_pool(last_date=None):
    """Return a mock ConnectionPool whose cursor returns *last_date*."""
    pool = MagicMock()
    conn = MagicMock()
    cursor = MagicMock()
    cursor.fetchone.return_value = (last_date,)
    conn.cursor.return_value.__enter__ = lambda s: cursor
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    @contextmanager
    def fake_get_connection():
        yield conn

    pool.get_connection = fake_get_connection
    return pool


def _yf_history_response() -> pd.DataFrame:
    """Minimal yfinance-style DataFrame with one row."""
    idx = pd.DatetimeIndex(["2024-01-15"], tz="UTC")
    return pd.DataFrame(
        {
            "Open": [72.50],
            "High": [74.20],
            "Low": [71.80],
            "Close": [73.45],
            "Adj Close": [73.45],
            "Volume": [450_000],
            "Dividends": [0.0],
            "Stock Splits": [0.0],
        },
        index=idx,
    )


# ---------------------------------------------------------------------------
# fetch_historical
# ---------------------------------------------------------------------------

class TestFetchHistorical:
    def test_returns_standard_columns(self):
        pool = _make_mock_pool()
        with patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value.history.return_value = _yf_history_response()
            extractor = YahooFinanceExtractor(db_pool=pool)
            df = extractor.fetch_historical("CL=F", date(2024, 1, 15), date(2024, 1, 15))

        assert list(df.columns) == STANDARD_COLUMNS

    def test_returns_correct_symbol(self):
        pool = _make_mock_pool()
        with patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value.history.return_value = _yf_history_response()
            extractor = YahooFinanceExtractor(db_pool=pool)
            df = extractor.fetch_historical("BZ=F", date(2024, 1, 15), date(2024, 1, 15))

        assert df.iloc[0]["symbol"] == "BZ=F"

    def test_empty_yf_response_returns_empty_df(self):
        pool = _make_mock_pool()
        with patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value.history.return_value = pd.DataFrame()
            extractor = YahooFinanceExtractor(db_pool=pool)
            df = extractor.fetch_historical("CL=F", date(2024, 1, 15), date(2024, 1, 15))

        assert df.empty
        assert list(df.columns) == STANDARD_COLUMNS

    def test_yf_exception_returns_empty_df(self):
        """Any yfinance exception should be caught and return empty DataFrame."""
        pool = _make_mock_pool()
        with patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value.history.side_effect = Exception("API unavailable")
            extractor = YahooFinanceExtractor(db_pool=pool)
            df = extractor.fetch_historical("CL=F", date(2024, 1, 15), date(2024, 1, 15))

        assert df.empty

    def test_trade_date_column_contains_date_objects(self):
        pool = _make_mock_pool()
        with patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value.history.return_value = _yf_history_response()
            extractor = YahooFinanceExtractor(db_pool=pool)
            df = extractor.fetch_historical("CL=F", date(2024, 1, 15), date(2024, 1, 15))

        assert isinstance(df.iloc[0]["trade_date"], date)


# ---------------------------------------------------------------------------
# fetch_latest
# ---------------------------------------------------------------------------

class TestFetchLatest:
    def test_calls_fetch_historical_with_correct_window(self):
        pool = _make_mock_pool()
        extractor = YahooFinanceExtractor(db_pool=pool)
        with patch.object(extractor, "fetch_historical", return_value=pd.DataFrame(columns=STANDARD_COLUMNS)) as mock_fh:
            extractor.fetch_latest("CL=F", days=7)
            args = mock_fh.call_args[0]
            symbol, start_date, end_date = args
        assert symbol == "CL=F"
        assert (end_date - start_date).days == 7


# ---------------------------------------------------------------------------
# get_last_available_date
# ---------------------------------------------------------------------------

class TestGetLastAvailableDate:
    def test_returns_date_when_data_exists(self):
        expected = date(2024, 3, 15)
        pool = _make_mock_pool(last_date=expected)
        extractor = YahooFinanceExtractor(db_pool=pool)
        result = extractor.get_last_available_date("CL=F")
        assert result == expected

    def test_returns_none_when_no_data(self):
        pool = _make_mock_pool(last_date=None)
        extractor = YahooFinanceExtractor(db_pool=pool)
        result = extractor.get_last_available_date("CL=F")
        assert result is None
