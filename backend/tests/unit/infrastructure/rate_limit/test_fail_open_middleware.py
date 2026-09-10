"""Tests for the fail_open behavior in rate limiter middleware."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request

from src.infrastructure.rate_limit.exceptions import RateLimitException
from src.infrastructure.rate_limit.middleware import _check_rate_limit


@pytest.fixture
def mock_request():
    """Create a mock Request object."""
    mock = MagicMock(spec=Request)
    mock.url = MagicMock()
    mock.url.path = "/api/v1/test"
    mock.client = MagicMock()
    mock.client.host = "127.0.0.1"
    mock.state = MagicMock()
    mock.app = MagicMock()
    mock.app.state = MagicMock()
    mock.app.state.initialization_complete = AsyncMock()
    mock.app.state.initialization_complete.wait = AsyncMock()
    return mock


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return AsyncMock()


@pytest.mark.asyncio
async def test_middleware_fail_open_behavior(mock_request, mock_db, mock_rate_limit_settings_fail_open):
    """Test middleware with fail_open=True when a backend error occurs."""

    with (
        patch("src.infrastructure.rate_limit.middleware.increment_and_check") as mock_inc,
        patch("src.infrastructure.rate_limit.middleware.DEFAULT_LIMIT", 100),
        patch("src.infrastructure.rate_limit.middleware.settings", mock_rate_limit_settings_fail_open),
    ):
        mock_inc.side_effect = Exception("Backend error")

        await _check_rate_limit(mock_request, mock_db)

        mock_inc.assert_called_once()
        assert mock_inc.call_args[1]["fail_open"] is True


@pytest.mark.asyncio
async def test_middleware_fail_closed_behavior(mock_request, mock_db, mock_rate_limit_settings_fail_closed):
    """Test middleware with fail_open=False when a backend error occurs."""

    with (
        patch("src.infrastructure.rate_limit.middleware.increment_and_check") as mock_inc,
        patch("src.infrastructure.rate_limit.middleware.DEFAULT_LIMIT", 100),
        patch("src.infrastructure.rate_limit.middleware.settings", mock_rate_limit_settings_fail_closed),
    ):
        mock_inc.side_effect = Exception("Backend error")

        with pytest.raises(RateLimitException):
            await _check_rate_limit(mock_request, mock_db)

        mock_inc.assert_called_once()
        assert mock_inc.call_args[1]["fail_open"] is False


@pytest.mark.asyncio
async def test_middleware_respects_rate_limit_exception(mock_request, mock_db, mock_rate_limit_settings_fail_open):
    """Test that middleware re-raises RateLimitException even with fail_open=True."""

    with (
        patch("src.infrastructure.rate_limit.middleware.increment_and_check") as mock_inc,
        patch("src.infrastructure.rate_limit.middleware.DEFAULT_LIMIT", 100),
        patch("src.infrastructure.rate_limit.middleware.settings", mock_rate_limit_settings_fail_open),
    ):
        mock_inc.side_effect = RateLimitException("Rate limit exceeded")

        with pytest.raises(RateLimitException):
            await _check_rate_limit(mock_request, mock_db)


@pytest.mark.asyncio
async def test_middleware_sets_correct_headers(mock_request, mock_db, mock_rate_limit_settings_fail_open):
    """Test that middleware sets correct rate limit headers on success."""

    with (
        patch("src.infrastructure.rate_limit.middleware.increment_and_check") as mock_inc,
        patch("src.infrastructure.rate_limit.middleware.DEFAULT_LIMIT", 100),
        patch("src.infrastructure.rate_limit.middleware.settings", mock_rate_limit_settings_fail_open),
    ):
        mock_inc.return_value = (3, False)

        await _check_rate_limit(mock_request, mock_db)

        assert hasattr(mock_request.state, "rate_limit_headers")
        headers = mock_request.state.rate_limit_headers
        assert headers["X-RateLimit-Limit"] == "100"
        assert headers["X-RateLimit-Remaining"] == "97"
        assert headers["X-RateLimit-Reset"] == "60"
