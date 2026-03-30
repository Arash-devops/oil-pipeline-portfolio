# Oil Price Ingestion Service

Python service that pulls OHLCV data from Yahoo Finance and loads it into the
`oil_warehouse` PostgreSQL data warehouse via a staging-first ELT pipeline.

## Architecture

```
Yahoo Finance API
      |
      v
[YahooFinanceExtractor]  -- yfinance library
      |
      | pandas DataFrame (symbol, trade_date, open, high, low, close, adj_close, volume)
      v
[PriceValidator]         -- 10 business rules applied in a single pass
      |
      | (valid_df, invalid_df)
      v
[PostgresLoader]
  |-- load_to_staging()         INSERT into staging.stg_oil_prices (batch)
  |-- process_staging()         CALL warehouse.sp_process_staging()
  |-- calculate_metrics()       CALL analytics.sp_calculate_metrics()
  |-- aggregate_monthly()       CALL analytics.sp_aggregate_monthly()
      |
      v
PostgreSQL oil_warehouse
  staging.stg_oil_prices       (raw landing)
  warehouse.fact_oil_prices    (clean, conformed)
  analytics.price_metrics      (MA, RSI, volatility)
  analytics.monthly_summary    (monthly aggregates)
```

## Setup

```bash
cd services/ingestor
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your database credentials
```

## Usage

```bash
# Full historical backfill (5 years by default)
python -m src.main backfill

# Incremental load (only new data since last run)
python -m src.main incremental

# Full refresh (truncate staging + backfill)
python -m src.main refresh

# Health check
python -m src.main health
```

## Run with Docker

```bash
# Build
docker build -t oil-price-ingestor .

# Run (pass credentials via environment)
docker run --rm \
  -e DB_HOST=host.docker.internal \
  -e DB_PASSWORD=warehouse_dev_2026 \
  oil-price-ingestor incremental
```

## Configuration Reference

| Variable | Default | Description |
|---|---|---|
| DB_HOST | localhost | PostgreSQL host |
| DB_PORT | 5432 | PostgreSQL port |
| DB_NAME | oil_warehouse | Database name |
| DB_USER | arash | Database user |
| DB_PASSWORD | (required) | Database password |
| COMMODITIES | CL=F,BZ=F,NG=F,HO=F | Comma-separated ticker symbols |
| SOURCE_NAME | Yahoo Finance | Label written to dim_source |
| LOG_LEVEL | INFO | Python logging level |
| RETRY_MAX_ATTEMPTS | 3 | Network retry attempts |
| RETRY_BASE_DELAY | 2.0 | Base delay in seconds (exponential backoff) |
| BACKFILL_YEARS | 5 | Years of history for full backfill |
| BATCH_SIZE | 500 | Rows per staging INSERT batch |

## Validation Rules

Each row is checked against 10 rules before reaching the database:

1. `close` > 0
2. `close` < 500 (sanity ceiling for oil prices)
3. `high` >= `low`
4. `high` >= `open` and `high` >= `close`
5. `low` <= `open` and `low` <= `close`
6. `volume` >= 0
7. `trade_date` not in the future
8. `trade_date` is a weekday
9. No null values in price columns
10. No duplicate `(symbol, trade_date)` pairs within the batch

Invalid rows are logged with their error descriptions. They never reach the
warehouse but remain in `staging.stg_oil_prices` with `is_valid = FALSE`
for audit purposes.

## Error Handling

- **Yahoo Finance down**: the extractor returns an empty DataFrame;
  the pipeline logs a warning and skips the commodity for this run.
- **Single commodity failure**: logged as an error; all other
  commodities in the run continue normally.
- **Database connection failure**: the ConnectionPool raises an
  exception which propagates to `main.py` and exits with code 2.
- **Partial failure**: if some but not all commodities fail, exit code 1
  is returned so the caller (e.g. Airflow) can distinguish from total failure.

## Running Tests

```bash
pytest tests/ -v
```
