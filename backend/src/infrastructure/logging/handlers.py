"""Custom logging handlers for different output destinations."""

import logging
import logging.handlers
import sys
from pathlib import Path

from .formatters import get_formatter


class ColoredConsoleHandler(logging.StreamHandler):
    """Enhanced console handler with color support."""

    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
    }
    RESET = "\033[0m"

    def __init__(self, stream=None):
        super().__init__(stream or sys.stdout)
        self.use_colors = self._should_use_colors()

    def _should_use_colors(self) -> bool:
        return hasattr(self.stream, "isatty") and self.stream.isatty() and sys.platform != "win32"

    def format(self, record: logging.LogRecord) -> str:
        formatted = super().format(record)
        if self.use_colors and record.levelname in self.COLORS:
            color = self.COLORS[record.levelname]
            formatted = formatted.replace(f"[{record.levelname}]", f"[{color}{record.levelname}{self.RESET}]")
        return formatted


class RotatingFileHandler(logging.handlers.RotatingFileHandler):
    """Enhanced rotating file handler with automatic directory creation."""

    def __init__(self, filename: str, max_bytes: int = 10485760, backup_count: int = 5, encoding: str = "utf-8"):
        log_path = Path(filename)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        super().__init__(filename=filename, maxBytes=max_bytes, backupCount=backup_count, encoding=encoding)


def create_console_handler(
    format_type: str = "detailed", level: int = logging.INFO, use_colors: bool = True
) -> logging.Handler:
    """Create a configured console handler."""
    handler: logging.Handler
    if use_colors:
        handler = ColoredConsoleHandler()
    else:
        handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(get_formatter(format_type))
    return handler


def create_file_handler(
    filepath: str,
    format_type: str = "structured",
    level: int = logging.DEBUG,
    max_bytes: int = 10485760,
    backup_count: int = 5,
) -> logging.Handler:
    """Create a configured rotating file handler."""
    handler = RotatingFileHandler(filename=filepath, max_bytes=max_bytes, backup_count=backup_count)
    handler.setLevel(level)
    handler.setFormatter(get_formatter(format_type))
    return handler


def create_null_handler() -> logging.Handler:
    """Create a null handler that discards all log records."""
    return logging.NullHandler()
