"""Logging utilities for the application.

This module provides backward compatibility with the old logging utility
while redirecting to the new centralized logging infrastructure.

For new code, prefer importing directly from infrastructure.logging:
    from infrastructure.logging import get_logger
"""

import logging

from ....infrastructure.logging import get_logger as _get_centralized_logger


def get_logger(name: str, level: int | None = None) -> logging.Logger | logging.LoggerAdapter[logging.Logger]:
    """Get a configured logger with backward compatibility.

    This function provides backward compatibility with the old logging
    utility while using the new centralized logging infrastructure.

    Args:
        name: The name of the logger, typically __name__
        level: The logging level (will override configuration for this logger)

    Returns:
        A configured logger instance

    Note:
        For new code, prefer importing directly from infrastructure.logging:
            from infrastructure.logging import get_logger

        The level parameter is deprecated - use environment variables instead:
            LOG_LEVEL=DEBUG
    """
    logger = _get_centralized_logger(name)

    if level is not None:
        if isinstance(logger, logging.LoggerAdapter):
            logger.logger.setLevel(level)
        else:
            logger.setLevel(level)

    return logger
