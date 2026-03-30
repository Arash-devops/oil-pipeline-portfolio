"""
DuckDB query engine: registers all lakehouse layers as views and exposes
convenience query methods.
"""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from src.config import Settings

logger = logging.getLogger(__name__)

_EMPTY_DF = pd.DataFrame()


class DuckDBEngine:
    """In-memory DuckDB engine with views over the three lakehouse layers.

    Args:
        config: Application settings with data path configuration.
    """

    def __init__(self, config: Settings) -> None:
        self._config = config
        self._con = duckdb.connect(":memory:")
        self._register_views()

    # ------------------------------------------------------------------
    # View registration
    # ------------------------------------------------------------------

    def _register_views(self) -> None:
        """Register raw, curated, and serving Parquet paths as DuckDB views.

        Views are only created if at least one matching Parquet file exists.
        Missing layers produce a warning but do not raise.
        """
        layers = {
            "raw": str(self._config.raw_path / "**" / "*.parquet"),
            "curated": str(self._config.curated_path / "**" / "*.parquet"),
        }
        for view_name, glob in layers.items():
            self._safe_create_view(
                view_name,
                f"SELECT * FROM read_parquet('{glob}', hive_partitioning=true)",
            )

        serving_datasets = ["monthly_summary", "price_metrics", "commodity_comparison"]
        for ds in serving_datasets:
            path = self._config.serving_path / ds / "data.parquet"
            if path.exists():
                self._safe_create_view(
                    ds,
                    f"SELECT * FROM read_parquet('{path}')",
                )
            else:
                logger.debug("Serving dataset '%s' not found, skipping view.", ds)

    def _safe_create_view(self, name: str, sql: str) -> None:
        """Create a DuckDB view, logging a warning on failure.

        Args:
            name: View name.
            sql: SELECT statement for the view body.
        """
        try:
            self._con.execute(f"CREATE OR REPLACE VIEW {name} AS {sql}")
            logger.debug("Registered DuckDB view: %s", name)
        except Exception as exc:
            logger.warning("Could not register view '%s': %s", name, exc)

    # ------------------------------------------------------------------
    # Public query API
    # ------------------------------------------------------------------

    def query(self, sql: str) -> pd.DataFrame:
        """Execute an arbitrary SQL statement and return results as a DataFrame.

        Args:
            sql: SQL query string.

        Returns:
            Results DataFrame, or empty DataFrame on error.
        """
        try:
            return self._con.execute(sql).df()
        except Exception as exc:
            logger.error("Query failed: %s — SQL: %s", exc, sql[:200])
            return _EMPTY_DF.copy()

    def get_latest_prices(self) -> pd.DataFrame:
        """Return the most recent close price for each commodity.

        Returns:
            DataFrame with columns: symbol, trade_date, close.
        """
        sql = """
        SELECT symbol, MAX(trade_date) AS trade_date, close
        FROM curated
        WHERE trade_date = (
            SELECT MAX(trade_date) FROM curated c2
            WHERE c2.symbol = curated.symbol
        )
        GROUP BY symbol, close
        ORDER BY symbol
        """
        return self._safe_query(sql, "get_latest_prices")

    def get_price_history(
        self,
        commodity: str,
        start: date,
        end: date,
    ) -> pd.DataFrame:
        """Return daily price history for a commodity within a date range.

        Args:
            commodity: Ticker symbol (e.g. 'CL=F').
            start: Inclusive start date.
            end: Inclusive end date.

        Returns:
            DataFrame ordered by trade_date ascending.
        """
        sql = f"""
        SELECT trade_date, open, high, low, close, adj_close, volume,
               daily_return_pct, quality_flag
        FROM curated
        WHERE symbol = '{commodity}'
          AND trade_date BETWEEN DATE '{start.isoformat()}' AND DATE '{end.isoformat()}'
        ORDER BY trade_date
        """
        return self._safe_query(sql, "get_price_history")

    def get_monthly_summary(self, year: int | None = None) -> pd.DataFrame:
        """Return monthly aggregation data, optionally filtered by year.

        Args:
            year: Optional calendar year filter.

        Returns:
            DataFrame from the monthly_summary serving dataset.
        """
        year_filter = f"WHERE year = {year}" if year is not None else ""
        sql = f"SELECT * FROM monthly_summary {year_filter} ORDER BY symbol, year, month"
        return self._safe_query(sql, "get_monthly_summary")

    def get_commodity_spread(self, start: date, end: date) -> pd.DataFrame:
        """Return WTI/Brent spread data for a date range.

        Args:
            start: Inclusive start date.
            end: Inclusive end date.

        Returns:
            DataFrame with columns: trade_date, wti_close, brent_close, spread, ratio.
        """
        sql = f"""
        SELECT *
        FROM commodity_comparison
        WHERE trade_date BETWEEN DATE '{start.isoformat()}' AND DATE '{end.isoformat()}'
        ORDER BY trade_date
        """
        return self._safe_query(sql, "get_commodity_spread")

    def layer_stats(self) -> dict[str, Any]:
        """Return row counts and file sizes for each layer.

        Returns:
            Dict mapping layer names to stats dicts with 'rows' and 'size_mb'.
        """
        stats: dict[str, Any] = {}

        layers = {
            "raw": self._config.raw_path,
            "curated": self._config.curated_path,
            "serving/monthly_summary": self._config.serving_path / "monthly_summary",
            "serving/price_metrics": self._config.serving_path / "price_metrics",
            "serving/commodity_comparison": self._config.serving_path / "commodity_comparison",
        }

        for layer_name, layer_path in layers.items():
            parquet_files = list(layer_path.rglob("*.parquet")) if layer_path.exists() else []
            total_bytes = sum(f.stat().st_size for f in parquet_files)
            size_mb = round(total_bytes / (1024 * 1024), 3)

            row_count = 0
            if parquet_files:
                view_name = layer_name.replace("/", "_")
                glob = str(layer_path / "**" / "*.parquet")
                try:
                    row_count = self._con.execute(
                        f"SELECT COUNT(*) FROM read_parquet('{glob}', hive_partitioning=true)"
                    ).fetchone()[0]
                except Exception:
                    row_count = 0

            stats[layer_name] = {"rows": row_count, "size_mb": size_mb}

        return stats

    def close(self) -> None:
        """Close the DuckDB in-memory connection."""
        self._con.close()
        logger.debug("DuckDB connection closed.")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _safe_query(self, sql: str, method_name: str) -> pd.DataFrame:
        """Execute SQL, returning an empty DataFrame on any error.

        Args:
            sql: SQL query to execute.
            method_name: Used in log messages for traceability.

        Returns:
            Results DataFrame or empty DataFrame on error.
        """
        try:
            return self._con.execute(sql).df()
        except Exception as exc:
            logger.warning("%s: query failed (%s); returning empty DataFrame.", method_name, exc)
            return _EMPTY_DF.copy()
