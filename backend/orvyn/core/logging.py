"""Structured JSON logging for observability and agent timeline auditing."""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict


class StructuredJsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects for log shippers and audit trails."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include custom extra fields if provided
        if hasattr(record, "task_id"):
            log_data["task_id"] = str(record.task_id)
        if hasattr(record, "event_type"):
            log_data["event_type"] = record.event_type
        if hasattr(record, "metadata"):
            log_data["metadata"] = record.metadata
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logger(name: str = "orvyn", level: int = logging.INFO) -> logging.Logger:
    """Configures and returns the central logger."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredJsonFormatter())
        logger.addHandler(handler)

    return logger


logger = setup_logger()
