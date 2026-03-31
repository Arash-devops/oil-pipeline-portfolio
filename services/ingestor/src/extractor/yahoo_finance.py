"""
Yahoo Finance extractor using the yfinance library.

Fetches OHLCV data and normalises it into a standard DataFrame schema
expected by the rest of the pipeline.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta

import pandas as pd
import yfinance as yf

from src.extractor.base import BaseExtractor
from src.utils.db_connection import ConnectionPool
from src.utils.retry import retry

logger = logging.getLogger(__name__)

# Columns emitted by this extractor — every downstream component relies on these names
STANDARD_COLUMNS = ["symbol", "trade_date", "open", "high", "low", "close", "adj_close", "volume"]

_NETWORK_ERRORS = (
    ConnectionError,
    TimeoutError,
    OSError,
)


class YahooFinanceExtractor(BaseExtractor):
    """Fetches oil price OHLCV data from Yahoo Finance via *yfinance*.

    Args:
        db_pool:     Connection pool used only by :meth:`get_last_available_date`.
        source_name: Human-readable label written to ``dim_source``.
    """

    def __init__(self, db_pool: ConnectionPool, source_name: str = "Yahoo Finance") -> None:
        self._db_pool = db_pool
        self._source_name = source_name

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    @retry(max_attempts=3, base_delay=2.0, exceptions=_NETWORK_ERRORS)
    def fetch_historical(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        """Fetch OHLCV data from Yahoo Finance for the given date range.

        Args:
            symbol:     Yahoo Finance ticker (e.g. 'CL=F').
            start_date: Inclusive start date.
            end_date:   Inclusive end date.

        Returns:
            Standardised DataFrame or an empty DataFrame if no data is found.
        """
        logger.info(
            "Fetching %s from %s to %s",
            symbol,
            start_date.isoformat(),
            end_date.isoformat(),
            extra={"symbol": symbol},
        )

        # yfinance end date is exclusive, so add one day
        yf_end = end_date + timedelta(days=1)

        try:
            ticker = yf.Ticker(symbol)
            raw: pd.DataFrame = ticker.history(
                start=start_date.isoformat(),
                end=yf_end.isoformat(),
                auto_adjust=False,
            )
        except Exception as exc:
            logger.error("yfinance error for %s: %s", symbol, exc, extra={"symbol": symbol})
            return self._empty_frame()

        if raw is None or raw.empty:
            logger.warning(
                "No data returned by Yahoo Finance for %s (%s to %s)",
                symbol,
                start_date,
                end_date,
                extra={"symbol": symbol},
            )
            return self._empty_frame()

        df = self._normalise(raw, symbol)
        logger.info(
            "Fetched %d rows for %s",
            len(df),
            symbol,
            extra={"symbol": symbol, "rows": len(df)},
        )
        return df

    @retry(max_attempts=3, base_delay=2.0, exceptions=_NETWORK_ERRORS)
    def fetch_latest(self, symbol: str, days: int = 7) -> pd.DataFrame:
        """Fetch the most recent *days* of data for *symbol*.

        Args:
            symbol: Yahoo Finance ticker.
            days:   Calendar days to look back from today.

        Returns:
            Standardised DataFrame or empty DataFrame.
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        return self.fetch_historical(symbol, start_date, end_date)

    def get_last_available_date(self, symbol: str) -> date | None:
        """Query the warehouse for the latest loaded date for *symbol*.

        Queries ``warehouse.fact_oil_prices`` joined to ``dim_commodity``
        and ``dim_date`` to find the maximum trade date already present.

        Args:
            symbol: Commodity ticker (e.g. 'CL=F').

        Returns:
            The most recent date in the fact table, or ``None`` if the
            warehouse has no data for this symbol yet.
        """
        sql = """
            SELECT MAX(d.full_date)
            FROM   warehouse.fact_oil_prices f
            JOIN   warehouse.dim_commodity   c ON c.commodity_key = f.commodity_key
            JOIN   warehouse.dim_date        d ON d.date_key      = f.date_key
            WHERE  c.commodity_id = %s
              AND  c.is_current   = TRUE
        """
        try:
            with self._db_pool.get_connection() as conn, conn.cursor() as cur:
                cur.execute(sql, (symbol,))
                row = cur.fetchone()
                result = row[0] if row and row[0] is not None else None
                if result:
                    logger.debug(
                        "Last available date for %s: %s",
                        symbol,
                        result,
                        extra={"symbol": symbol},
                    )
                else:
                    logger.info(
                        "No existing data found for %s (first run).",
                        symbol,
                        extra={"symbol": symbol},
                    )
                return result
        except Exception as exc:
            logger.error(
                "Failed to query last available date for %s: %s",
                symbol,
                exc,
                extra={"symbol": symbol},
            )
            return None

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalise(raw: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Convert a raw yfinance DataFrame to the standard pipeline schema.

        Args:
            raw:    DataFrame as returned by ``yf.Ticker.history()``.
            symbol: Ticker symbol to embed in the ``symbol`` column.

        Returns:
            DataFrame with exactly the columns in ``STANDARD_COLUMNS``.
        """
        # Strip timezone info from the DatetimeIndex
        index = raw.index
        if hasattr(index, "tz") and index.tz is not None:
            index = index.tz_convert("UTC").tz_localize(None)

        # Build the standardised frame
        adj_close_col = raw.get("Adj Close", raw["Close"])
        df = pd.DataFrame(
            {
                "symbol": symbol,
                "trade_date": index.date,
                "open": pd.to_numeric(raw["Open"], errors="coerce"),
                "high": pd.to_numeric(raw["High"], errors="coerce"),
                "low": pd.to_numeric(raw["Low"], errors="coerce"),
                "close": pd.to_numeric(raw["Close"], errors="coerce"),
                "adj_close": pd.to_numeric(adj_close_col, errors="coerce"),
                "volume": pd.to_numeric(raw["Volume"], errors="coerce").fillna(0).astype("int64"),
            }
        )
        return df.reset_index(drop=True)

    @staticmethod
    def _empty_frame() -> pd.DataFrame:
        """Return an empty DataFrame with the standard column schema."""
        return pd.DataFrame(columns=STANDARD_COLUMNS)
