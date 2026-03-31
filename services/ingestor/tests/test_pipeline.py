"""
Tests for IngestionPipeline orchestration logic.

All external dependencies (extractor, validator, loader) are replaced with
lightweight test doubles so the tests run without a database or network.
"""

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import MagicMock

import pandas as pd

from src.config import Settings
from src.extractor.yahoo_finance import STANDARD_COLUMNS
from src.pipeline.ingestion_pipeline import IngestionPipeline

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _settings() -> Settings:
    return Settings(
        DB_HOST="localhost",
        DB_PORT=5432,
        DB_NAME="oil_warehouse",
        DB_USER="test",
        DB_PASSWORD="test",
        COMMODITIES="CL=F,BZ=F",
        BATCH_SIZE=100,
        BACKFILL_YEARS=1,
    )


def _valid_df(symbol: str = "CL=F", rows: int = 3) -> pd.DataFrame:
    today = date.today()
    return pd.DataFrame(
        {
            "symbol": [symbol] * rows,
            "trade_date": [today - timedelta(days=i + 1) for i in range(rows)],
            "open": [72.0] * rows,
            "high": [74.0] * rows,
            "low": [71.0] * rows,
            "close": [73.0] * rows,
            "adj_close": [73.0] * rows,
            "volume": [400_000] * rows,
        }
    )


def _make_pipeline(
    fetch_return=None,
    last_date=None,
    validate_return=None,
    load_return=5,
    process_return=None,
):
    """Build a pipeline with fully controlled mock dependencies."""
    config = _settings()

    extractor = MagicMock()
    extractor.fetch_historical.return_value = fetch_return if fetch_return is not None else _valid_df()
    extractor.get_last_available_date.return_value = last_date

    validator = MagicMock()
    if validate_return is None:
        df = fetch_return if fetch_return is not None else _valid_df()
        validate_return = (df, pd.DataFrame(columns=df.columns))
    validator.validate_dataframe.return_value = validate_return

    loader = MagicMock()
    loader.load_to_staging.return_value = load_return
    loader.process_staging.return_value = (
        process_return if process_return is not None else {"processed": 3, "skipped": 0, "errors": 0}
    )
    loader.get_commodity_keys.return_value = {"CL=F": 1, "BZ=F": 2}

    pipeline = IngestionPipeline(config=config, extractor=extractor, validator=validator, loader=loader)
    return pipeline, extractor, validator, loader


# ---------------------------------------------------------------------------
# run_incremental
# ---------------------------------------------------------------------------


class TestRunIncremental:
    def test_skips_symbol_when_already_up_to_date(self):
        """If last_date == today the pipeline should not call fetch_historical."""
        today = date.today()
        pipeline, extractor, *_ = _make_pipeline(last_date=today)
        summary = pipeline.run_incremental()

        extractor.fetch_historical.assert_not_called()
        for result in summary.values():
            assert result["status"] == "skipped"

    def test_processes_new_data_when_last_date_is_in_the_past(self):
        last = date.today() - timedelta(days=5)
        pipeline, extractor, _, loader = _make_pipeline(last_date=last)
        pipeline.run_incremental()

        assert extractor.fetch_historical.call_count == 2  # one per symbol
        # Loader should have been called
        assert loader.load_to_staging.called

    def test_falls_back_to_30_days_when_no_data_exists(self):
        """If get_last_available_date returns None, start_date = today - 30 days."""
        pipeline, extractor, *_ = _make_pipeline(last_date=None)
        pipeline.run_incremental()

        call_args = extractor.fetch_historical.call_args_list[0][0]
        symbol, start_date, end_date = call_args
        assert (end_date - start_date).days == 30


# ---------------------------------------------------------------------------
# run_backfill
# ---------------------------------------------------------------------------


class TestRunBackfill:
    def test_returns_success_for_all_symbols(self):
        pipeline, *_ = _make_pipeline()
        summary = pipeline.run_backfill()
        assert set(summary.keys()) == {"CL=F", "BZ=F"}
        for result in summary.values():
            assert result["status"] == "success"

    def test_continues_after_one_commodity_fails(self):
        """A failure on CL=F must not prevent BZ=F from being processed."""
        pipeline, extractor, validator, loader = _make_pipeline()

        # Make CL=F fail at the fetch stage
        def side_effect(symbol, start, end):
            if symbol == "CL=F":
                raise RuntimeError("simulated network error")
            return _valid_df(symbol=symbol)

        extractor.fetch_historical.side_effect = side_effect
        summary = pipeline.run_backfill()

        assert summary["CL=F"]["status"] == "error"
        assert summary["BZ=F"]["status"] == "success"

    def test_empty_fetch_marks_as_skipped(self):
        pipeline, *_ = _make_pipeline(
            fetch_return=pd.DataFrame(columns=STANDARD_COLUMNS),
            validate_return=(
                pd.DataFrame(columns=STANDARD_COLUMNS),
                pd.DataFrame(columns=STANDARD_COLUMNS),
            ),
        )
        summary = pipeline.run_backfill()
        for result in summary.values():
            assert result["status"] == "skipped"


# ---------------------------------------------------------------------------
# run_full_refresh
# ---------------------------------------------------------------------------


class TestRunFullRefresh:
    def test_truncates_staging_before_backfill(self):
        pipeline, _, _, loader = _make_pipeline()
        pipeline.run_full_refresh()
        loader.truncate_staging.assert_called_once()
