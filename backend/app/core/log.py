"""Shared logging setup for API and worker processes."""

import logging

from backend.app.core.config import get_settings

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logging(level: str | None = None) -> None:
    """Configure root logging without replacing handlers owned by the host process."""

    configured_level = level or get_settings().log_level
    logging.basicConfig(
        level=configured_level,
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
    )
    # basicConfig is a no-op when Uvicorn or Celery has installed handlers.
    # Setting the root level still makes the application setting effective.
    logging.getLogger().setLevel(configured_level)
