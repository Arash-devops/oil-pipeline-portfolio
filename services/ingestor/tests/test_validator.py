"""
Unit tests for PriceValidator.

Each test targets one validation rule in isolation, plus tests for
edge cases like accumulated errors and an entirely valid batch.
"""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import pytest

from src.validator.price_validator import PriceValidator


@pytest.fixture
def validator() -> PriceValidator:
    return PriceValidator()


def _make_valid_row(**overrides) -> dict:
    """Build a dict representing one valid OHLCV row."""
    yesterday = date.today() - timedelta(days=1)
    base = {
        "symbol": "CL=F",
        "trade_date": yesterday,
        "open": 72.50,
        "high": 74.20,
        "low": 71.80,
        "close": 73.45,
        "adj_close": 73.45,
        "volume": 450_000,
    }
    base.update(overrides)
    return base


def _df(*rows: dict) -> pd.DataFrame:
    return pd.DataFrame(list(rows))


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

class TestValidRows:
    def test_single_valid_row_passes(self, validator):
        valid, invalid = validator.validate_dataframe(_df(_make_valid_row()))
        assert len(valid) == 1
        assert len(invalid) == 0

    def test_zero_volume_is_valid(self, validator):
        """volume >= 0, so 0 is acceptable."""
        valid, invalid = validator.validate_dataframe(_df(_make_valid_row(volume=0)))
        assert len(valid) == 1
        assert len(invalid) == 0

    def test_open_equals_close_is_valid(self, validator):
        """A doji candle (open == close) is perfectly valid."""
        valid, invalid = validator.validate_dataframe(
            _df(_make_valid_row(open=73.0, close=73.0, high=73.5, low=72.5))
        )
        assert len(valid) == 1


# ---------------------------------------------------------------------------
# Rule 1: close > 0
# ---------------------------------------------------------------------------

class TestCloseMustBePositive:
    def test_zero_close_is_invalid(self, validator):
        _, invalid = validator.validate_dataframe(_df(_make_valid_row(close=0.0)))
        assert len(invalid) == 1
        assert "close" in invalid.iloc[0]["validation_errors"].lower()

    def test_negative_close_is_invalid(self, validator):
        _, invalid = validator.validate_dataframe(_df(_make_valid_row(close=-5.0)))
        assert len(invalid) == 1


# ---------------------------------------------------------------------------
# Rule 2: close < 500
# ---------------------------------------------------------------------------

class TestCloseSanityCeiling:
    def test_close_at_500_is_invalid(self, validator):
        _, invalid = validator.validate_dataframe(
            _df(_make_valid_row(close=500.0, high=500.0, open=499.0))
        )
        assert len(invalid) == 1
        assert "500" in invalid.iloc[0]["validation_errors"]

    def test_close_just_below_500_is_valid(self, validator):
        valid, _ = validator.validate_dataframe(
            _df(_make_valid_row(close=499.99, high=499.99))
        )
        assert len(valid) == 1


# ---------------------------------------------------------------------------
# Rule 3: high >= low
# ---------------------------------------------------------------------------

class TestHighMustBeGteqLow:
    def test_high_below_low_is_invalid(self, validator):
        _, invalid = validator.validate_dataframe(
            _df(_make_valid_row(high=70.0, low=75.0))
        )
        assert len(invalid) == 1
        assert "high" in invalid.iloc[0]["validation_errors"].lower()


# ---------------------------------------------------------------------------
# Rule 7: no future dates
# ---------------------------------------------------------------------------

class TestFutureDateIsInvalid:
    def test_tomorrow_is_invalid(self, validator):
        tomorrow = date.today() + timedelta(days=1)
        _, invalid = validator.validate_dataframe(_df(_make_valid_row(trade_date=tomorrow)))
        assert len(invalid) == 1
        assert "future" in invalid.iloc[0]["validation_errors"].lower()

    def test_today_is_valid(self, validator):
        """Today's date is not in the future."""
        valid, _ = validator.validate_dataframe(_df(_make_valid_row(trade_date=date.today())))
        assert len(valid) == 1


# ---------------------------------------------------------------------------
# Rule 8: no weekends
# ---------------------------------------------------------------------------

class TestWeekendDateIsInvalid:
    def test_saturday_is_invalid(self, validator):
        # Find the most recent Saturday
        today = date.today()
        days_since_sat = (today.weekday() - 5) % 7
        last_sat = today - timedelta(days=days_since_sat if days_since_sat else 7)
        _, invalid = validator.validate_dataframe(_df(_make_valid_row(trade_date=last_sat)))
        assert len(invalid) == 1
        assert "weekend" in invalid.iloc[0]["validation_errors"].lower()


# ---------------------------------------------------------------------------
# Rule 9: no null prices
# ---------------------------------------------------------------------------

class TestNullPricesAreInvalid:
    def test_null_close_is_invalid(self, validator):
        row = _make_valid_row()
        row["close"] = None
        _, invalid = validator.validate_dataframe(_df(row))
        assert len(invalid) == 1
        assert "close" in invalid.iloc[0]["validation_errors"].lower()


# ---------------------------------------------------------------------------
# Rule 10: no duplicates within batch
# ---------------------------------------------------------------------------

class TestDuplicateSymbolDateIsInvalid:
    def test_duplicate_pair_second_row_flagged(self, validator):
        row = _make_valid_row()
        valid, invalid = validator.validate_dataframe(_df(row, row))
        # First occurrence is kept; second is flagged
        assert len(valid) == 1
        assert len(invalid) == 1
        assert "duplicate" in invalid.iloc[0]["validation_errors"].lower()


# ---------------------------------------------------------------------------
# Multi-error accumulation
# ---------------------------------------------------------------------------

class TestMultipleErrorsAccumulated:
    def test_two_rules_violated_both_reported(self, validator):
        tomorrow = date.today() + timedelta(days=1)
        row = _make_valid_row(close=-1.0, trade_date=tomorrow)
        _, invalid = validator.validate_dataframe(_df(row))
        errors = invalid.iloc[0]["validation_errors"]
        assert "close" in errors.lower()
        assert "future" in errors.lower()

    def test_empty_dataframe_returns_two_empty_frames(self, validator):
        empty = pd.DataFrame(columns=["symbol", "trade_date", "open", "high", "low", "close", "adj_close", "volume"])
        valid, invalid = validator.validate_dataframe(empty)
        assert len(valid) == 0
        assert len(invalid) == 0
