# Monitoring — Prometheus + Grafana

This directory contains the configuration for the Oil Pipeline observability stack.

---

## What's included

| Component | Image | Purpose |
|-----------|-------|---------|
| **Prometheus** | `prom/prometheus:v3.2.1` | Scrapes `/metrics` from the FastAPI service every 15 s; stores 7 days of TSDB data |
| **Grafana** | `grafana/grafana:11.5.2` | Visualises the Prometheus data; auto-provisions the datasource and dashboard on first start |

Both services join the existing `oil-network` bridge network so they can reach the `api` container by hostname.

---

## Access

| UI | URL | Credentials |
|----|-----|-------------|
| Prometheus | http://localhost:9090 | — (no auth) |
| Grafana | http://localhost:3000 | `admin` / `oilpipeline2026` |

The **Oil Pipeline — API Monitoring** dashboard loads automatically on first start; no manual import needed.

---

## Starting the stack

```bash
# Start everything (Prometheus + Grafana come up after the api service starts)
docker compose up -d

# Confirm Prometheus is scraping successfully
# Open http://localhost:9090/targets — "oil-pipeline-api" should show State: UP

# Open Grafana
# http://localhost:3000 → Dashboards → "Oil Pipeline — API Monitoring"
```

---

## Metrics exposed by the API

The FastAPI service exposes a Prometheus scrape endpoint at `GET /metrics`.

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `http_requests_total` | Counter | `method`, `endpoint`, `status_code` | Total HTTP requests handled |
| `http_request_duration_seconds` | Histogram | `method`, `endpoint` | Request latency; buckets from 5 ms to 10 s |
| `http_requests_in_progress` | Gauge | `method` | Requests currently being processed |
| `db_query_duration_seconds` | Histogram | `database`, `operation` | Database call latency; buckets from 1 ms to 2.5 s |
| `app_info` | Gauge | `version` | Always 1; label carries the application version |

In addition, `prometheus_client` automatically exposes standard process metrics:
`process_cpu_seconds_total`, `process_resident_memory_bytes`, `process_open_fds`, etc.

---

## Dashboard panels

| Row | Panel | Type | What it shows |
|-----|-------|------|---------------|
| Overview | Request Rate | Timeseries | req/s by method × endpoint × status |
| Overview | Error Rate % | Stat | 5xx rate as a percentage of total traffic |
| Overview | P95 Response Time | Stat | 95th-percentile end-to-end request latency |
| Overview | Requests In Progress | Gauge | Current in-flight request count |
| Request Details | Duration Heatmap | Heatmap | Distribution of request latency over time |
| Request Details | Requests by Endpoint | Timeseries | Per-endpoint req/s breakdown |
| DB Performance | DB Query Duration (P95) | Timeseries | 95th-percentile query time per database |
| DB Performance | DB Query Rate | Timeseries | Query throughput by database and operation |
| System | Process Memory | Timeseries | Resident set size of the API process |
| System | Process CPU | Timeseries | CPU utilisation rate of the API process |

---

## Directory layout

```
monitoring/
├── prometheus/
│   └── prometheus.yml              # Scrape config — targets api:8000
└── grafana/
    ├── provisioning/
    │   ├── datasources/
    │   │   └── prometheus.yml      # Auto-provisions the Prometheus datasource
    │   └── dashboards/
    │       └── dashboard.yml       # Tells Grafana where to find dashboard JSON files
    └── dashboards/
        └── oil-pipeline.json       # The pre-built API monitoring dashboard
```
