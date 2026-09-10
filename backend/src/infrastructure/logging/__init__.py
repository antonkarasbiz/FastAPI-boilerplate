"""Centralized logging infrastructure.

This module provides a unified logging system that integrates with the application's
settings and provides environment-aware configuration. It replaces scattered
logging.getLogger(__name__) calls with a centralized, configurable system.

Key Features:
- Environment-aware logging configuration
- Integration with application settings
- Structured logging support
- Consistent formatting across all modules
- Performance optimized for production

Usage:
    ```python
    from infrastructure.logging import get_logger

    logger = get_logger()  # Auto-detects module name
    logger.info("Application started")

    # Or with explicit name
    logger = get_logger("my.module")
    logger.debug("Debug information", extra={"user_id": 123})
    ```
"""

from .config import setup_logging_configuration
from .factory import configure_logging, get_logger

__all__ = [
    "get_logger",
    "configure_logging",
    "setup_logging_configuration",
]
