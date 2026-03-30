"""
Gold layer aggregator: produces serving-ready analytical datasets.

Reads from silver curated Parquet files using DuckDB and writes three
serving datasets: monthly_summary, price_metrics, and commodity_comparison.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

from src.config import Settings

logger = logging.getLogger(__name__)


class GoldAggregator:
    """Produces gold-layer serving datasets from silver-layer Parquet files.

    Args:
        config: Application settings with data path configuration.
    """

    def __init__(self, config: Settings) -> None:
        self._config = config

    def aggregate(self) -> dict[str, Any]:
        """Run all three gold aggregations.

        Returns:
            Stats dict with rows written per dataset and total duration.
        """
        t0 = datetime.now(tz=timezone.utc)
        curated_glob = str(self._config.curated_path / "**" / "*.parquet")

        con = duckdb.connect(":memory:")
        try:
            # Check if any curated files exist
            try:
                con.execute(
                    f"CREATE VIEW curated AS "
                    f"SELECT * FROM read_parquet('{curated_glob}', hive_partitioning=true)"
                )
                row_count = con.execute("SELECT COUNT(*) FROM curated").fetchone()[0]
            except Exception as exc:
                logger.warning("No curated data available: %s", exc)
                return {
                    "monthly_summary_rows": 0,
                    "price_metrics_rows": 0,
                    "commodity_comparison_rows": 0,
                    "duration_seconds": 0.0,
                }

            if row_count == 0:
                logger.warning("Curated layer is empty; skipping gold aggregation.")
                return {
                    "monthly_summary_rows": 0,
                    "price_metrics_rows": 0,
                    "commodity_comparison_rows": 0,
                    "duration_seconds": 0.0,
                }

            ms_rows = self._write_monthly_summary(con)
            pm_rows = self._write_price_metrics(con)
            cc_rows = self._write_commodity_comparison(con)
        finally:
            con.close()

        duration = (datetime.now(tz=timezone.utc) - t0).total_seconds()
        stats = {
            "monthly_summary_rows": ms_rows,
            "price_metrics_rows": pm_rows,
            "commodity_comparison_rows": cc_rows,
            "duration_seconds": round(duration, 2),
        }
        logger.info("Gold aggregation complete: %s", stats)
        return stats

    # ------------------------------------------------------------------
    # Private: individual aggregations
    # ------------------------------------------------------------------

    def _write_monthly_summary(self, con: duckdb.DuckDBPyConnection) -> int:
        """Aggregate monthly price statistics per commodity.

        Args:
            con: Open DuckDB connection with 'curated' view registered.

        Returns:
            Number of rows written.
        """
        sql = """
        SELECT
            symbol,
            commodity_name,
            year,
            month,
            COUNT(*)                            AS trading_days,
            ROUND(AVG(close), 4)                AS avg_close,
            ROUND(MIN(close), 4)                AS min_close,
            ROUND(MAX(close), 4)                AS max_close,
            ROUND(STDDEV_SAMP(close), 4)        AS stddev_close,
            SUM(volume)                         AS total_volume,
            ROUND(
                (LAST_VALUE(close) OVER (
                    PARTITION BY symbol, year, month
                    ORDER BY trade_date
                    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
                ) - FIRST_VALUE(close) OVER (
                    PARTITION BY symbol, year, month
                    ORDER BY trade_date
                    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
                )) / NULLIF(FIRST_VALUE(close) OVER (
                    PARTITION BY symbol, year, month
                    ORDER BY trade_date
                    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
                ), 0) * 100, 4
            )                                   AS monthly_return_pct
        FROM curated
        WHERE quality_flag = 'valid'
        GROUP BY symbol, commodity_name, year, month,
                 trade_date, close
        """
        # Simpler version without window-in-GROUP-BY conflict
        sql = """
        WITH ranked AS (
            SELECT
                symbol,
                commodity_name,
                year,
                month,
                trade_date,
                close,
                volume,
                ROW_NUMBER() OVER (PARTITION BY symbol, year, month ORDER BY trade_date ASC)  AS rn_first,
                ROW_NUMBER() OVER (PARTITION BY symbol, year, month ORDER BY trade_date DESC) AS rn_last
            FROM curated
            WHERE quality_flag = 'valid'
        ),
        bounds AS (
            SELECT symbol, year, month,
                MAX(CASE WHEN rn_first = 1 THEN close END) AS month_open,
                MAX(CASE WHEN rn_last  = 1 THEN close END) AS month_close
            FROM ranked
            GROUP BY symbol, year, month
        ),
        agg AS (
            SELECT
                c.symbol,
                c.commodity_name,
                c.year,
                c.month,
                COUNT(*)                         AS trading_days,
                ROUND(AVG(c.close), 4)           AS avg_close,
                ROUND(MIN(c.close), 4)           AS min_close,
                ROUND(MAX(c.close), 4)           AS max_close,
                ROUND(STDDEV_SAMP(c.close), 4)   AS stddev_close,
                SUM(c.volume)                    AS total_volume
            FROM curated c
            WHERE c.quality_flag = 'valid'
            GROUP BY c.symbol, c.commodity_name, c.year, c.month
        )
        SELECT
            a.*,
            ROUND((b.month_close - b.month_open) / NULLIF(b.month_open, 0) * 100, 4)
                AS monthly_return_pct
        FROM agg a
        JOIN bounds b ON b.symbol = a.symbol AND b.year = a.year AND b.month = a.month
        ORDER BY a.symbol, a.year, a.month
        """
        return self._run_and_write(con, sql, "monthly_summary")

    def _write_price_metrics(self, con: duckdb.DuckDBPyConnection) -> int:
        """Compute rolling moving averages, volatility, and Bollinger bands.

        Args:
            con: Open DuckDB connection with 'curated' view registered.

        Returns:
            Number of rows written.
        """
        sql = """
        SELECT
            symbol,
            trade_date,
            close,
            ROUND(AVG(close) OVER (
                PARTITION BY symbol ORDER BY trade_date
                ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
            ), 4)                                                     AS ma7,
            ROUND(AVG(close) OVER (
                PARTITION BY symbol ORDER BY trade_date
                ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
            ), 4)                                                     AS ma30,
            ROUND(AVG(close) OVER (
                PARTITION BY symbol ORDER BY trade_date
                ROWS BETWEEN 89 PRECEDING AND CURRENT ROW
            ), 4)                                                     AS ma90,
            ROUND(STDDEV_SAMP(close) OVER (
                PARTITION BY symbol ORDER BY trade_date
                ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
            ), 4)                                                     AS volatility_20d,
            ROUND(AVG(close) OVER (
                PARTITION BY symbol ORDER BY trade_date
                ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
            ) + 2 * STDDEV_SAMP(close) OVER (
                PARTITION BY symbol ORDER BY trade_date
                ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
            ), 4)                                                     AS bollinger_upper,
            ROUND(AVG(close) OVER (
                PARTITION BY symbol ORDER BY trade_date
                ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
            ) - 2 * STDDEV_SAMP(close) OVER (
                PARTITION BY symbol ORDER BY trade_date
                ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
            ), 4)                                                     AS bollinger_lower
        FROM curated
        WHERE quality_flag = 'valid'
        ORDER BY symbol, trade_date
        """
        return self._run_and_write(con, sql, "price_metrics")

    def _write_commodity_comparison(self, con: duckdb.DuckDBPyConnection) -> int:
        """Compute daily WTI/Brent price spread and ratio.

        Args:
            con: Open DuckDB connection with 'curated' view registered.

        Returns:
            Number of rows written.
        """
        sql = """
        SELECT
            wti.trade_date,
            wti.close                                            AS wti_close,
            brent.close                                          AS brent_close,
            ROUND(wti.close - brent.close, 4)                   AS spread,
            ROUND(wti.close / NULLIF(brent.close, 0), 6)        AS ratio
        FROM curated wti
        JOIN curated brent
            ON wti.trade_date = brent.trade_date
           AND brent.symbol   = 'BZ=F'
        WHERE wti.symbol       = 'CL=F'
          AND wti.quality_flag = 'valid'
          AND brent.quality_flag = 'valid'
        ORDER BY wti.trade_date
        """
        return self._run_and_write(con, sql, "commodity_comparison")

    def _run_and_write(
        self,
        con: duckdb.DuckDBPyConnection,
        sql: str,
        dataset_name: str,
    ) -> int:
        """Execute a DuckDB query and write the result as a Parquet file.

        Args:
            con: Open DuckDB connection.
            sql: Query to execute.
            dataset_name: Name of the serving dataset (used as directory name).

        Returns:
            Number of rows written.
        """
        try:
            arrow_table = con.execute(sql).fetch_arrow_table()
            row_count = arrow_table.num_rows

            out_dir = self._config.serving_path / dataset_name
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / "data.parquet"

            pq.write_table(arrow_table, out_path, compression="snappy")
            logger.info(
                "Wrote %d rows to serving/%s/data.parquet",
                row_count,
                dataset_name,
            )
            return row_count
        except Exception as exc:
            logger.error("Failed to write serving dataset '%s': %s", dataset_name, exc)
            return 0
