"""
Application-level validation for oil price DataFrames.

Applies business rules matching those in ``staging.sp_validate_staging_data()``
in the warehouse (plus additional Python-side checks), so bad data is caught
before it reaches the database.
"""

from __future__ import annotations

import logging
from datetime import date

import pandas as pd

logger = logging.getLogger(__name__)

# Sanity ceiling for oil prices in USD per barrel (or MMBtu / gallon)
_MAX_CLOSE_PRICE = 500.0


class PriceValidator:
    """Validates a DataFrame of OHLCV rows against a set of business rules.

    All rules are applied in a single pass; a row accumulates the descriptions
    of every rule it violates before being placed in the ``invalid`` partition.
    """

    def validate_dataframe(self, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Validate all rows in *df* and split into valid and invalid partitions.

        Rules applied:
        1.  ``close`` > 0
        2.  ``close`` < 500 (sanity ceiling for oil)
        3.  ``high`` >= ``low``
        4.  ``high`` >= ``open`` and ``high`` >= ``close``
        5.  ``low``  <= ``open`` and ``low``  <= ``close``
        6.  ``volume`` >= 0
        7.  ``trade_date`` not in the future
        8.  ``trade_date`` is a weekday (no weekend trades)
        9.  No null values in price columns (``open``, ``high``, ``low``, ``close``)
        10. No duplicate ``(symbol, trade_date)`` pairs within the batch

        Args:
            df: DataFrame with columns ``symbol``, ``trade_date``,
                ``open``, ``high``, ``low``, ``close``, ``adj_close``, ``volume``.

        Returns:
            ``(valid_df, invalid_df)`` where ``invalid_df`` has an extra
            ``validation_errors`` column containing a semicolon-separated
            description of every failed rule for that row.
        """
        if df.empty:
            return df.copy(), df.copy()

        work = df.copy()
        errors: list[list[str]] = [[] for _ in range(len(work))]
        today = date.today()

        for idx, (_, row) in enumerate(work.iterrows()):
            errs = errors[idx]

            # --- Rule 9: null price columns --------------------------------
            for col in ("open", "high", "low", "close"):
                val = row.get(col)
                if pd.isna(val):
                    errs.append(f"{col} is null")

            # Skip numeric checks if critical columns are null
            if errs:
                continue

            close = float(row["close"])
            high = float(row["high"])
            low = float(row["low"])
            open_ = float(row["open"])
            volume = row.get("volume")

            # --- Rule 1: close > 0 -----------------------------------------
            if close <= 0:
                errs.append(f"close must be > 0 (got {close})")

            # --- Rule 2: close < 500 ----------------------------------------
            if close >= _MAX_CLOSE_PRICE:
                errs.append(f"close {close} >= {_MAX_CLOSE_PRICE} (sanity limit)")

            # --- Rule 3: high >= low ----------------------------------------
            if high < low:
                errs.append(f"high ({high}) < low ({low})")

            # --- Rule 4: high >= open and close -----------------------------
            if high < open_:
                errs.append(f"high ({high}) < open ({open_})")
            if high < close:
                errs.append(f"high ({high}) < close ({close})")

            # --- Rule 5: low <= open and close ------------------------------
            if low > open_:
                errs.append(f"low ({low}) > open ({open_})")
            if low > close:
                errs.append(f"low ({low}) > close ({close})")

            # --- Rule 6: volume >= 0 ----------------------------------------
            if volume is not None and not pd.isna(volume) and float(volume) < 0:
                errs.append(f"volume ({volume}) < 0")

            # --- Rules 7 & 8: trade_date checks -----------------------------
            trade_date = row.get("trade_date")
            if trade_date is not None and not pd.isna(trade_date):
                td = trade_date if isinstance(trade_date, date) else pd.Timestamp(trade_date).date()
                if td > today:
                    errs.append(f"trade_date {td} is in the future")
                if td.weekday() >= 5:  # 5=Saturday, 6=Sunday
                    errs.append(f"trade_date {td} is a weekend")
            else:
                errs.append("trade_date is null")

        # Build error strings column on the working copy
        error_strings = ["; ".join(e) if e else "" for e in errors]
        work["_errors"] = error_strings

        # --- Rule 10: duplicates within the batch ---------------------------
        dup_mask = work.duplicated(subset=["symbol", "trade_date"], keep="first")
        for idx in work.index[dup_mask]:
            pos = work.index.get_loc(idx)
            if work.at[idx, "_errors"]:
                work.at[idx, "_errors"] += "; duplicate (symbol, trade_date)"
            else:
                work.at[idx, "_errors"] = "duplicate (symbol, trade_date)"
            _ = pos  # suppress unused warning

        # Split
        is_invalid = work["_errors"].str.len() > 0
        valid_df = work.loc[~is_invalid].drop(columns=["_errors"]).reset_index(drop=True)

        invalid_df = work.loc[is_invalid].copy()
        invalid_df = invalid_df.rename(columns={"_errors": "validation_errors"}).reset_index(drop=True)

        self._log_summary(df, valid_df, invalid_df)
        return valid_df, invalid_df

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _log_summary(
        original: pd.DataFrame,
        valid: pd.DataFrame,
        invalid: pd.DataFrame,
    ) -> None:
        """Log a concise validation summary."""
        total = len(original)
        n_valid = len(valid)
        n_invalid = len(invalid)

        logger.info(
            "Validation complete: %d total, %d valid, %d invalid",
            total,
            n_valid,
            n_invalid,
            extra={"total": total, "valid": n_valid, "invalid": n_invalid},
        )
        if n_invalid > 0 and not invalid.empty:
            # Aggregate error types for the summary
            all_errors: list[str] = []
            for err_str in invalid["validation_errors"]:
                all_errors.extend(e.strip() for e in str(err_str).split(";") if e.strip())
            from collections import Counter

            breakdown = Counter(all_errors)
            for msg, count in breakdown.most_common():
                logger.debug("  Validation error x%d: %s", count, msg)
