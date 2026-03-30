"""
PostgreSQL data loader.

Responsible for:
- Batch-inserting validated rows into ``staging.stg_oil_prices``
- Invoking the warehouse stored procedures (sp_process_staging, etc.)
- Querying commodity surrogate keys for metrics calculation
"""

from __future__ import annotations

import logging
from datetime import date

import pandas as pd

from src.config import Settings
from src.utils.db_connection import ConnectionPool

logger = logging.getLogger(__name__)


class PostgresLoader:
    """Loads validated DataFrames into the oil_warehouse staging table
    and drives the downstream stored procedures.

    Args:
        pool:        Shared connection pool.
        config:      Application settings (SOURCE_NAME, BATCH_SIZE).
    """

    _INSERT_SQL = """
        INSERT INTO staging.stg_oil_prices
            (symbol, trade_date, price_open, price_high, price_low,
             price_close, adj_close, volume, source_name,
             is_processed, is_valid)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, FALSE, NULL)
        ON CONFLICT DO NOTHING
    """

    def __init__(self, pool: ConnectionPool, config: Settings) -> None:
        self._pool = pool
        self._config = config

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_to_staging(self, df: pd.DataFrame) -> int:
        """Batch-insert rows from *df* into ``staging.stg_oil_prices``.

        Uses ``cursor.executemany`` which psycopg3 pipelines automatically.
        NaN values are converted to ``None`` so they map to SQL NULL.

        Args:
            df: Validated DataFrame with standardised column names.

        Returns:
            Number of rows inserted.
        """
        if df.empty:
            return 0

        rows = [
            (
                row["symbol"],
                row["trade_date"],
                self._to_python(row.get("open")),
                self._to_python(row.get("high")),
                self._to_python(row.get("low")),
                self._to_python(row.get("close")),
                self._to_python(row.get("adj_close")),
                int(row["volume"]) if pd.notna(row.get("volume")) else None,
                self._config.SOURCE_NAME,
            )
            for _, row in df.iterrows()
        ]

        with self._pool.get_connection() as conn:
            with conn.cursor() as cur:
                cur.executemany(self._INSERT_SQL, rows)

        logger.info(
            "Loaded %d rows to staging.stg_oil_prices",
            len(rows),
            extra={"rows_inserted": len(rows)},
        )
        return len(rows)

    def process_staging(self) -> dict[str, int]:
        """Call ``warehouse.sp_process_staging()`` to promote staged rows.

        Returns:
            Dict with keys ``processed``, ``skipped``, ``errors``.
        """
        sql = "SELECT * FROM warehouse.sp_process_staging()"
        with self._pool.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                row = cur.fetchone()

        if row is None:
            result = {"processed": 0, "skipped": 0, "errors": 0}
        else:
            result = {"processed": row[0], "skipped": row[1], "errors": row[2]}

        logger.info(
            "sp_process_staging: processed=%d skipped=%d errors=%d",
            result["processed"],
            result["skipped"],
            result["errors"],
            extra=result,
        )
        return result

    def calculate_metrics(
        self,
        commodity_key: int,
        start_date: date,
        end_date: date,
    ) -> None:
        """Call ``analytics.sp_calculate_metrics()`` for one commodity.

        Args:
            commodity_key: Surrogate key from ``dim_commodity``.
            start_date:    Start of the date range to (re)calculate.
            end_date:      End of the date range to (re)calculate.
        """
        sql = "SELECT analytics.sp_calculate_metrics(%s, %s, %s)"
        with self._pool.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (commodity_key, start_date, end_date))

        logger.info(
            "sp_calculate_metrics: commodity_key=%d, %s to %s",
            commodity_key,
            start_date,
            end_date,
        )

    def aggregate_monthly(self, year: int, month: int) -> None:
        """Call ``analytics.sp_aggregate_monthly()`` for one month.

        Args:
            year:  Calendar year.
            month: Calendar month (1-12).
        """
        sql = "SELECT analytics.sp_aggregate_monthly(%s, %s)"
        with self._pool.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (year, month))

        logger.info("sp_aggregate_monthly: %d-%02d", year, month)

    def get_commodity_keys(self) -> dict[str, int]:
        """Return a mapping of ticker symbol to surrogate commodity_key.

        Queries only current (``is_current = TRUE``) dimension rows.

        Returns:
            Dict like ``{'CL=F': 1, 'BZ=F': 2, ...}``.
        """
        sql = """
            SELECT commodity_id, commodity_key
            FROM   warehouse.dim_commodity
            WHERE  is_current = TRUE
        """
        with self._pool.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                rows = cur.fetchall()

        result = {row[0]: row[1] for row in rows}
        logger.debug("Commodity key map: %s", result)
        return result

    def truncate_staging(self) -> None:
        """Truncate ``staging.stg_oil_prices`` for a full refresh."""
        with self._pool.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("TRUNCATE TABLE staging.stg_oil_prices RESTART IDENTITY")
        logger.info("staging.stg_oil_prices truncated.")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_python(value: object) -> float | None:
        """Convert NaN/None to Python None; otherwise return float."""
        if value is None:
            return None
        try:
            import math
            f = float(value)
            return None if math.isnan(f) else f
        except (TypeError, ValueError):
            return None
