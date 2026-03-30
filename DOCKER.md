# Docker Setup

## Prerequisites

- Docker Desktop installed and running

## Quick Start

```bash
# Clone the repository
git clone https://github.com/arashrazban/arash-portfolio.git
cd arash-portfolio

# Build and start all services
docker compose up --build

# The startup sequence takes ~5-10 minutes:
#   1. PostgreSQL starts and passes health check (~10s)
#   2. Ingestor fetches oil price history from Yahoo Finance (~3-7 min)
#   3. Lakehouse processes Bronze → Silver → Gold Parquet files (~20s)
#   4. API starts serving on http://localhost:8000

# Access the API
# Swagger UI:   http://localhost:8000/docs
# Health check: http://localhost:8000/api/v1/health
# API info:     http://localhost:8000/api/v1/info
```

## Services

| Service   | Description                          | Host Port |
|-----------|--------------------------------------|-----------|
| postgres  | PostgreSQL 16 data warehouse         | 5433      |
| ingestor  | Yahoo Finance → PostgreSQL (batch)   | —         |
| lakehouse | PostgreSQL → Parquet medallion (batch)| —        |
| api       | FastAPI REST API                     | 8000      |

> **Port 5433**: The compose stack maps PostgreSQL to host port 5433 to avoid
> conflicting with any existing `oil_warehouse_db` container running on 5432.

## Architecture

```
┌──────────────┐     ┌───────────────────┐     ┌─────────────┐
│   Ingestor   │────▶│    PostgreSQL      │◀────│     API     │
│  (run-once)  │     │  oil_warehouse_db  │     │   :8000     │
└──────────────┘     │      :5432         │     └──────┬──────┘
                     └───────────────────┘            │
                                                      │ reads
┌──────────────┐     ┌───────────────────┐            │
│  Lakehouse   │────▶│  Parquet Volume   │────────────┘
│  (run-once)  │     │  (lakehouse-data) │
└──────────────┘     └───────────────────┘
```

Data flow:
1. **Ingestor** pulls OHLCV data from Yahoo Finance and writes to `warehouse.fact_oil_prices`
2. **Lakehouse** reads from PostgreSQL, writes Bronze/Silver/Gold Parquet files to a shared Docker volume
3. **API** queries PostgreSQL directly for operational endpoints and reads Parquet via DuckDB for analytical endpoints

## Useful Commands

```bash
# Start in detached mode (background)
docker compose up -d --build

# Follow logs for a specific service
docker compose logs -f api
docker compose logs -f ingestor
docker compose logs -f lakehouse

# Stop all services (volumes preserved)
docker compose down

# Full reset — stop everything and delete all data
docker compose down -v

# Rebuild and restart a single service
docker compose build api
docker compose up -d api

# Run ingestor in incremental mode (fetch only new data)
docker compose run --rm ingestor incremental

# Run only the lakehouse export step
docker compose run --rm lakehouse python -m src.main export

# Open an interactive psql session against the warehouse
docker compose exec postgres psql -U arash -d oil_warehouse

# Check service status
docker compose ps
```

## Environment Variables

All services use sensible defaults for local development. In the compose stack
the following overrides are applied automatically:

| Variable | Service | Value in Docker |
|----------|---------|-----------------|
| `DB_HOST` | ingestor, lakehouse | `postgres` (service name) |
| `DB_PORT` | ingestor, lakehouse | `5432` |
| `DB_NAME` | ingestor, lakehouse | `oil_warehouse` |
| `DATA_DIR` | lakehouse | `/app/data` |
| `OIL_API_PG_HOST` | api | `postgres` |
| `OIL_API_PG_DATABASE` | api | `oil_warehouse` |
| `OIL_API_LAKEHOUSE_BASE_PATH` | api | `/opt/lakehouse` |

To override any value, create a `.env` file in the project root or pass
`-e KEY=VALUE` to `docker compose run`.

## Troubleshooting

**Ingestor fails to connect to PostgreSQL**
```bash
docker compose logs ingestor
# Usually means postgres wasn't ready — the healthcheck guards this,
# but if it still fails, increase start_period in docker-compose.yml.
```

**Lakehouse exits before ingestor completes**
The lakehouse depends on `ingestor: condition: service_completed_successfully`.
If the ingestor crashes (non-zero exit), the lakehouse will not start. Check:
```bash
docker compose logs ingestor
```

**API returns empty data from analytics endpoints**
The gold-layer Parquet files may not exist yet. Verify:
```bash
docker compose run --rm api ls /opt/lakehouse/data/serving/
```
If empty, re-run the lakehouse: `docker compose run --rm lakehouse`.

**Port 8000 already in use**
```bash
# Change the host port mapping in docker-compose.yml
ports:
  - "8001:8000"  # use 8001 on the host instead
```
