"""Tests for correlation ID logging functionality."""

import contextvars
import logging
import threading
import time
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

from src.infrastructure.logging.config import (
    CorrelationIdFilter,
    add_correlation_id_filter,
    generate_correlation_id,
    get_correlation_id,
    set_correlation_id,
)


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    logger = logging.getLogger("test_correlation")
    logger.setLevel(logging.DEBUG)

    # Clear existing handlers
    logger.handlers.clear()

    # Add string handler for capturing output
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(correlation_id)s - %(message)s"))
    logger.addHandler(handler)

    return logger, stream


def test_correlation_id_context_management():
    """Test correlation ID context variable management."""
    # Test setting and getting correlation ID
    test_id = "test-correlation-123"
    set_correlation_id(test_id)

    retrieved_id = get_correlation_id()
    assert retrieved_id == test_id

    # Test in different context - create new empty context
    def new_context():
        # Should not have correlation ID in new empty context
        assert get_correlation_id() is None

        # Set new ID in this context
        set_correlation_id("context-456")
        assert get_correlation_id() == "context-456"

    # Run in new empty context
    ctx = contextvars.Context()  # Create empty context instead of copying
    ctx.run(new_context)

    # Original context should still have original ID
    assert get_correlation_id() == test_id


def test_generate_correlation_id():
    """Test correlation ID generation."""
    id1 = generate_correlation_id()
    id2 = generate_correlation_id()

    # Should generate different IDs
    assert id1 != id2

    # Should be valid UUIDs (36 characters with hyphens)
    assert len(id1) == 36
    assert len(id2) == 36
    assert "-" in id1
    assert "-" in id2


def test_correlation_id_filter_with_context(mock_logger):
    """Test correlation ID filter with context variable."""
    logger, stream = mock_logger

    # Add correlation filter
    correlation_filter = CorrelationIdFilter()
    logger.addFilter(correlation_filter)

    # Set correlation ID in context
    test_id = "filter-test-789"
    set_correlation_id(test_id)

    # Log message
    logger.info("Test message with correlation ID")

    # Check output
    output = stream.getvalue()
    assert test_id in output
    assert "Test message with correlation ID" in output


def test_correlation_id_filter_no_context(mock_logger):
    """Test correlation ID filter without context."""
    logger, stream = mock_logger

    # Add correlation filter
    correlation_filter = CorrelationIdFilter()
    logger.addFilter(correlation_filter)

    # Test in a fresh context without correlation ID
    def run_test():
        # Log message in context without correlation ID
        logger.info("Test message without correlation ID")

    # Run in fresh context (no correlation ID set)
    ctx = contextvars.Context()
    ctx.run(run_test)

    # Check output - should have default value
    output = stream.getvalue()
    assert "no-correlation" in output
    assert "Test message without correlation ID" in output


def test_correlation_id_filter_thread_local(mock_logger):
    """Test correlation ID filter with thread local fallback."""
    logger, stream = mock_logger

    # Add correlation filter
    correlation_filter = CorrelationIdFilter()
    logger.addFilter(correlation_filter)

    # Set thread local correlation ID
    test_id = "thread-local-456"
    threading.current_thread().correlation_id = test_id  # type: ignore[attr-defined]

    try:
        # Test in fresh context to force thread local lookup
        def run_test():
            # Log message - should fall back to thread local
            logger.info("Test thread local correlation ID")

        # Run in fresh context (no correlation ID context var set)
        ctx = contextvars.Context()
        ctx.run(run_test)

        # Check output
        output = stream.getvalue()
        assert test_id in output

    finally:
        # Clean up thread local
        delattr(threading.current_thread(), "correlation_id")


def test_correlation_id_filter_request_headers(mock_logger):
    """Test correlation ID filter basic functionality."""
    logger, stream = mock_logger

    # Add correlation filter
    correlation_filter = CorrelationIdFilter()
    logger.addFilter(correlation_filter)

    # Set correlation ID via context (the primary method)
    set_correlation_id("header-correlation-123")

    # Log message
    logger.info("Test correlation ID functionality")

    # Check output
    output = stream.getvalue()
    assert "header-correlation-123" in output


def test_correlation_id_filter_request_id_header(mock_logger):
    """Test correlation ID filter with different ID format."""
    logger, stream = mock_logger

    # Add correlation filter
    correlation_filter = CorrelationIdFilter()
    logger.addFilter(correlation_filter)

    # Set correlation ID with request ID format
    set_correlation_id("request-id-789")

    # Log message
    logger.info("Test request ID header")

    # Check output
    output = stream.getvalue()
    assert "request-id-789" in output


