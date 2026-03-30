"""
Structured JSON logging configuration.

Provides:
- JSONFormatter: emits log records as single-line JSON objects
- setup_logging(): configures the root logger once at startup
- get_logger(): returns a named child logger with optional bound context fields
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

SERVICE_NAME = "oil-price-ingestor"

_INTERNAL_KEYS = frozenset({
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process", "taskName", "message",
})


class JSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON strings."""

    def format(self, record: logging.LogRecord) -> str:
        """Serialise a LogRecord to a JSON string."""
        record.getMessage()  # populate record.message
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "service": SERVICE_NAME,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        # Merge any extra= fields passed by the caller
        for key, value in record.__dict__.items():
            if key not in _INTERNAL_KEYS and not key.startswith("_"):
                try:
                    json.dumps(value)  # guard: skip non-serialisable extras
                    payload[key] = value
                except (TypeError, ValueError):
                    payload[key] = str(value)
        return json.dumps(payload, default=str)


def setup_logging(level: str = "INFO") -> None:
    """Configure the root logger with a JSON handler on stdout.

    Call once at application startup.  Subsequent calls are idempotent
    because the root logger is only configured when it has no handlers yet.

    Args:
        level: Python logging level name (e.g. 'INFO', 'DEBUG').
    """
    root = logging.getLogger()
    if root.handlers:
        return  # already configured

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root.addHandler(handler)
    root.setLevel(getattr(logging, level, logging.INFO))


def get_logger(name: str, **context: Any) -> logging.LoggerAdapter:
    """Return a LoggerAdapter that injects *context* into every log record.

    Args:
        name:    Logger name (typically ``__name__`` of the calling module).
        **context: Key-value pairs merged into every record's ``extra`` dict.

    Returns:
        A LoggerAdapter wrapping the named logger.
    """
    logger = logging.getLogger(name)
    return logging.LoggerAdapter(logger, extra=context)
