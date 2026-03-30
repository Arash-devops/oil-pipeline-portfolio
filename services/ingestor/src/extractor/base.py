"""Abstract base class for all data source extractors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

import pandas as pd


class BaseExtractor(ABC):
    """Contract every data-source extractor must satisfy.

    Concrete subclasses implement the three abstract methods.
    The pipeline depends only on this interface, making it easy to swap
    Yahoo Finance for another data provider without touching the pipeline.
    """

    @abstractmethod
    def fetch_historical(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        """Fetch OHLCV data for *symbol* between *start_date* and *end_date*.

        Args:
            symbol:     Ticker symbol recognised by the data source.
            start_date: Inclusive start of the requested date range.
            end_date:   Inclusive end of the requested date range.

        Returns:
            DataFrame with columns:
            ``symbol``, ``trade_date``, ``open``, ``high``, ``low``,
            ``close``, ``adj_close``, ``volume``.
            Returns an empty DataFrame if no data is available.
        """

    @abstractmethod
    def fetch_latest(self, symbol: str, days: int = 7) -> pd.DataFrame:
        """Fetch the most recent *days* of OHLCV data for *symbol*.

        Useful for catching gaps in incremental loads without fetching
        the full history.

        Args:
            symbol: Ticker symbol.
            days:   Number of calendar days to look back from today.

        Returns:
            Same schema as :meth:`fetch_historical`.
        """

    @abstractmethod
    def get_last_available_date(self, symbol: str) -> date | None:
        """Query the warehouse for the most recent date loaded for *symbol*.

        Args:
            symbol: Commodity ticker symbol.

        Returns:
            The most recent ``full_date`` in ``fact_oil_prices`` for this
            symbol, or ``None`` if no data has ever been loaded.
        """