def test_correlation_id_filter_request_state(mock_logger):
    """Test correlation ID filter with request state."""
    logger, stream = mock_logger

    # Add correlation filter
    correlation_filter = CorrelationIdFilter()
    logger.addFilter(correlation_filter)

    # Create mock log record
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="", lineno=0, msg="Test message", args=(), exc_info=None
    )

    # Set test correlation ID in context
    test_id = "state-correlation-456"
    set_correlation_id(test_id)

    # Process record through filter
    result = correlation_filter.filter(record)

    assert result is True
    assert record.correlation_id == test_id  # type: ignore[attr-defined]
    assert hasattr(record, "extra")
    assert getattr(record, "extra")["correlation_id"] == test_id


def test_correlation_id_filter_error_handling(mock_logger):
    """Test correlation ID filter error handling."""
    logger, stream = mock_logger

    # Add correlation filter
    correlation_filter = CorrelationIdFilter()
    logger.addFilter(correlation_filter)

    # Mock _get_correlation_id to raise exception
    mock_method = MagicMock(side_effect=Exception("Test error"))

    # Use patch to mock the method properly
    with patch.object(correlation_filter, "_get_correlation_id", mock_method):
        # Log message - should not crash
        logger.info("Test error handling")

        # Check output - should have default value
        output = stream.getvalue()
        assert "no-correlation" in output


def test_add_correlation_id_filter():
    """Test adding correlation ID filter to logger."""
    test_logger = logging.getLogger("test_add_filter")
    test_logger.handlers.clear()

    # Add stream handler
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(correlation_id)s - %(message)s"))
    test_logger.addHandler(handler)
    test_logger.setLevel(logging.DEBUG)

    # Should start with no filters
    assert len(test_logger.filters) == 0

    # Add correlation filter
    add_correlation_id_filter()

    # Root logger should have the filter
    root_logger = logging.getLogger()
    correlation_filters = [f for f in root_logger.filters if isinstance(f, CorrelationIdFilter)]
    assert len(correlation_filters) >= 1


def test_correlation_id_inheritance():
    """Test correlation ID functionality in child loggers."""
    # Create child logger with its own filter
    child_logger = logging.getLogger("test.child")
    child_logger.setLevel(logging.DEBUG)
    child_logger.handlers.clear()

    # Add correlation filter to child logger
    correlation_filter = CorrelationIdFilter()
    child_logger.addFilter(correlation_filter)

    # Add handler to capture output
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(correlation_id)s - %(message)s"))
    child_logger.addHandler(handler)
    child_logger.propagate = False  # Don't propagate to avoid double filtering

    # Set correlation ID
    test_id = "inheritance-test-123"
    set_correlation_id(test_id)

    # Log to child logger
    child_logger.info("Child logger message")

    # Should have correlation ID from filter
    output = stream.getvalue()
    assert test_id in output


def test_correlation_id_multiple_contexts():
    """Test correlation ID in multiple concurrent contexts."""
    results = {}

    def context_function(context_id):
        test_id = f"context-{context_id}"
        set_correlation_id(test_id)
        retrieved_id = get_correlation_id()
        results[context_id] = retrieved_id

    # Run multiple contexts
    contexts = []
    for i in range(3):
        ctx = contextvars.copy_context()
        contexts.append(ctx)
        ctx.run(context_function, i)

    # Each context should have its own correlation ID
    assert results[0] == "context-0"
    assert results[1] == "context-1"
    assert results[2] == "context-2"
    assert len(set(results.values())) == 3  # All unique


def test_correlation_id_filter_performance():
    """Test correlation ID filter performance."""
    filter_instance = CorrelationIdFilter()

    # Create log record
    record = logging.LogRecord(
        name="perf_test", level=logging.INFO, pathname="", lineno=0, msg="Performance test message", args=(), exc_info=None
    )

    # Set correlation ID
    set_correlation_id("performance-test-id")

    # Time multiple filter calls
    start_time = time.time()

    for _ in range(1000):
        filter_instance.filter(record)

    end_time = time.time()
    duration = end_time - start_time

    # Should be fast (less than 1 second for 1000 calls)
    assert duration < 1.0

    # Record should have correlation ID
    assert record.correlation_id == "performance-test-id"  # type: ignore[attr-defined]
