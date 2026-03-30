"""
CLI entry point for the oil price ingestion service.

Usage:
    python -m src.main backfill     # Full historical backfill
    python -m src.main incremental  # Incremental load (new data only)
    python -m src.main refresh      # Truncate staging + full backfill
    python -m src.main health       # DB connectivity check
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

from src.config import Settings
from src.extractor.yahoo_finance import YahooFinanceExtractor
from src.loader.postgres_loader import PostgresLoader
from src.pipeline.ingestion_pipeline import IngestionPipeline, PipelineSummary
from src.utils.db_connection import ConnectionPool
from src.utils.logging_config import get_logger, setup_logging
from src.validator.price_validator import PriceValidator

# Logger is initialised after setup_logging() is called
logger = get_logger(__name__, component="main")


def _build_pipeline(config: Settings) -> tuple[IngestionPipeline, ConnectionPool]:
    """Construct all pipeline components and wire them together."""
    pool = ConnectionPool(config)
    extractor = YahooFinanceExtractor(db_pool=pool, source_name=config.SOURCE_NAME)
    validator = PriceValidator()
    loader = PostgresLoader(pool=pool, config=config)
    pipeline = IngestionPipeline(
        config=config, extractor=extractor, validator=validator, loader=loader
    )
    return pipeline, pool


def _print_summary(summary: PipelineSummary) -> None:
    """Print a formatted ASCII summary table to stdout."""
    col_w = [10, 10, 8, 8, 8, 8, 10]
    headers = ["Symbol", "Status", "Fetched", "Valid", "Loaded", "Errors", "Mode"]
    sep = "+" + "+".join("-" * w for w in col_w) + "+"
    row_fmt = "|" + "|".join(f"{{:<{w}}}" for w in col_w) + "|"

    print()
    print(sep)
    print(row_fmt.format(*headers))
    print(sep)
    for symbol, result in summary.items():
        row = [
            symbol[:col_w[0] - 1],
            str(result.get("status", ""))[:col_w[1] - 1],
            str(result.get("rows_fetched", 0)),
            str(result.get("rows_valid", 0)),
            str(result.get("rows_loaded", 0)),
            str(result.get("rows_errors", 0)),
            str(result.get("mode", ""))[:col_w[6] - 1],
        ]
        print(row_fmt.format(*row))
    print(sep)
    print()


def _exit_code(summary: PipelineSummary) -> int:
    """Determine exit code from summary.

    Returns:
        0 - all success/skipped
        1 - partial failure (some errors)
        2 - total failure (all errored or summary is empty)
    """
    if not summary:
        return 2
    statuses = [r.get("status", "error") for r in summary.values()]
    error_count = sum(1 for s in statuses if s == "error")
    if error_count == 0:
        return 0
    if error_count == len(statuses):
        return 2
    return 1


def cmd_backfill(config: Settings) -> int:
    """Run full historical backfill."""
    pipeline, pool = _build_pipeline(config)
    try:
        summary = pipeline.run_backfill()
        _print_summary(summary)
        return _exit_code(summary)
    finally:
        pool.close()


def cmd_incremental(config: Settings) -> int:
    """Run incremental load."""
    pipeline, pool = _build_pipeline(config)
    try:
        summary = pipeline.run_incremental()
        _print_summary(summary)
        return _exit_code(summary)
    finally:
        pool.close()


def cmd_refresh(config: Settings) -> int:
    """Truncate staging and run full backfill."""
    pipeline, pool = _build_pipeline(config)
    try:
        summary = pipeline.run_full_refresh()
        _print_summary(summary)
        return _exit_code(summary)
    finally:
        pool.close()


def cmd_health(config: Settings) -> int:
    """Check database connectivity."""
    pool = ConnectionPool(config)
    try:
        ok = pool.health_check()
        if ok:
            print("OK - database is reachable at " + config.db_dsn)
            return 0
        else:
            print("FAIL - could not reach database at " + config.db_dsn)
            return 2
    finally:
        pool.close()


def main() -> None:
    """Parse CLI arguments and dispatch to the appropriate command."""
    parser = argparse.ArgumentParser(
        prog="oil-ingestor",
        description="Oil price data ingestion service for the oil_warehouse PostgreSQL warehouse.",
    )
    parser.add_argument(
        "command",
        choices=["backfill", "incremental", "refresh", "health"],
        help=(
            "backfill: fetch full history | "
            "incremental: fetch new data only | "
            "refresh: truncate + backfill | "
            "health: check DB connection"
        ),
    )
    args = parser.parse_args()

    config = Settings()
    setup_logging(config.LOG_LEVEL)

    commands: dict[str, Any] = {
        "backfill": cmd_backfill,
        "incremental": cmd_incremental,
        "refresh": cmd_refresh,
        "health": cmd_health,
    }

    exit_code = commands[args.command](config)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
