"""
Silver layer transformer: curates and enriches the bronze Parquet data.

Reads raw Parquet files, applies quality filters, computes derived columns,
and writes curated Parquet files alongside a data quality report.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import duckdb
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from src.config import Settings

logger = logging.getLogger(__name__)

# Price sanity bounds (USD per barrel / MMBtu)
_PRICE_FLOOR = 0.01
_PRICE_CEILING = 500.0

_CURATED_SCHEMA = pa.schema(
    [
        pa.field("price_key", pa.int64()),
        pa.field("symbol", pa.string()),
        pa.field("commodity_name", pa.string()),
        pa.field("commodity_type", pa.string()),
        pa.field("trade_date", pa.date32()),
        pa.field("year", pa.int32()),
        pa.field("month", pa.int32()),
        pa.field("day", pa.int32()),
        pa.field("quarter", pa.int32()),
        pa.field("is_trading_day", pa.bool_()),
        pa.field("open", pa.float64()),
        pa.field("high", pa.float64()),
        pa.field("low", pa.float64()),
        pa.field("close", pa.float64()),
        pa.field("adj_close", pa.float64()),
        pa.field("volume", pa.int64()),
        pa.field("daily_change", pa.float64()),
        pa.field("daily_change_pct", pa.float64()),
        pa.field("daily_return_pct", pa.float64()),
        pa.field("source", pa.string()),
        pa.field("quality_flag", pa.string()),
    ]
)

_QUALITY_SCHEMA = pa.schema(
    [
        pa.field("symbol", pa.string()),
        pa.field("trade_date", pa.date32()),
        pa.field("quality_flag", pa.string()),
        pa.field("reason", pa.string()),
    ]
)


class SilverTransformer:
    """Transforms bronze Parquet data into curated silver layer.

    Args:
        config: Application settings with data path configuration.
    """

    def __init__(self, config: Settings) -> None:
        self._config = config

    def transform(self) -> dict[str, Any]:
        """Run the full silver transformation pipeline.

        Reads all raw Parquet files, applies transformations, writes curated
        Parquet files and a quality report.

        Returns:
            Stats dict with: rows_in, rows_out, rows_filtered, quality_score,
            partitions_written, duration_seconds.
        """
        t0 = datetime.now(tz=UTC)

        raw_glob = str(self._config.raw_path / "**" / "*.parquet")
        df = self._read_raw(raw_glob)

        if df.empty:
            logger.warning("No raw Parquet files found; nothing to transform.")
            return {
                "rows_in": 0,
                "rows_out": 0,
                "rows_filtered": 0,
                "quality_score": 0.0,
                "partitions_written": 0,
                "duration_seconds": 0.0,
            }

        rows_in = len(df)
        df_clean, quality_df = self._apply_transformations(df)
        rows_out = len(df_clean)
        rows_filtered = rows_in - rows_out

        partitions = self._write_curated(df_clean)
        self._write_quality_report(quality_df)

        quality_score = round(rows_out / rows_in * 100, 2) if rows_in > 0 else 0.0
        duration = (datetime.now(tz=UTC) - t0).total_seconds()

        stats = {
            "rows_in": rows_in,
            "rows_out": rows_out,
            "rows_filtered": rows_filtered,
            "quality_score": quality_score,
            "partitions_written": partitions,
            "duration_seconds": round(duration, 2),
        }
        logger.info("Silver transformation complete: %s", stats)
        return stats

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _read_raw(self, glob_pattern: str) -> pd.DataFrame:
        """Read all bronze Parquet files into a single DataFrame via DuckDB.

        Args:
            glob_pattern: Filesystem glob covering all raw partitions.

        Returns:
            Combined DataFrame, or empty DataFrame if no files found.
        """
        try:
            con = duckdb.connect(":memory:")
            df = con.execute(f"SELECT * FROM read_parquet('{glob_pattern}', hive_partitioning=true)").df()
            con.close()
            logger.info("Read %d rows from bronze layer", len(df))
            return df
        except Exception as exc:
            logger.warning("Could not read raw Parquet files: %s", exc)
            return pd.DataFrame()

    def _apply_transformations(self, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Apply all quality filters and compute derived columns.

        Filters:
          - Remove rows with null close price
          - Remove rows with non-positive close price
          - Flag rows where any price is outside [_PRICE_FLOOR, _PRICE_CEILING]

        Derived columns:
          - daily_return_pct: (close - prev_close) / prev_close per symbol
          - quality_flag: 'valid' or 'suspect'

        Args:
            df: Raw combined DataFrame.

        Returns:
            Tuple of (clean_df, quality_report_df).
        """
        df = df.copy()

        # Standardise column names to snake_case (already snake_case from exporter)
        df.columns = [c.lower().replace(" ", "_") for c in df.columns]

        quality_records: list[dict] = []

        # --- Filter: null close ---
        null_mask = df["close"].isna()
        for _, row in df[null_mask].iterrows():
            quality_records.append(
                {
                    "symbol": row.get("symbol", ""),
                    "trade_date": row.get("trade_date"),
                    "quality_flag": "filtered",
                    "reason": "null close price",
                }
            )
        df = df[~null_mask].copy()

        # --- Filter: non-positive close ---
        neg_mask = df["close"] <= 0
        for _, row in df[neg_mask].iterrows():
            quality_records.append(
                {
                    "symbol": row.get("symbol", ""),
                    "trade_date": row.get("trade_date"),
                    "quality_flag": "filtered",
                    "reason": f"non-positive close price: {row.get('close')}",
                }
            )
        df = df[~neg_mask].copy()

        # --- Compute daily_return_pct ---
        df = df.sort_values(["symbol", "trade_date"])
        df["prev_close"] = df.groupby("symbol")["close"].shift(1)
        df["daily_return_pct"] = ((df["close"] - df["prev_close"]) / df["prev_close"]).round(6)
        df = df.drop(columns=["prev_close"])

        # --- Quality flag: price range check ---
        suspect_mask = (df["close"] < _PRICE_FLOOR) | (df["close"] > _PRICE_CEILING) | (df["high"] < df["low"])
        df["quality_flag"] = "valid"
        df.loc[suspect_mask, "quality_flag"] = "suspect"

        for _, row in df[suspect_mask].iterrows():
            quality_records.append(
                {
                    "symbol": row.get("symbol", ""),
                    "trade_date": row.get("trade_date"),
                    "quality_flag": "suspect",
                    "reason": (
                        f"close={row.get('close')} outside [{_PRICE_FLOOR},{_PRICE_CEILING}]"
                        if not (row.get("close", 1) >= _PRICE_FLOOR and row.get("close", 0) <= _PRICE_CEILING)
                        else "high < low"
                    ),
                }
            )

        quality_df = pd.DataFrame(
            quality_records,
            columns=["symbol", "trade_date", "quality_flag", "reason"],
        )

        # Drop columns not in silver schema
        keep_cols = [f.name for f in _CURATED_SCHEMA]
        df = df[[c for c in keep_cols if c in df.columns]]

        logger.info(
            "Transformations applied: %d rows in, %d out, %d filtered, %d suspect",
            len(df) + len([r for r in quality_records if r["quality_flag"] == "filtered"]),
            len(df),
            len([r for r in quality_records if r["quality_flag"] == "filtered"]),
            len(df[df["quality_flag"] == "suspect"]),
        )
        return df, quality_df

    def _write_curated(self, df: pd.DataFrame) -> int:
        """Write cleaned DataFrame to Hive-partitioned silver Parquet files.

        Args:
            df: Cleaned and enriched DataFrame.

        Returns:
            Number of partitions written.
        """
        if "year" not in df.columns or "month" not in df.columns:
            logger.error("DataFrame missing year/month columns; cannot partition.")
            return 0

        count = 0
        for (year, month), part_df in df.groupby(["year", "month"]):
            out_dir = self._config.curated_path / f"year={year}" / f"month={month}"
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / "data.parquet"

            table = pa.Table.from_pandas(part_df, schema=_CURATED_SCHEMA, safe=False)
            pq.write_table(table, out_path, compression="snappy")
            logger.info("Wrote %d curated rows to %s", len(part_df), out_path)
            count += 1

        return count

    def _write_quality_report(self, quality_df: pd.DataFrame) -> None:
        """Write the data quality report Parquet file.

        Args:
            quality_df: DataFrame with quality flag records.
        """
        out_dir = self._config.quality_report_path
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "report.parquet"

        if quality_df.empty:
            quality_df = pd.DataFrame(columns=["symbol", "trade_date", "quality_flag", "reason"])

        table = pa.Table.from_pandas(quality_df, schema=_QUALITY_SCHEMA, safe=False)
        pq.write_table(table, out_path, compression="snappy")
        logger.info("Quality report written: %d records → %s", len(quality_df), out_path)
