# Oil Price Lakehouse

Batch service that transforms the PostgreSQL data warehouse into a medallion-architecture Parquet lakehouse. Implements Bronze → Silver → Gold layers using PyArrow for Parquet I/O and DuckDB for in-process SQL transformations.

---

## What it does

Reads `warehouse.fact_oil_prices` (joined to dimension tables) from PostgreSQL and writes a three-layer Parquet lakehouse:

1. **Bronze** — exact copy of the warehouse, Hive-partitioned by symbol, year, and month
2. **Silver** — validated, null-filled, and type-coerced version of Bronze
3. **Gold** — three analytical serving datasets consumed by the FastAPI analytics endpoints

---

## Medallion layers

### Bronze — Raw Ingest

**Path:** `{DATA_DIR}/raw/oil_prices/symbol=CL=F/year=2024/month=01/data.parquet`

Exact projection from `fact_oil_prices` with dimension attributes denormalized in. Written with a fixed PyArrow schema (typed columns, no implicit inference). Compression: snappy.

### Silver — Curated

**Path:** `{DATA_DIR}/curated/oil_prices/symbol=CL=F/year=2024/month=01/data.parquet`

Applies these transformations over Bronze via DuckDB:
- Forward-fill OHLCV nulls within each symbol partition
- Replace remaining nulls with 0 (volume) or previous-close (price changes)
- Cast all price columns to `DOUBLE PRECISION`
- Filter rows with `price_close <= 0`
- Write a per-partition quality report to `{DATA_DIR}/curated/_quality_report/`

### Gold — Serving

**Path:** `{DATA_DIR}/serving/{dataset_name}/data.parquet`

Three datasets written as flat (non-partitioned) Parquet files:

| Dataset | Columns | Description |
|---------|---------|-------------|
| `monthly_summary` | `symbol`, `commodity_name`, `year`, `month`, `trading_days`, `avg_close`, `min_close`, `max_close`, `stddev_close`, `total_volume`, `monthly_return_pct` | Monthly price aggregations per commodity |
| `price_metrics` | `symbol`, `trade_date`, `close`, `ma7`, `ma30`, `ma90`, `volatility_20d`, `bollinger_upper`, `bollinger_lower` | Rolling statistics per trading day |
| `commodity_comparison` | `trade_date`, `wti_close`, `brent_close`, `spread`, `ratio` | Daily WTI vs Brent spread and price ratio |

---

## Output file structure

```
data/
├── raw/
│   └── oil_prices/
│       ├── symbol=BZ=F/year=2020/month=01/data.parquet
│       ├── symbol=CL=F/...
│       ├── symbol=HO=F/...
│       └── symbol=NG=F/...
├── curated/
│   ├── oil_prices/          (same Hive partition structure as raw/)
│   └── _quality_report/
└── serving/
    ├── monthly_summary/data.parquet
    ├── price_metrics/data.parquet
    └── commodity_comparison/data.parquet
```

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_HOST` | `localhost` | PostgreSQL host |
| `DB_PORT` | `5432` | PostgreSQL port |
| `DB_NAME` | `oil_warehouse` | Database name |
| `DB_USER` | `arash` | Database user |
| `DB_PASSWORD` | `warehouse_dev_2026` | Database password |
| `DATA_DIR` | `data` | Root directory for Parquet output |
| `LOG_LEVEL` | `INFO` | Python logging level |

In Docker Compose, `DATA_DIR=/app/data` and the `lakehouse-data` volume is mounted at `/app/data`. The API mounts the same volume at `/opt/lakehouse/data` (read-only).

---

## How to run

### Docker (recommended)

```bash
# Full pipeline (export → transform → aggregate)
docker compose run lakehouse

# Individual stages
docker compose run lakehouse python -m src.main export
docker compose run lakehouse python -m src.main transform
docker compose run lakehouse python -m src.main aggregate

# Interactive SQL prompt over all layers
docker compose run lakehouse python -m src.main query

# Layer statistics
docker compose run lakehouse python -m src.main stats

# Incremental export (specific date range)
docker compose run lakehouse python -m src.main export \
  --start-date 2024-01-01 --end-date 2024-03-31
```

### Standalone

```bash
cd services/lakehouse
pip install -r requirements.txt
python -m src.main full-pipeline
```

---

## Performance notes

A full pipeline run over 5 years of data for 4 commodities (~20,000 rows) completes in approximately 1–3 seconds on a modern laptop. The dominant cost is the initial PostgreSQL export; DuckDB transformation stages run in well under 1 second due to in-process columnar execution.

The interactive `query` command registers all layers as DuckDB views (`raw`, `curated`, `monthly_summary`, `price_metrics`, `commodity_comparison`) and provides a SQL REPL for ad-hoc exploration.
