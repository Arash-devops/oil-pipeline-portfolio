"""
Ingestion pipeline orchestrator.

Ties together the extractor, validator, and loader into three runnable modes:
- backfill:       fetch N years of history for all commodities
- incremental:    fetch only new data since the last loaded date
- full_refresh:   truncate staging then re-run backfill from scratch
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

from src.config import Settings
from src.extractor.base import BaseExtractor
from src.loader.postgres_loader import PostgresLoader
from src.validator.price_validator import PriceValidator

logger = logging.getLogger(__name__)

# Type alias for the per-commodity result dict
CommodityResult = dict[str, Any]
PipelineSummary = dict[str, CommodityResult]


class IngestionPipeline:
    """Orchestrates extract -> validate -> batch-load -> store-proc flow.

    Uses constructor injection so every dependency is replaceable, making
    the class easy to unit-test with mock implementations.

    Args:
        config:    Application settings.
        extractor: Concrete data-source extractor.
        validator: Price validation implementation.
        loader:    PostgreSQL loader.
    """

    def __init__(
        self,
        config: Settings,
        extractor: BaseExtractor,
        validator: PriceValidator,
        loader: PostgresLoader,
    ) -> None:
        self._config = config
        self._extractor = extractor
        self._validator = validator
        self._loader = loader

    # ------------------------------------------------------------------
    # Public run modes
    # ------------------------------------------------------------------

    def run_backfill(self) -> PipelineSummary:
        """Fetch N years of history for every configured commodity.

        ``config.BACKFILL_YEARS`` controls how far back to go.
        A failure on one commodity is logged and skipped; the others
        still run.

        Returns:
            Summary dict keyed by ticker symbol.
        """
        end_date = date.today()
        start_date = end_date.replace(year=end_date.year - self._config.BACKFILL_YEARS)
        logger.info(
            "Starting backfill for %s from %s to %s",
            self._config.commodities_list,
            start_date,
            end_date,
        )
        return self._run_for_all(start_date, end_date, mode="backfill")

    def run_incremental(self) -> PipelineSummary:
        """Load only data that is newer than the last loaded date per symbol.

        If a symbol has no existing data, falls back to a 30-day window
        so the first incremental run still delivers something useful.

        Returns:
            Summary dict keyed by ticker symbol.
        """
        logger.info(
            "Starting incremental load for %s", self._config.commodities_list
        )
        summary: PipelineSummary = {}

        for symbol in self._config.commodities_list:
            last_date = self._extractor.get_last_available_date(symbol)
            if last_date is not None:
                start_date = last_date + timedelta(days=1)
            else:
                # First run for this symbol - fetch last 30 days as a safe default
                start_date = date.today() - timedelta(days=30)

            end_date = date.today()

            if start_date > end_date:
                logger.info("No new data to fetch for %s (up to date).", symbol)
                summary[symbol] = self._skipped_result("already up to date")
                continue

            summary[symbol] = self._run_one(symbol, start_date, end_date, mode="incremental")

        return summary

    def run_full_refresh(self) -> PipelineSummary:
        """Truncate staging and re-run backfill from scratch.

        Returns:
            Same summary structure as :meth:`run_backfill`.
        """
        logger.warning("Full refresh requested - truncating staging table.")
        self._loader.truncate_staging()
        return self.run_backfill()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _run_for_all(
        self, start_date: date, end_date: date, mode: str
    ) -> PipelineSummary:
        """Run the pipeline for every configured commodity over a fixed date range."""
        summary: PipelineSummary = {}
        for symbol in self._config.commodities_list:
            summary[symbol] = self._run_one(symbol, start_date, end_date, mode=mode)
        return summary

    def _run_one(
        self, symbol: str, start_date: date, end_date: date, mode: str
    ) -> CommodityResult:
        """Execute the full pipeline for a single commodity / date range.

        Any exception is caught and recorded in the result dict so the
        caller can continue with other commodities.

        Args:
            symbol:     Ticker symbol.
            start_date: Inclusive start of the fetch window.
            end_date:   Inclusive end of the fetch window.
            mode:       Label for logging ('backfill' or 'incremental').

        Returns:
            Dict containing rows_fetched, rows_valid, rows_loaded, etc.
        """
        result: CommodityResult = {
            "mode": mode,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "rows_fetched": 0,
            "rows_valid": 0,
            "rows_invalid": 0,
            "rows_loaded": 0,
            "rows_processed": 0,
            "rows_skipped": 0,
            "rows_errors": 0,
            "status": "success",
            "error": None,
        }

        try:
            # --- 1. Extract -------------------------------------------
            df = self._extractor.fetch_historical(symbol, start_date, end_date)
            result["rows_fetched"] = len(df)

            if df.empty:
                logger.info("No data fetched for %s. Skipping.", symbol)
                result["status"] = "skipped"
                return result

            # --- 2. Validate ------------------------------------------
            valid_df, invalid_df = self._validator.validate_dataframe(df)
            result["rows_valid"] = len(valid_df)
            result["rows_invalid"] = len(invalid_df)

            if valid_df.empty:
                logger.warning("All rows invalid for %s. Skipping load.", symbol)
                result["status"] = "skipped"
                return result

            # --- 3. Batch load to staging -----------------------------
            rows_loaded = 0
            for batch_start in range(0, len(valid_df), self._config.BATCH_SIZE):
                batch = valid_df.iloc[batch_start: batch_start + self._config.BATCH_SIZE]
                rows_loaded += self._loader.load_to_staging(batch)
            result["rows_loaded"] = rows_loaded

            # --- 4. Process staging -> warehouse ---------------------
            proc = self._loader.process_staging()
            result["rows_processed"] = proc.get("processed", 0)
            result["rows_skipped"] = proc.get("skipped", 0)
            result["rows_errors"] = proc.get("errors", 0)

            # --- 5. Calculate technical metrics ----------------------
            commodity_keys = self._loader.get_commodity_keys()
            commodity_key = commodity_keys.get(symbol)
            if commodity_key is not None:
                self._loader.calculate_metrics(commodity_key, start_date, end_date)
            else:
                logger.warning(
                    "commodity_key not found for %s; skipping metrics.", symbol
                )

            # --- 6. Aggregate monthly summaries ----------------------
            self._aggregate_months_in_range(start_date, end_date)

        except Exception as exc:
            logger.error(
                "Pipeline failed for %s: %s",
                symbol,
                exc,
                exc_info=True,
                extra={"symbol": symbol},
            )
            result["status"] = "error"
            result["error"] = str(exc)

        return result

    def _aggregate_months_in_range(self, start_date: date, end_date: date) -> None:
        """Call sp_aggregate_monthly for every year/month in the date range."""
        current = start_date.replace(day=1)
        end_month = end_date.replace(day=1)
        while current <= end_month:
            try:
                self._loader.aggregate_monthly(current.year, current.month)
            except Exception as exc:
                logger.warning(
                    "aggregate_monthly failed for %d-%02d: %s",
                    current.year,
                    current.month,
                    exc,
                )
            # Advance to next month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)

    @staticmethod
    def _skipped_result(reason: str) -> CommodityResult:
        """Build a result dict for a skipped commodity."""
        return {
            "mode": "incremental",
            "rows_fetched": 0,
            "rows_valid": 0,
            "rows_invalid": 0,
            "rows_loaded": 0,
            "rows_processed": 0,
            "rows_skipped": 0,
            "rows_errors": 0,
            "status": "skipped",
            "error": reason,
        }
