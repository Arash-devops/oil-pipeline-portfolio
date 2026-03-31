"""
FastAPI application factory for the Oil Price Data API.

Configures:
- Async lifespan (PostgreSQL pool init/close)
- CORS middleware
- Structlog JSON logging
- Router registration under /api/v1
- Root redirect to /docs
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.config import settings
from app.dependencies import close_pg_pool, init_pg_pool
from app.routers import analytics, health, prices

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Structlog configuration
# ---------------------------------------------------------------------------


def _configure_logging() -> None:
    """Configure structlog with JSON output for structured logging.

    Called once at startup. Sets up stdlib integration so that any
    library using the standard `logging` module also produces JSON.
    """
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )

    # Route stdlib logging through structlog so third-party libs emit JSON too.
    logging.basicConfig(
        format="%(message)s",
        level=logging.INFO,
    )
    for noisy in ("uvicorn.access", "uvicorn.error"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Manage application startup and shutdown.

    Startup:
      - Configure structured logging
      - Initialise the async PostgreSQL connection pool

    Shutdown:
      - Close the PostgreSQL connection pool

    Args:
        app: The FastAPI application instance.

    Yields:
        Control to the running application.
    """
    _configure_logging()
    await logger.ainfo(
        "Starting Oil Price API",
        version=settings.api_version,
        pg_host=settings.pg_host,
        pg_database=settings.pg_database,
        lakehouse=settings.lakehouse_base_path,
    )

    await init_pg_pool()

    yield  # Application is running

    await close_pg_pool()
    await logger.ainfo("Oil Price API shut down.")


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------


def create_app() -> FastAPI:
    """Construct and configure the FastAPI application.

    Returns:
        Configured FastAPI instance.
    """
    application = FastAPI(
        title=settings.api_title,
        description=settings.api_description,
        version=settings.api_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS — allow all origins by default (suitable for portfolio demo).
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    application.include_router(
        prices.router,
        prefix=f"{settings.api_prefix}/prices",
    )
    application.include_router(
        analytics.router,
        prefix=f"{settings.api_prefix}/analytics",
    )
    application.include_router(
        health.router,
        prefix=settings.api_prefix,
    )

    # Root → Swagger UI redirect
    @application.get("/", include_in_schema=False)
    async def root_redirect() -> RedirectResponse:
        """Redirect the bare root URL to the Swagger UI."""
        return RedirectResponse(url="/docs")

    return application


app: FastAPI = create_app()
