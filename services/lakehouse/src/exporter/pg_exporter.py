"""
Bronze layer exporter: reads from PostgreSQL, writes Parquet with Hive partitioning.

Exports warehouse.fact_oil_prices joined with dim_commodity and dim_date
into {DATA_DIR}/raw/oil_prices/year={YYYY}/month={MM}/data.parquet using
snappy compression via PyArrow.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from src.config import Settings
from src.utils.db_connection import PgConnectionPool

logger = logging.getLogger(__name__)

_EXPORT_QUERY = """
SELECT
    f.price_key,
    dc.commodity_id          AS symbol,
    dc.commodity_name,
    dc.category              AS commodity_type,
    dd.full_date             AS trade_date,
    dd.year,
    dd.month,
    dd.day_of_month          AS day,
    dd.quarter,
    dd.day_of_week,
    dd.is_trading_day,
    f.price_open             AS open,
    f.price_high             AS high,
    f.price_low              AS low,
    f.price_close            AS close,
    f.adj_close,
    f.volume,
    f.daily_change,
    f.daily_change_pct,
    ds.source_name           AS source,
    f.created_at
FROM warehouse.fact_oil_prices f
JOIN warehouse.dim_commodity dc ON dc.commodity_key = f.commodity_key
JOIN warehouse.dim_date      dd ON dd.date_key       = f.date_key
JOIN warehouse.dim_source    ds ON ds.source_key     = f.source_key
WHERE dc.is_current = TRUE
  AND (%(start_date)s IS NULL OR dd.full_date >= %(start_date)s)
  AND (%(end_date)s   IS NULL OR dd.full_date <= %(end_date)s)
