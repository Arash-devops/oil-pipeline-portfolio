"""
CLI entry point for the Oil Price Lakehouse service.

Commands:
  export      -- Export PostgreSQL warehouse data to Parquet bronze layer
  transform   -- Transform bronze to silver (curated) layer
  aggregate   -- Aggregate silver to gold (serving) layer
  query       -- Interactive SQL prompt against all layers
  stats       -- Print layer statistics
  full-pipeline -- Run export -> transform -> aggregate in sequence
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime

from src.config import Settings
from src.utils.db_connection import PgConnectionPool
from src.utils.logging_config import get_logger, setup_logging

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _print_table(title: str, rows: list[tuple[str, str]]) -> None:
    """Print a simple two-column ASCII summary table.

    Args:
        title: Table header text.
        rows: List of (label, value) string tuples.
    """
    width = max((len(r[0]) for r in rows), default=10) + 2
    border = "+" + "-" * (width + 1) + "+" + "-" * 22 + "+"
    print(border)
    print(f"| {title:<{width}} {'':21}|")
    print(border)
    for label, value in rows:
        print(f"| {label:<{width}} {str(value):<21} |")
    print(border)


def _date_arg(value: str) -> date:
    """Parse a YYYY-MM-DD string into a date object.

    Args:
        value: Date string.

    Returns:
        Parsed date.

    Raises:
        argparse.ArgumentTypeError: If the string is not a valid date.
    """
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as err:
        raise argparse.ArgumentTypeError(f"Date must be YYYY-MM-DD, got: {value}") from err


# ---------------------------------------------------------------------------
# Command implementations
# ---------------------------------------------------------------------------


def cmd_export(args: argparse.Namespace, config: Settings) -> int:
    """Run the bronze layer export.

    Args:
        args: Parsed CLI arguments.
        config: Application settings.

    Returns:
        Exit code (0 success, 2 failure).
    """
    from src.exporter.pg_exporter import PgExporter

    pool = PgConnectionPool(config)
    try:
        exporter = PgExporter(config, pool)
        if args.start_date or args.end_date:
            start = args.start_date or date(2000, 1, 1)
            end = args.end_date or date.today()
            stats = exporter.export_incremental(start, end)
            mode = f"incremental ({start} -> {end})"
        else:
            stats = exporter.export_full()
            mode = "full"

        _print_table(
            f"Export ({mode})",
            [
                ("total_rows", stats["total_rows"]),
                ("partitions_written", stats["partitions_written"]),
                ("duration_seconds", stats["duration_seconds"]),
            ],
        )
        return 0
    except Exception as exc:
        logger.error("Export failed: %s", exc)
        return 2
    finally:
        pool.close()


def cmd_transform(args: argparse.Namespace, config: Settings) -> int:
    """Run the silver layer transformation.

    Args:
        args: Parsed CLI arguments (unused).
        config: Application settings.

    Returns:
        Exit code (0 success, 2 failure).
    """
    from src.transformer.silver_transformer import SilverTransformer

    try:
        transformer = SilverTransformer(config)
        stats = transformer.transform()
        _print_table(
            "Transform (silver)",
            [
                ("rows_in", stats["rows_in"]),
                ("rows_out", stats["rows_out"]),
                ("rows_filtered", stats["rows_filtered"]),
                ("quality_score", f"{stats['quality_score']}%"),
                ("partitions_written", stats["partitions_written"]),
                ("duration_seconds", stats["duration_seconds"]),
            ],
        )
        return 0 if stats["rows_out"] > 0 else 1
    except Exception as exc:
        logger.error("Transform failed: %s", exc)
        return 2


def cmd_aggregate(args: argparse.Namespace, config: Settings) -> int:
    """Run the gold layer aggregation.

    Args:
        args: Parsed CLI arguments (unused).
        config: Application settings.

    Returns:
        Exit code (0 success, 2 failure).
    """
    from src.aggregator.gold_aggregator import GoldAggregator

    try:
        aggregator = GoldAggregator(config)
        stats = aggregator.aggregate()
        _print_table(
            "Aggregate (gold)",
            [
                ("monthly_summary_rows", stats["monthly_summary_rows"]),
                ("price_metrics_rows", stats["price_metrics_rows"]),
                ("commodity_comparison_rows", stats["commodity_comparison_rows"]),
                ("duration_seconds", stats["duration_seconds"]),
            ],
        )
        return (
            0
            if any(stats[k] > 0 for k in ("monthly_summary_rows", "price_metrics_rows", "commodity_comparison_rows"))
            else 1
        )
    except Exception as exc:
        logger.error("Aggregate failed: %s", exc)
        return 2


def cmd_query(args: argparse.Namespace, config: Settings) -> int:
    """Launch an interactive SQL prompt against the lakehouse.

    Args:
        args: Parsed CLI arguments (unused).
        config: Application settings.

    Returns:
        Exit code (always 0).
    """
    from src.query.duckdb_engine import DuckDBEngine

    engine = DuckDBEngine(config)
    print("Oil Price Lakehouse — Interactive SQL")
    print("Available views: raw, curated, monthly_summary, price_metrics, commodity_comparison")
    print("Type 'exit' or Ctrl+D to quit.\n")

    try:
        while True:
            try:
                sql = input("sql> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye.")
                break

            if not sql:
                continue
            if sql.lower() in ("exit", "quit", "\\q"):
                break

            df = engine.query(sql)
            if df.empty:
                print("(no rows)")
            else:
                print(df.to_string(index=False))
                print(f"\n({len(df)} rows)\n")
    finally:
        engine.close()

    return 0


def cmd_stats(args: argparse.Namespace, config: Settings) -> int:
    """Print statistics for all lakehouse layers.

    Args:
        args: Parsed CLI arguments (unused).
        config: Application settings.

    Returns:
        Exit code (always 0).
    """
    from src.query.duckdb_engine import DuckDBEngine

    engine = DuckDBEngine(config)
    try:
        stats = engine.layer_stats()
        rows = [(layer, f"{s['rows']} rows / {s['size_mb']} MB") for layer, s in stats.items()]
        _print_table("Lakehouse Layer Stats", rows)
    finally:
        engine.close()

    return 0


def cmd_full_pipeline(args: argparse.Namespace, config: Settings) -> int:
    """Run export -> transform -> aggregate in sequence.

    Args:
        args: Parsed CLI arguments.
        config: Application settings.

    Returns:
        Exit code (0 all success, 1 partial, 2 all failed).
    """
    print("Running full pipeline: export -> transform -> aggregate\n")

    results = []

    results.append(("export", cmd_export(args, config)))
    results.append(("transform", cmd_transform(args, config)))
    results.append(("aggregate", cmd_aggregate(args, config)))

    print("\nPipeline summary:")
    for step, code in results:
        status = "OK" if code == 0 else ("PARTIAL" if code == 1 else "FAILED")
        print(f"  {step:<12} {status}")

    exit_codes = [r[1] for r in results]
    if all(c == 0 for c in exit_codes):
        return 0
    if all(c == 2 for c in exit_codes):
        return 2
    return 1


# ---------------------------------------------------------------------------
# CLI wiring
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    parser = argparse.ArgumentParser(
        prog="python -m src.main",
        description="Oil Price Lakehouse CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # export
    p_export = sub.add_parser("export", help="Export PostgreSQL data to Parquet bronze layer")
    p_export.add_argument("--start-date", type=_date_arg, help="Incremental start (YYYY-MM-DD)")
    p_export.add_argument("--end-date", type=_date_arg, help="Incremental end (YYYY-MM-DD)")

    # transform
    sub.add_parser("transform", help="Transform bronze to silver curated layer")

    # aggregate
    sub.add_parser("aggregate", help="Aggregate silver to gold serving layer")

    # query
    sub.add_parser("query", help="Interactive SQL prompt")

    # stats
    sub.add_parser("stats", help="Print layer statistics")

    # full-pipeline
    p_full = sub.add_parser("full-pipeline", help="Run export -> transform -> aggregate")
    p_full.add_argument("--start-date", type=_date_arg, help="Incremental start (YYYY-MM-DD)")
    p_full.add_argument("--end-date", type=_date_arg, help="Incremental end (YYYY-MM-DD)")

    return parser


def main() -> None:
    """Parse arguments, configure logging, and dispatch to command."""
    config = Settings()
    setup_logging(config.LOG_LEVEL)

    parser = build_parser()
    args = parser.parse_args()

    dispatch = {
        "export": cmd_export,
        "transform": cmd_transform,
        "aggregate": cmd_aggregate,
        "query": cmd_query,
        "stats": cmd_stats,
        "full-pipeline": cmd_full_pipeline,
    }

    handler = dispatch[args.command]
    sys.exit(handler(args, config))


if __name__ == "__main__":
    main()
