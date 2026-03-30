# Oil Price Data API

A FastAPI REST API serving oil price data from two complementary backends:
- **PostgreSQL** — operational queries on the live star-schema warehouse
- **DuckDB + Parquet** — analytical queries on the pre-aggregated gold layer

Interactive Swagger UI auto-generated at `http://localhost:8000/docs`.

---

## Architecture

```
Client
  |
  | HTTP
  v
FastAPI (services/api/)
  |
  +-- /api/v1/prices/*       ──►  PostgreSQL (psycopg v3 async pool)
  |                                 oil_warehouse_db:5432
  |                                 warehouse.fact_oil_prices
  |                                 warehouse.dim_commodity / dim_date
  |
  +-- /api/v1/analytics/*    ──►  DuckDB (in-memory, per-request)
  |                                 services/lakehouse/data/gold/
  |                                   monthly_summary/data.parquet
  |                                   price_metrics/data.parquet
  |                                   commodity_comparison/data.parquet
  |
  +-- /api/v1/health         ──►  Both backends (connectivity check)
  +-- /api/v1/info           ──►  Both backends (metadata + row counts)
```

### Why two backends?

| Backend | Strength | Used for |
|---------|----------|----------|
| PostgreSQL | Transactional, live data, row-level queries | Latest prices, historical OHLCV, commodity lookup |
| DuckDB/Parquet | Columnar analytics, pre-aggregated, fast range scans | Moving averages, Bollinger bands, monthly summaries, WTI/Brent spread |

---

## Prerequisites

1. Python 3.14 (other versions may work but are untested)
2. Docker container `oil_warehouse_db` running (Stage 2 — PostgreSQL)
3. Lakehouse gold layer populated (Stage 5 — `services/lakehouse/`)
4. The gold Parquet files must exist at:
   ```
   services/lakehouse/data/gold/monthly_summary/data.parquet
   services/lakehouse/data/gold/price_metrics/data.parquet
   services/lakehouse/data/gold/commodity_comparison/data.parquet
   ```

---

## Setup

```bash
cd services/api

# Create and activate a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt

# Start the server (reload mode for development)
python run.py
```

The API will be available at `http://localhost:8000`.
Swagger UI: `http://localhost:8000/docs`

### Environment variables

All settings use the prefix `OIL_API_`. Create a `.env` file to override defaults:

```env
OIL_API_PG_HOST=localhost
OIL_API_PG_PORT=5432
OIL_API_PG_DATABASE=oil_warehouse
OIL_API_PG_USER=arash
OIL_API_PG_PASSWORD=warehouse_dev_2026
OIL_API_DEBUG=true
```

---

## Endpoint Summary

| Method | Path | Backend | Description |
|--------|------|---------|-------------|
| GET | `/api/v1/prices/latest` | PostgreSQL | Most recent price per commodity |
| GET | `/api/v1/prices/history` | PostgreSQL | Historical OHLCV with date/symbol filters |
| GET | `/api/v1/prices/commodities` | PostgreSQL | All active commodity records |
| GET | `/api/v1/analytics/monthly-summary` | DuckDB | Monthly avg/min/max/volume/return |
| GET | `/api/v1/analytics/price-metrics` | DuckDB | MA7/30/90, volatility, Bollinger bands |
| GET | `/api/v1/analytics/commodity-comparison` | DuckDB | WTI vs Brent spread and ratio |
| GET | `/api/v1/health` | Both | Liveness check with per-component status |
| GET | `/api/v1/info` | Both | API metadata and row counts |

All list endpoints return:
```json
{
  "status": "success",
  "data": [...],
  "meta": {
    "count": 4,
    "source": "postgresql",
    "query_time_ms": 3.12
  }
}
```

---

## Example curl Commands

```bash
# Latest prices for all commodities
curl "http://localhost:8000/api/v1/prices/latest"

# Latest 10 records for WTI crude
curl "http://localhost:8000/api/v1/prices/latest?commodity=CL%3DF&limit=10"

# Historical data for Brent crude, Jan 2024
curl "http://localhost:8000/api/v1/prices/history?commodity=BZ%3DF&start_date=2024-01-01&end_date=2024-01-31"

# Historical data for all commodities, last 30 days
curl "http://localhost:8000/api/v1/prices/history?limit=200"

# All active commodities
curl "http://localhost:8000/api/v1/prices/commodities"

# Monthly summary for WTI, year 2024
curl "http://localhost:8000/api/v1/analytics/monthly-summary?commodity=CL%3DF&year=2024"

# Price metrics for Brent, last 30 rows
curl "http://localhost:8000/api/v1/analytics/price-metrics?commodity=BZ%3DF&limit=30"

# WTI/Brent spread for Q1 2024
curl "http://localhost:8000/api/v1/analytics/commodity-comparison?start_date=2024-01-01&end_date=2024-03-31"

# Health check
curl "http://localhost:8000/api/v1/health"

# API info + row counts
curl "http://localhost:8000/api/v1/info"
```

> **Note on URL encoding:** The `=` in commodity symbols like `CL=F` should be encoded as `%3D` in URLs, though most HTTP clients handle this automatically.

---

## CORS

CORS is configured to allow all origins (`*`) by default, making it suitable for
portfolio demonstrations where a frontend on a different port or domain needs access.
To restrict CORS in production, set `OIL_API_CORS_ORIGINS=["https://yourdomain.com"]`.
