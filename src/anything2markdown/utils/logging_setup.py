"""Dual-format logging system (JSON + plain text) using structlog."""

from anything2markdown._internal.logging_setup import get_logger, setup_logging as _setup_logging

from ..config import settings


def setup_logging():
    """Configure dual-format logging for the anything2markdown module."""
    return _setup_logging(
        module_name="anything2md",
        log_dir=settings.log_dir,
        log_level=settings.log_level,
        log_format=settings.log_format,
        extra_silenced_loggers={"charset_normalizer": 30},  # WARNING
    )
