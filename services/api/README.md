# Oil Price API

FastAPI service that exposes the oil price data warehouse and analytics lakehouse via a REST API. Serves two distinct backends: PostgreSQL (operational queries) and DuckDB/Parquet (pre-aggregated analytics).

---

## What it does

- Provides 8 REST endpoints under `/api/v1/`
- Uses `async psycopg v3` with an `AsyncConnectionPool` for PostgreSQL queries
- Uses synchronous DuckDB connections (per-request, FastAPI thread pool) for Gold-layer Parquet queries
- Exports Prometheus metrics at `/metrics` via a `BaseHTTPMiddleware` wrapper
- Returns structured JSON responses with a standard `{ status, data, meta }` envelope
- Produces JSON structured logs via `structlog`

---

## Endpoint Reference

| Method | Path | Backend | Description | Key Parameters |
|--------|------|---------|-------------|----------------|
| GET | `/api/v1/prices/latest` | PostgreSQL | Latest price per commodity (or N most recent for one) | `commodity` (optional), `limit` (1–50) |
| GET | `/api/v1/prices/history` | PostgreSQL | Historical OHLCV with date range and pagination | `commodity`, `start_date`, `end_date`, `limit` (max 1000), `offset` |
| GET | `/api/v1/prices/commodities` | PostgreSQL | All active commodity records from `dim_commodity` | — |
| GET | `/api/v1/analytics/monthly-summary` | DuckDB | Monthly avg/min/max/stddev/volume per commodity | `commodity`, `year`, `limit` (max 500) |
| GET | `/api/v1/analytics/price-metrics` | DuckDB | Rolling 7/30/90-day MAs, 20-day volatility, Bollinger bands | `commodity`, `start_date`, `end_date`, `limit` |
| GET | `/api/v1/analytics/commodity-comparison` | DuckDB | WTI vs Brent daily spread and ratio | `start_date`, `end_date`, `limit` |
| GET | `/api/v1/health` | Both | Liveness + readiness for both backends | — |
| GET | `/api/v1/info` | Both | API metadata, endpoint list, row counts | — |
| GET | `/metrics` | — | Prometheus scrape endpoint | — |

Valid `commodity` values: `CL=F` (WTI Crude), `BZ=F` (Brent Crude), `NG=F` (Natural Gas), `HO=F` (Heating Oil)

Interactive documentation: http://localhost:8000/docs

---

## Configuration

All settings use `pydantic-settings` with the `OIL_API_` prefix.

| Variable | Default | Description |
|----------|---------|-------------|
| `OIL_API_PG_HOST` | `localhost` | PostgreSQL host |
| `OIL_API_PG_PORT` | `5432` | PostgreSQL port |
| `OIL_API_PG_DATABASE` | `oil_warehouse` | Database name |
| `OIL_API_PG_USER` | `arash` | Database user |
| `OIL_API_PG_PASSWORD` | `warehouse_dev_2026` | Database password |
| `OIL_API_LAKEHOUSE_BASE_PATH` | auto-resolved | Root of the lakehouse — serving Parquet at `{base}/data/serving/` |
| `OIL_API_PG_MIN_POOL_SIZE` | `2` | Minimum async pool connections |
| `OIL_API_PG_MAX_POOL_SIZE` | `10` | Maximum async pool connections |

---

## Middleware pipeline

```
Request → MetricsMiddleware → CORSMiddleware → Router → Handler
```

`MetricsMiddleware` (outermost) records `http_requests_total`, `http_request_duration_seconds`, and `http_requests_in_progress` for every request except `/metrics` itself.

`CORSMiddleware` allows all origins by default (`*`).

---

## How to run

### Docker (recommended)

```bash
docker compose up api
```

### Standalone

```bash
cd services/api
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Testing

48 tests across 5 modules. PostgreSQL is fully mocked; DuckDB uses a real in-memory instance.

```bash
cd services/api
pytest tests/ -v
```

| File | Coverage |
|------|---------|
| `test_health.py` | `/health` status codes and field presence |
| `test_prices.py` | `/prices/latest`, `/history`, `/commodities`, 422 validation |
| `test_analytics.py` | `/monthly-summary`, `/price-metrics`, `/commodity-comparison` |
| `test_models.py` | Pydantic model instantiation and field defaults |
| `test_config.py` | Settings defaults, env overrides, conninfo format |

---

## Dependencies

```
fastapi>=0.115.0          # Web framework + OpenAPI
uvicorn[standard]>=0.34.0 # ASGI server
psycopg[binary]>=3.2.0    # PostgreSQL adapter (v3, Python 3.14 compatible)
psycopg-pool>=3.2.0       # Async connection pool
pydantic>=2.10.0           # Data validation
pydantic-settings>=2.7.0   # Environment variable configuration
duckdb>=1.2.0              # In-process analytical SQL over Parquet
structlog>=24.4.0          # Structured JSON logging
python-dotenv>=1.0.0       # .env file support
httpx>=0.27.0              # HTTP client (used in tests)
pytest>=8.0.0              # Test runner
prometheus-client>=0.21.0  # Prometheus metrics
