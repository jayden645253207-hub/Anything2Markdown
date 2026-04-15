"""Dual-format logging system (JSON + plain text) using structlog."""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import structlog


# Default noisy third-party loggers to silence
DEFAULT_SILENCED_LOGGERS = {
    "httpx": logging.WARNING,
    "httpcore": logging.WARNING,
    "openai": logging.WARNING,
}


def setup_logging(
    module_name: str,
    log_dir: Path,
    log_level: str,
    log_format: str,
    extra_silenced_loggers: dict[str, int] | None = None,
) -> structlog.stdlib.BoundLogger:
    """
    Configure dual-format logging: JSON + plain text.

    Args:
        module_name: Prefix for log filenames (e.g., "anything2md").
        log_dir: Base directory for logs.
        log_level: Logging level string (e.g., "INFO").
        log_format: One of "json", "text", "both".
        extra_silenced_loggers: Optional extra logger names to silence.

    Returns:
        Configured structlog BoundLogger.
    """
    # Ensure log directories exist
    json_log_dir = Path(log_dir) / "json"
    text_log_dir = Path(log_dir) / "text"
    json_log_dir.mkdir(parents=True, exist_ok=True)
    text_log_dir.mkdir(parents=True, exist_ok=True)

    # Timestamp for log files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Silence noisy third-party loggers
    silenced = {**DEFAULT_SILENCED_LOGGERS, **(extra_silenced_loggers or {})}
    for logger_name, level in silenced.items():
        logging.getLogger(logger_name).setLevel(level)

    # Configure structlog processors
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    structlog.configure(
        processors=shared_processors + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler (always plain text with colors)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processor=structlog.dev.ConsoleRenderer(colors=True),
            foreign_pre_chain=shared_processors,
        )
    )
    root_logger.addHandler(console_handler)

    # JSON file handler
    if log_format in ("json", "both"):
        json_file = json_log_dir / f"{module_name}_{timestamp}.json"
        json_handler = logging.FileHandler(json_file, encoding="utf-8")
        json_handler.setFormatter(
            structlog.stdlib.ProcessorFormatter(
                processor=structlog.processors.JSONRenderer(),
                foreign_pre_chain=shared_processors,
            )
        )
        root_logger.addHandler(json_handler)

    # Plain text file handler
    if log_format in ("text", "both"):
        text_file = text_log_dir / f"{module_name}_{timestamp}.log"
        text_handler = logging.FileHandler(text_file, encoding="utf-8")
        text_handler.setFormatter(
            structlog.stdlib.ProcessorFormatter(
                processor=structlog.dev.ConsoleRenderer(colors=False),
                foreign_pre_chain=shared_processors,
            )
        )
        root_logger.addHandler(text_handler)

    return structlog.get_logger()


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a bound logger for a module."""
    return structlog.get_logger(name)
