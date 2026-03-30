# Oil Price Lakehouse — DuckDB + Parquet

A medallion-architecture lakehouse for oil price analytics, built on DuckDB and Apache Parquet. Reads from the PostgreSQL `oil_warehouse` and materialises three layers of analytical data locally.

## Architecture

```
PostgreSQL Warehouse
       |
       | psycopg v3
       v
+------+------+
|   BRONZE     |  raw/oil_prices/year={Y}/month={M}/data.parquet
|  (pg_exporter)|  snappy-compressed, full fidelity
+------+------+
       |
       | DuckDB SQL
       v
+------+------+
|   SILVER     |  curated/oil_prices/year={Y}/month={M}/data.parquet
|(transformer) |  nulls removed, negatives removed, daily_return_pct added
+------+------+
       |
       | DuckDB SQL
       v
+------+------+
|    GOLD      |  serving/monthly_summary/data.parquet
| (aggregator) |  serving/price_metrics/data.parquet
+------+------+  serving/commodity_comparison/data.parquet
       |
       | DuckDB in-memory views
       v
+------+------+
|  QUERY LAYER |  Arbitrary SQL + convenience methods
|(duckdb_engine)|
+--------------+
```

## Why Medallion Architecture?

| Layer | Purpose | Audience |
|-------|---------|----------|
| Bronze | Raw, immutable copy of source data | Debugging, reprocessing |
| Silver | Cleaned, enriched, validated | Data analysts, ML features |
| Gold | Pre-aggregated serving tables | Dashboards, APIs, reports |

Separating concerns this way means a bad transformation never corrupts the raw data, and aggregations stay cheap because silver is already clean.

## Quick Start

```bash
cd services/lakehouse
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env with your connection details

# Full pipeline (export -> transform -> aggregate)
python -m src.main full-pipeline

# Or step by step
python -m src.main export
python -m src.main transform
python -m src.main aggregate
```

## CLI Usage

```bash
# Export all data from PostgreSQL
python -m src.main export

# Incremental export for a date range
python -m src.main export --start-date 2024-01-01 --end-date 2024-12-31

# Transform bronze to silver
python -m src.main transform

# Aggregate silver to gold
python -m src.main aggregate

# Interactive SQL prompt
python -m src.main query
# sql> SELECT symbol, COUNT(*) FROM curated GROUP BY symbol

# Print layer statistics
python -m src.main stats

# Run everything in sequence
python -m src.main full-pipeline
python -m src.main full-pipeline --start-date 2024-01-01 --end-date 2024-12-31
```

## Query Examples

```sql
-- Latest price for each commodity
SELECT symbol, MAX(trade_date) AS date, close
FROM curated
GROUP BY symbol, close
ORDER BY symbol;

-- Monthly WTI average price
SELECT year, month, ROUND(AVG(close), 2) AS avg_close
FROM curated
WHERE symbol = 'CL=F'
GROUP BY year, month
ORDER BY year, month;

-- WTI/Brent spread over time
SELECT * FROM commodity_comparison
WHERE trade_date >= '2024-01-01'
ORDER BY trade_date;

-- Bollinger band squeeze (narrow bands = low volatility)
SELECT trade_date, symbol,
       bollinger_upper - bollinger_lower AS band_width
FROM price_metrics
ORDER BY band_width ASC
LIMIT 20;
```

## File Structure

```
data/
├── raw/
│   └── oil_prices/
│       ├── year=2020/month=1/data.parquet
│       ├── year=2020/month=2/data.parquet
│       └── ...
├── curated/
│   ├── oil_prices/
│   │   ├── year=2020/month=1/data.parquet
│   │   └── ...
│   └── _quality_report/
│       └── report.parquet
└── serving/
    ├── monthly_summary/data.parquet
    ├── price_metrics/data.parquet
    └── commodity_comparison/data.parquet
```

## Running Tests

```bash
pytest tests/ -v
```
