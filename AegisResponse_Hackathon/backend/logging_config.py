"""
Structured JSON logging configuration for Aegis Hospitality OS.
Provides consistent, machine-parseable log output across all modules.
"""

import logging
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from contextvars import ContextVar

# Context variable for request correlation IDs
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


class JSONFormatter(logging.Formatter):
    """Format log records as structured JSON for machine parsing."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
            "correlation_id": correlation_id_var.get(""),
        }

        # Include exception info if present
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }

        # Include any extra fields
        if hasattr(record, "extra_data"):
            log_entry["data"] = record.extra_data

        return json.dumps(log_entry, default=str)


def generate_correlation_id() -> str:
    """Generate a unique correlation ID for request tracing."""
    return str(uuid.uuid4())[:8]


def setup_logging(log_level: str = "INFO", log_file: str = "logs/ahos.log") -> None:
    """Configure application-wide structured JSON logging."""

    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Create JSON formatter
    json_formatter = JSONFormatter()

    # Console handler — structured JSON to stdout
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(json_formatter)

    # File handler — structured JSON to rotating file
    file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    file_handler.setFormatter(json_formatter)

    # Configure root logger
    root_logger = logging.getLogger("ahos")
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    root_logger.info(
        "Structured logging initialized",
        extra={"extra_data": {"log_level": log_level, "log_file": log_file}},
    )


def get_logger(name: str) -> logging.Logger:
    """Get a child logger under the 'ahos' namespace."""
    return logging.getLogger(f"ahos.{name}")
