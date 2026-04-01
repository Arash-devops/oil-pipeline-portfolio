# Oil Price Ingestor

Batch service that fetches daily OHLCV energy commodity prices from Yahoo Finance and loads them into the PostgreSQL data warehouse.

---

## What it does

1. Calls `yfinance.download()` for each configured ticker symbol
2. Validates each row (price bounds, date sanity, required fields)
3. Batch-INSERTs valid rows into `staging.stg_oil_prices` (500 rows/batch)
4. Calls `sp_process_staging()` to promote validated rows to `warehouse.fact_oil_prices`
5. Prints a per-symbol ASCII summary table and exits with a meaningful exit code

---

## Commodities tracked

| Ticker | Instrument | Exchange |
|--------|-----------|---------|
| `CL=F` | WTI Crude Oil (West Texas Intermediate) | NYMEX |
| `BZ=F` | Brent Crude Oil | ICE |
| `NG=F` | Natural Gas | NYMEX |
| `HO=F` | Heating Oil (No. 2) | NYMEX |

Add or remove tickers by changing the `COMMODITIES` environment variable (comma-separated).

---

## Modes

| Command | What happens |
|---------|-------------|
| `backfill` | Fetches full history (default: 5 years) for all commodities |
| `incremental` | Fetches only rows newer than the latest date already in the warehouse |
| `refresh` | Truncates the staging table, then runs a full backfill |
| `health` | Checks database connectivity; exits 0 if reachable, 2 if not |

---

## Configuration

All settings are read from environment variables (or a `.env` file):

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_HOST` | `localhost` | PostgreSQL host |
| `DB_PORT` | `5432` | PostgreSQL port |
| `DB_NAME` | `oil_warehouse` | Database name |
| `DB_USER` | `arash` | Database user |
| `DB_PASSWORD` | `warehouse_dev_2026` | Database password |
| `COMMODITIES` | `CL=F,BZ=F,NG=F,HO=F` | Comma-separated ticker symbols |
| `SOURCE_NAME` | `Yahoo Finance` | Label written to `dim_source` |
| `LOG_LEVEL` | `INFO` | Python logging level |
| `RETRY_MAX_ATTEMPTS` | `3` | Max retries for network calls |
| `RETRY_BASE_DELAY` | `2.0` | Base delay (seconds) between retries |
| `BACKFILL_YEARS` | `5` | Years of history to fetch on backfill |
| `BATCH_SIZE` | `500` | Rows per INSERT batch |

Copy `.env.example` to `.env` and edit before running locally.

---

## How to run

### Docker (recommended)

```bash
# Full backfill (default)
docker compose run ingestor

# Incremental load
docker compose run ingestor python -m src.main incremental

# Connectivity check
docker compose run ingestor python -m src.main health
```

### Standalone (requires a local PostgreSQL with the warehouse schema)

```bash
cd services/ingestor
pip install -r requirements.txt
python -m src.main backfill
python -m src.main incremental
python -m src.main health
```

---

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | All symbols processed successfully |
| `1` | Partial failure (some symbols errored) |
| `2` | Total failure (all symbols errored, or DB unreachable) |

---

## Key implementation details

**Retry logic:** `tenacity` with exponential backoff — `wait_exponential(multiplier=1, min=RETRY_BASE_DELAY, max=60)`. Network errors from `yfinance` (connection timeouts, rate limits) are retried up to `RETRY_MAX_ATTEMPTS` times before the symbol is marked as `error` in the summary.

**Connection pooling:** `psycopg_pool.ConnectionPool` (sync) with min 2, max 10 connections. The pool opens eagerly on startup and closes in the `finally` block of each command handler.

**Validation rules:** non-null `symbol` and `price_close`; `price_close > 0`; `price_high >= price_low` when both present; `trade_date` is not in the future; `trade_date` is not a weekend. Failed rows are marked `is_valid = FALSE` with a semicolon-separated `validation_errors` string.

**Idempotency:** The warehouse fact table has a `UNIQUE (date_key, commodity_key, source_key)` constraint. The stored procedure uses `INSERT ... ON CONFLICT DO NOTHING`, making repeated runs safe.
