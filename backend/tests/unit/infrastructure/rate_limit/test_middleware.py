"""Tests for the rate limiter middleware module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request, Response

from src.infrastructure.rate_limit.exceptions import RateLimitException
from src.infrastructure.rate_limit.middleware import (
    RateLimiterMiddleware,
    _check_rate_limit,
)
from src.modules.tier.schemas import TierSelect


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
def mock_response():
    """Create a mock Response object."""
    mock = MagicMock(spec=Response)
    mock.headers = {}
    return mock


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return AsyncMock()


@pytest.fixture
def mock_user():
    """Create a mock user dict."""
    return {
        "id": 123,
        "username": "testuser",
        "email": "test@example.com",
        "tier_id": 1,
    }


@pytest.fixture
def mock_app():
    """Create a mock FastAPI app."""
    return MagicMock()


@pytest.mark.asyncio
async def test_check_rate_limit_disabled(mock_request, mock_db):
    """Test check_rate_limit when rate limiting is disabled."""
    with patch("src.infrastructure.rate_limit.middleware.settings") as mock_settings:
        mock_settings.RATE_LIMITER_ENABLED = False

        await _check_rate_limit(mock_request, mock_db, None)


@pytest.mark.asyncio
async def test_check_rate_limit_no_user(mock_request, mock_db):
    """Test check_rate_limit with no authenticated user."""
    with (
        patch("src.infrastructure.rate_limit.middleware.settings") as mock_settings,
        patch("src.infrastructure.rate_limit.middleware.DEFAULT_LIMIT", 100),
        patch("src.infrastructure.rate_limit.middleware.increment_and_check") as mock_increment,
    ):
        mock_settings.RATE_LIMITER_ENABLED = True
        mock_settings.DEFAULT_RATE_LIMIT_LIMIT = 100
        mock_settings.DEFAULT_RATE_LIMIT_PERIOD = 60

        mock_increment.return_value = (1, False)

        await _check_rate_limit(mock_request, mock_db, None)

        mock_increment.assert_called_once()
        key_arg = mock_increment.call_args.kwargs["key"]
        assert "127.0.0.1" in key_arg
        assert mock_increment.call_args.kwargs["limit"] == 100
        assert mock_increment.call_args.kwargs["period"] == 60


@pytest.mark.asyncio
async def test_check_rate_limit_with_user(mock_request, mock_db, mock_user):
    """Test check_rate_limit with an authenticated user."""
    with (
        patch("src.infrastructure.rate_limit.middleware.settings") as mock_settings,
        patch("src.infrastructure.rate_limit.middleware.DEFAULT_LIMIT", 100),
        patch("src.infrastructure.rate_limit.middleware.increment_and_check") as mock_increment,
        patch("src.infrastructure.rate_limit.middleware.crud_tiers.get") as mock_get_tier,
        patch("src.infrastructure.rate_limit.middleware.crud_rate_limits.get") as mock_get_rate_limit,
    ):
        mock_settings.RATE_LIMITER_ENABLED = True
        mock_settings.DEFAULT_RATE_LIMIT_LIMIT = 100
        mock_settings.DEFAULT_RATE_LIMIT_PERIOD = 60

        mock_get_tier.return_value = {"id": 1, "name": "pro"}
        mock_get_rate_limit.return_value = {"limit": 10, "period": 30}

        mock_increment.return_value = (1, False)

        await _check_rate_limit(mock_request, mock_db, mock_user)

        mock_get_tier.assert_called_once_with(db=mock_db, id=1, schema_to_select=TierSelect)
        mock_get_rate_limit.assert_called_once()

        mock_increment.assert_called_once()
        key_arg = mock_increment.call_args.kwargs["key"]
        assert "123" in key_arg
        assert mock_increment.call_args.kwargs["limit"] == 10
        assert mock_increment.call_args.kwargs["period"] == 30


@pytest.mark.asyncio
async def test_check_rate_limit_no_specific_limits(mock_request, mock_db, mock_user):
    """Test check_rate_limit with user but no specific rate limits."""
    with (
        patch("src.infrastructure.rate_limit.middleware.settings") as mock_settings,
        patch("src.infrastructure.rate_limit.middleware.DEFAULT_LIMIT", 100),
        patch("src.infrastructure.rate_limit.middleware.increment_and_check") as mock_increment,
        patch("src.infrastructure.rate_limit.middleware.crud_tiers.get") as mock_get_tier,
        patch("src.infrastructure.rate_limit.middleware.crud_rate_limits.get") as mock_get_rate_limit,
        patch("src.infrastructure.rate_limit.middleware.logger") as mock_logger,
    ):
        mock_settings.RATE_LIMITER_ENABLED = True
        mock_settings.DEFAULT_RATE_LIMIT_LIMIT = 100
        mock_settings.DEFAULT_RATE_LIMIT_PERIOD = 60

        mock_get_tier.return_value = {"id": 1, "name": "pro"}
        mock_get_rate_limit.return_value = None

        mock_increment.return_value = (1, False)

        await _check_rate_limit(mock_request, mock_db, mock_user)

        assert mock_logger.warning.called
        mock_increment.assert_called_once()
        assert mock_increment.call_args.kwargs["limit"] == 100
        assert mock_increment.call_args.kwargs["period"] == 60


@pytest.mark.asyncio
async def test_check_rate_limit_exceeded(mock_request, mock_db):
    """Test check_rate_limit when rate limit is exceeded."""
    with (
        patch("src.infrastructure.rate_limit.middleware.settings") as mock_settings,
        patch("src.infrastructure.rate_limit.middleware.DEFAULT_LIMIT", 100),
        patch("src.infrastructure.rate_limit.middleware.increment_and_check") as mock_increment,
        patch("src.infrastructure.rate_limit.middleware.logger") as mock_logger,
    ):
        mock_settings.RATE_LIMITER_ENABLED = True
        mock_settings.DEFAULT_RATE_LIMIT_LIMIT = 100
        mock_settings.DEFAULT_RATE_LIMIT_PERIOD = 60

        mock_increment.return_value = (101, True)

        with pytest.raises(RateLimitException) as excinfo:
            await _check_rate_limit(mock_request, mock_db, None)

        assert "Rate limit exceeded" in str(excinfo.value)
        assert mock_logger.warning.called


@pytest.mark.asyncio
async def test_rate_limiter_middleware(mock_request, mock_response, mock_app):
    """Test the RateLimiterMiddleware."""
    middleware = RateLimiterMiddleware(app=mock_app)

    async def next_handler(request):
        return mock_response

    mock_request.state.rate_limit_headers = {
        "X-RateLimit-Limit": "10",
        "X-RateLimit-Remaining": "5",
        "X-RateLimit-Reset": "60",
    }

    response = await middleware.dispatch(mock_request, next_handler)

    assert response.headers["X-RateLimit-Limit"] == "10"
    assert response.headers["X-RateLimit-Remaining"] == "5"
    assert response.headers["X-RateLimit-Reset"] == "60"


@pytest.mark.asyncio
async def test_rate_limiter_middleware_no_headers(mock_request, mock_response, mock_app):
    """Test the RateLimiterMiddleware with no rate limit headers."""
    middleware = RateLimiterMiddleware(app=mock_app)

    async def next_handler(request):
        return mock_response

    if hasattr(mock_request.state, "rate_limit_headers"):
        delattr(mock_request.state, "rate_limit_headers")

    response = await middleware.dispatch(mock_request, next_handler)

    assert len(response.headers) == 0
