"""Structured application logging."""

import logging
import sys
from typing import Any, cast

import structlog


def configure_logging(log_level: str, *, json_logs: bool) -> None:
    """Configure standard-library and structlog output."""

    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
    ]
    renderer: Any = (
        structlog.processors.JSONRenderer()
        if json_logs
        else structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty())
    )

    logging.basicConfig(
        format="%(message)s",
        level=log_level,
        stream=sys.stdout,
        force=True,
    )
    structlog.configure(
        processors=[*shared_processors, structlog.processors.format_exc_info, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(log_level)),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a named structured logger."""

    return cast(structlog.stdlib.BoundLogger, structlog.get_logger(name))
