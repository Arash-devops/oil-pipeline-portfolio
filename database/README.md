# Oil Price Data Warehouse

A production-quality PostgreSQL 16 data warehouse implementing a **star schema** for oil commodity price analytics. Built to demonstrate real-world data engineering patterns: dimensional modelling, staging/validation pipelines, SCD Type 2, stored procedures, and advanced analytical SQL.

---

## Architecture

### What is a Star Schema and Why?

A **star schema** places a central **fact table** (granular measurements) at the middle, surrounded by **dimension tables** (descriptive context). This structure optimises analytical queries because:

- **JOINs are simple**: fact → dimension, never dimension → dimension
- **Query patterns are predictable**: filter on dimensions, aggregate facts
- **Aggregation is fast**: the fact table is narrow; dimensions carry descriptions
- **Reporting tools understand it**: BI tools like Metabase/Tableau natively optimise star schemas

```
         DIM_DATE
             │
DIM_SOURCE ──┼── FACT_OIL_PRICES ──── DIM_COMMODITY
             │           │
             │    ANALYTICS_MONTHLY_SUMMARY
             │    ANALYTICS_PRICE_METRICS
             │
         STAGING (separate schema, no FKs)
```

See [`diagrams/star-schema.md`](diagrams/star-schema.md) for the full Mermaid ER diagram and ASCII data flow.

---

## Quick Start

### Prerequisites
- Docker Desktop (includes Docker Compose)
- `psql` client (optional, for connecting)

### Start the database

```bash
cd database/
docker compose up -d
```

Docker will automatically run all SQL files in `init/` **in numeric order** on first start. The database will be ready in ~30–60 seconds.

Check health:
```bash
docker compose ps
# oil_warehouse_db   Up (healthy)
```

### Connect

```bash
psql postgresql://arash:warehouse_dev_2026@localhost:5432/oil_warehouse
```

Or with individual flags:
```bash
psql -h localhost -p 5432 -U arash -d oil_warehouse
# Password: warehouse_dev_2026
```

### Reset (destroy all data and re-initialise)

**Linux / macOS:**
```bash
./scripts/reset-db.sh
```

**Windows (PowerShell):**
```powershell
.\scripts\reset-db.ps1
```

---

## Database Structure

### Schemas

| Schema      | Purpose                                                   |
|-------------|-----------------------------------------------------------|
| `staging`   | Raw data landing zone. No FK constraints. Validated in-place. |
| `warehouse` | Dimensional model (star schema). Source of truth.         |
| `analytics` | Pre-aggregated summaries and technical indicators.        |

### Tables

| Table                          | Rows (seeded) | Description |
|-------------------------------|---------------|-------------|
| `warehouse.dim_date`           | 5,844         | 2020-01-01 to 2035-12-31 |
| `warehouse.dim_commodity`      | 4             | WTI, Brent, Natural Gas, Heating Oil |
| `warehouse.dim_source`         | 2             | Yahoo Finance, Manual Entry |
| `warehouse.fact_oil_prices`    | 0 (load data) | Central fact table — daily OHLCV |
| `staging.stg_oil_prices`       | 0             | Landing zone |
| `analytics.monthly_summary`    | 0             | Populated by `sp_aggregate_monthly` |
| `analytics.price_metrics`      | 0             | Populated by `sp_calculate_metrics` |

### Views

| View                                | Description |
|-------------------------------------|-------------|
| `warehouse.v_latest_prices`         | Most recent price per active commodity |
| `warehouse.v_price_history`         | Full denormalised history with dimension labels |
| `warehouse.v_price_with_metrics`    | OHLCV joined with MA, RSI, trend signals |

---

## Stored Procedures

All procedures use `BEGIN / EXCEPTION / END` error handling and `RAISE NOTICE` logging.

### Pipeline Procedures (run in order)

```sql
-- 1. Validate raw staging rows
SELECT * FROM staging.sp_validate_staging_data();
-- Returns: total_records, valid_records, invalid_records

-- 2. Promote valid rows to warehouse + mark staging rows as processed
SELECT * FROM warehouse.sp_process_staging();
-- Returns: processed, skipped, errors

-- 3. Compute technical indicators for a commodity (defaults: last 365 days)
PERFORM analytics.sp_calculate_metrics(
    p_commodity_key := 1,       -- from dim_commodity
    p_start_date    := '2024-01-01',
    p_end_date      := CURRENT_DATE
);

-- 4. Aggregate monthly statistics (defaults: current month)
PERFORM analytics.sp_aggregate_monthly(p_year := 2024, p_month := 3);
```

