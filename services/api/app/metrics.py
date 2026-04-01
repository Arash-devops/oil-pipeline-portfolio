"""
Prometheus metrics for the Oil Price API.

Exposes:
  - http_requests_total          (Counter)   — by method, endpoint, status_code
  - http_request_duration_seconds (Histogram) — by method, endpoint
  - http_requests_in_progress    (Gauge)     — by method
  - db_query_duration_seconds    (Histogram) — by database, operation
  - app_info                     (Gauge)     — static label carrying the app version

Usage:
  - MetricsMiddleware: add to the FastAPI app to instrument every HTTP request.
  - track_db_query: async context manager for timing individual DB calls.
  - metrics_endpoint: Starlette Response handler for GET /metrics.
"""

from __future__ import annotations

import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import settings

# ---------------------------------------------------------------------------
# Metric definitions
# ---------------------------------------------------------------------------

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests currently being processed",
    ["method"],
)

db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["database", "operation"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
)

# Static gauge — value is always 1; labels carry metadata.
app_info = Gauge("app_info", "Application info", ["version"])
app_info.labels(version=settings.api_version).set(1)


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------


class MetricsMiddleware(BaseHTTPMiddleware):
    """Starlette middleware that records Prometheus HTTP metrics per request."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        path = request.url.path.rstrip("/") or "/"

        # Do not instrument the metrics scrape endpoint itself.
        if path == "/metrics":
            return await call_next(request)

        method = request.method
        http_requests_in_progress.labels(method=method).inc()
        start = time.perf_counter()
        status_code = "500"

        try:
            response = await call_next(request)
            status_code = str(response.status_code)
            return response
        finally:
            duration = time.perf_counter() - start
            http_requests_in_progress.labels(method=method).dec()
            http_requests_total.labels(
                method=method,
                endpoint=path,
                status_code=status_code,
            ).inc()
            http_request_duration_seconds.labels(
                method=method,
                endpoint=path,
            ).observe(duration)


# ---------------------------------------------------------------------------
# DB query timing helper
# ---------------------------------------------------------------------------


@asynccontextmanager
async def track_db_query(
    database: str,
    operation: str,
) -> AsyncGenerator[None, None]:
    """Async context manager that times a database operation.

    Usage::

        async with track_db_query("postgresql", "fetch_prices"):
            rows = await cursor.fetchall()

    Args:
        database: Label value — "postgresql" or "duckdb".
        operation: Short description of the query, e.g. "fetch_prices".
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        duration = time.perf_counter() - start
        db_query_duration_seconds.labels(
            database=database,
            operation=operation,
        ).observe(duration)


# ---------------------------------------------------------------------------
# /metrics endpoint handler
# ---------------------------------------------------------------------------


def metrics_endpoint(request: Request) -> Response:  # noqa: ARG001
    """Return the current Prometheus metrics in text exposition format.

    Registered as a plain Starlette route (not a FastAPI route) so that it
    does not appear in the OpenAPI schema.
    """
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
