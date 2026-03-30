"""
Shared query parameter constants and validators.

Query parameters are defined inline in router endpoint signatures using
FastAPI's Query(). This module holds shared constants used across routers.
"""

from datetime import date

# Valid commodity ticker symbols loaded in the warehouse.
VALID_COMMODITIES: list[str] = ["CL=F", "BZ=F", "NG=F", "HO=F"]

# Pagination defaults.
DEFAULT_LIMIT: int = 100
MAX_LIMIT: int = 1000

# Earliest date present in the warehouse.
EARLIEST_DATE: date = date(2021, 3, 29)