### Utility Procedures

```sql
-- Single-row upsert (bypasses staging — useful for one-off corrections)
PERFORM warehouse.sp_upsert_oil_price(
    'CL=F', '2024-03-15',
    71.20, 73.80, 70.50, 72.45, 72.45, 425000, 'Yahoo Finance'
);

-- SCD Type 2 update — records history of dimension changes
PERFORM warehouse.sp_manage_scd2('CL=F', 'exchange', 'CME');
-- Creates a new version; old version gets valid_to stamped
```

---

## Sample Queries

`init/10-sample-queries.sql` contains 12 showcase queries. Key highlights:

| # | Technique | Description |
|---|-----------|-------------|
| 01 | `LAG` / `LEAD` | Daily price context with previous/next day |
| 02 | `ROW_NUMBER`, `RANK`, `NTILE` | Price rankings and quartile buckets |
| 03 | Multi-step CTE | 52-week high/low band position |
| 04 | `WITH RECURSIVE` | Compound return simulation ($10k portfolio) |
| 05 | PIVOT (conditional aggregation) | Monthly returns calendar grid |
| 06 | Gap detection | Missing trading days via set difference |
| 07 | `YoY` comparison | Year-over-year average price with LAG |
| 08 | Window frames | On-the-fly MA + Bollinger Bands |
| 09 | `PERCENTILE_CONT`, `WIDTH_BUCKET` | Price distribution & histogram |
| 10 | Correlated subquery | Intra-year price percentile rank |
| 11 | Full pipeline | DO block running all procedures end-to-end |
| 12 | `CORR()` aggregate | WTI–Brent Pearson correlation + spread analysis |

---

## Design Decisions

### Why surrogate integer keys for `dim_date`?
The `date_key` is `YYYYMMDD` as an `INTEGER` (e.g. `20240315`). This is:
- **Human-readable**: you can scan a column and immediately understand the date
- **Fast for range scans**: integer comparisons are faster than date comparisons at scale
- **ETL-friendly**: `TO_CHAR(date, 'YYYYMMDD')::INTEGER` works in any language without timezone concerns

### Why SCD Type 2 for `dim_commodity`?
Commodity attributes (name, exchange listing, unit of measure) change rarely but need **audit history**. SCD Type 2 preserves the full history of changes by creating new rows rather than overwriting. This means historical fact rows still point to the commodity _as it was then_, which is essential for accurate backtesting and regulatory audit trails.

### Why a staging pattern (ELT over ETL)?
Raw data lands in `staging.stg_oil_prices` **before** any transformation. Benefits:
- **Auditability**: every raw record is persisted, even if invalid
- **Re-processability**: if validation rules change, raw data can be re-validated without re-fetching
- **Decoupling**: the ingestion layer (Kafka/Airflow/script) only needs to write simple INSERTs; complexity lives in the database
- **Observability**: `is_valid`, `validation_errors`, and `processed_at` give a complete picture of data quality

### Why store `daily_change` and `daily_change_pct` in the fact table?
These are **derived facts** — technically calculable from `LAG()`. They are denormalised here intentionally because:
- They are queried on every dashboard request
- Recalculating them with a window function at query time scans the entire series
- Pre-storing them makes the `v_price_history` view and API endpoints O(1) per row

### Why separate `analytics` schema tables instead of materialised views?
Materialised views in PostgreSQL require manual `REFRESH MATERIALIZED VIEW` and cannot be incrementally updated. The explicit `analytics` tables with `INSERT ... ON CONFLICT DO UPDATE` in stored procedures allow:
- Partial refreshes (e.g. only refresh last 30 days of metrics)
- Audit timestamps (`updated_at`)
- Granular control over refresh scheduling (e.g. nightly via Airflow)

---

## Connection Details

| Parameter | Value |
|-----------|-------|
| Host | `localhost` |
| Port | `5432` |
| Database | `oil_warehouse` |
| User | `arash` |
| Password | `warehouse_dev_2026` |

> These credentials are for local development only. Never commit production credentials.