ORDER BY dd.full_date, dc.commodity_id
"""

_PARQUET_SCHEMA = pa.schema([
    pa.field("price_key",       pa.int64()),
    pa.field("symbol",          pa.string()),
    pa.field("commodity_name",  pa.string()),
    pa.field("commodity_type",  pa.string()),
    pa.field("trade_date",      pa.date32()),
    pa.field("year",            pa.int32()),
    pa.field("month",           pa.int32()),
    pa.field("day",             pa.int32()),
    pa.field("quarter",         pa.int32()),
    pa.field("day_of_week",     pa.int16()),
    pa.field("is_trading_day",  pa.bool_()),
    pa.field("open",            pa.float64()),
    pa.field("high",            pa.float64()),
    pa.field("low",             pa.float64()),
    pa.field("close",           pa.float64()),
    pa.field("adj_close",       pa.float64()),
    pa.field("volume",          pa.int64()),
    pa.field("daily_change",    pa.float64()),
    pa.field("daily_change_pct",pa.float64()),
    pa.field("source",          pa.string()),
    pa.field("created_at",      pa.timestamp("us", tz="UTC")),
])


class PgExporter:
    """Exports PostgreSQL warehouse data to Parquet bronze layer.

    Args:
        config: Application settings.
        pool: Open PostgreSQL connection pool.
    """

    def __init__(self, config: Settings, pool: PgConnectionPool) -> None:
        self._config = config
        self._pool = pool

    def export_full(self) -> dict[str, Any]:
        """Export all available data with no date filter.

        Returns:
            Stats dict with keys: total_rows, partitions_written, duration_seconds.
        """
        logger.info("Starting full export from PostgreSQL warehouse")
        return self._export(start_date=None, end_date=None)

    def export_incremental(
        self,
        start_date: date,
        end_date: date,
    ) -> dict[str, Any]:
        """Export data within a date range.

        Args:
            start_date: Inclusive start date.
            end_date: Inclusive end date.

        Returns:
            Stats dict with keys: total_rows, partitions_written, duration_seconds.
        """
        logger.info(
            "Starting incremental export from %s to %s",
            start_date.isoformat(),
            end_date.isoformat(),
        )
        return self._export(start_date=start_date, end_date=end_date)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _export(
        self,
        start_date: date | None,
        end_date: date | None,
    ) -> dict[str, Any]:
        """Fetch rows from Postgres and write Hive-partitioned Parquet files.

        Args:
            start_date: Optional lower bound (inclusive).
            end_date: Optional upper bound (inclusive).

        Returns:
            Stats dict.
        """
        t0 = datetime.now(tz=timezone.utc)
        df = self._fetch(start_date, end_date)

        if df.empty:
            logger.warning("No rows returned from PostgreSQL; nothing to write.")
            return {"total_rows": 0, "partitions_written": 0, "duration_seconds": 0.0}

        partitions_written = self._write_partitioned(df)

        duration = (datetime.now(tz=timezone.utc) - t0).total_seconds()
        stats = {
            "total_rows": len(df),
            "partitions_written": partitions_written,
            "duration_seconds": round(duration, 2),
        }
        logger.info("Export complete: %s", stats)
        return stats

    def _fetch(
        self,
        start_date: date | None,
        end_date: date | None,
    ) -> pd.DataFrame:
        """Execute the warehouse query and return a DataFrame."""
        base_query = """
        SELECT
            f.price_key,
            dc.commodity_id          AS symbol,
            dc.commodity_name,
            dc.category              AS commodity_type,
            dd.full_date             AS trade_date,
            dd.year,
            dd.month,
            dd.day_of_month          AS day,
            dd.quarter,
            dd.day_of_week,
            dd.is_trading_day,
            f.price_open             AS open,
            f.price_high             AS high,
            f.price_low              AS low,
            f.price_close            AS close,
            f.adj_close,
            f.volume,
            f.daily_change,
            f.daily_change_pct,
            ds.source_name           AS source,
            f.created_at
        FROM warehouse.fact_oil_prices f
        JOIN warehouse.dim_commodity dc ON dc.commodity_key = f.commodity_key
        JOIN warehouse.dim_date      dd ON dd.date_key       = f.date_key
        JOIN warehouse.dim_source    ds ON ds.source_key     = f.source_key
        WHERE dc.is_current = TRUE
        """
        params: dict = {}

        if start_date is not None:
            base_query += " AND dd.full_date >= %(start_date)s"
            params["start_date"] = start_date

        if end_date is not None:
            base_query += " AND dd.full_date <= %(end_date)s"
            params["end_date"] = end_date

        base_query += " ORDER BY dd.full_date, dc.commodity_id"

        with self._pool.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(base_query, params)
                rows = cur.fetchall()
                col_names = [desc[0] for desc in cur.description]

        df = pd.DataFrame(rows, columns=col_names)
        logger.info("Fetched %d rows from PostgreSQL", len(df))
        return df

    def _write_partitioned(self, df: pd.DataFrame) -> int:
        """Write the DataFrame to Hive-partitioned Parquet files.

        One file per (year, month) partition. Files are written to:
          {raw_path}/year={YYYY}/month={MM}/data.parquet

        Args:
            df: Full export DataFrame.

        Returns:
            Number of partitions written.
        """
        export_ts = datetime.now(tz=timezone.utc).isoformat()
        partitions = df.groupby(["year", "month"])
        count = 0

        for (year, month), partition_df in partitions:
            out_dir = self._config.raw_path / f"year={year}" / f"month={month}"
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / "data.parquet"

            # Cast to target schema with metadata
            table = self._to_arrow(partition_df)
            metadata = {
                b"source": b"oil_warehouse_db",
                b"export_timestamp": export_ts.encode(),
                b"record_count": str(len(partition_df)).encode(),
            }
            table = table.replace_schema_metadata(
                {**table.schema.metadata, **metadata} if table.schema.metadata else metadata
            )

            pq.write_table(
                table,
                out_path,
                compression="snappy",
            )
            logger.info(
                "Wrote %d rows to %s",
                len(partition_df),
                out_path,
                extra={"year": year, "month": month},
            )
            count += 1

        return count

    def _to_arrow(self, df: pd.DataFrame) -> pa.Table:
        """Convert a pandas DataFrame to a PyArrow Table using the target schema."""
        df = df.copy()

        # Convert Decimal columns to float64 (PostgreSQL numeric comes as Decimal)
        decimal_cols = ["open", "high", "low", "close", "adj_close",
                        "daily_change", "daily_change_pct"]
        for col in decimal_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").astype("float64")

        # Ensure trade_date is python date objects for pa.date32
        if "trade_date" in df.columns:
            df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date

        # Ensure created_at is UTC-aware timestamp
        if "created_at" in df.columns:
            df["created_at"] = pd.to_datetime(df["created_at"], utc=True)

        # Cast nullable int columns
        if "volume" in df.columns:
            df["volume"] = pd.to_numeric(df["volume"], errors="coerce").astype("Int64")

        table = pa.Table.from_pandas(df, schema=_PARQUET_SCHEMA, safe=False)
        return table