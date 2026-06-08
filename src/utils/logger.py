"""
TRIDENT-AI Structured Logging.

Sets up structlog with JSON output, timestamps, log levels, and module context.
All TRIDENT modules must import `get_logger` from here — never use print() or
the stdlib logging module directly.

Usage:
    from src.utils.logger import get_logger
    log = get_logger(__name__)
    log.info("agent_started", agent="TelemetrySentinel", poll_cycle=42)
"""

from __future__ import annotations

import logging
import sys

import structlog

from src.utils.config import settings


def setup_logging() -> None:
    """
    Configure structlog and stdlib logging for the entire application.

    Output format is controlled by settings.LOG_FORMAT:
        - "json": machine-readable JSON lines (production)
        - "console": human-readable coloured output (development)
    """
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # ─── Shared processors ──────────────────────────────────────────
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.LOG_FORMAT.lower() == "json":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    # ─── Configure structlog ────────────────────────────────────────
    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # ─── Configure stdlib logging to use structlog formatter ────────
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # Silence noisy third-party loggers
    for noisy_logger in ("urllib3", "botocore", "httpx", "httpcore"):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger bound to the given module name.

    Args:
        name: Module name, typically __name__.

    Returns:
        A structlog BoundLogger instance with structured context.
    """
    return structlog.get_logger(name)


# ─── Auto-setup on import ───────────────────────────────────────────────
setup_logging()
