"""Tests for the fail_open override functionality in the rate limiter provider."""

from unittest.mock import AsyncMock, patch

import pytest

from src.infrastructure.rate_limit.base import RateLimiterBackend
from src.infrastructure.rate_limit.provider import (
    RateLimiterProvider,
    increment_and_check,
)


class MockBackend(RateLimiterBackend):
    """Mock implementation of RateLimiterBackend with fail_open support."""

    def __init__(self, fail_open: bool = True):
        """Initialize the mock backend with configurable fail_open behavior."""
        super().__init__(fail_open=fail_open)
        self.increment_and_check_mock = AsyncMock(return_value=(1, False))
        self.get_count_mock = AsyncMock(return_value=1)
        self.reset_mock = AsyncMock()
        self.ping_mock = AsyncMock(return_value=True)
        self.increment_mock = AsyncMock(return_value=1)
        self.delete_mock = AsyncMock(return_value=True)

    async def increment_and_check(self, key, limit, period):
        """Mock implementation with side effect based on fail_open value."""
        if hasattr(self.increment_and_check_mock, "side_effect") and self.increment_and_check_mock.side_effect:
            if isinstance(self.increment_and_check_mock.side_effect, Exception):
                return 0, not self.fail_open
            if callable(self.increment_and_check_mock.side_effect):
                return self.increment_and_check_mock.side_effect(key, limit, period)
            raise self.increment_and_check_mock.side_effect
        return await self.increment_and_check_mock(key, limit, period)

    async def get_count(self, key):
        return await self.get_count_mock(key)

    async def reset(self, key):
        return await self.reset_mock(key)

    async def ping(self):
        return await self.ping_mock()

    async def increment(self, key, amount=1, expiry=300):
        return await self.increment_mock(key, amount, expiry)

    async def delete(self, key):
        return await self.delete_mock(key)


@pytest.fixture
def provider():
    """Create a fresh RateLimiterProvider for testing."""
    return RateLimiterProvider()


@pytest.fixture
def mock_backend_fail_open():
    """Create a mock rate limiter backend with fail_open=True."""
    return MockBackend(fail_open=True)


@pytest.fixture
def mock_backend_fail_closed():
    """Create a mock rate limiter backend with fail_open=False."""
    return MockBackend(fail_open=False)


@pytest.mark.asyncio
async def test_increment_and_check_with_fail_open_override(provider, mock_backend_fail_closed):
    """Test overriding fail_closed with fail_open in increment_and_check."""
    provider.register_backend("test", mock_backend_fail_closed, default=True)

    mock_backend_fail_closed.increment_and_check_mock.side_effect = Exception("Test error")

    with patch("src.infrastructure.rate_limit.provider.rate_limiter_provider", provider):
        count, is_limited = await increment_and_check(key="test:key", limit=5, period=60, backend_name="test")
        assert is_limited is True

        count, is_limited = await increment_and_check(key="test:key", limit=5, period=60, backend_name="test", fail_open=True)
        assert is_limited is False

        assert mock_backend_fail_closed.fail_open is False


@pytest.mark.asyncio
async def test_increment_and_check_with_fail_closed_override(provider, mock_backend_fail_open):
    """Test overriding fail-open with fail-closed in increment_and_check."""
    provider.register_backend("test", mock_backend_fail_open, default=True)

    mock_backend_fail_open.increment_and_check_mock.side_effect = Exception("Test error")

    with patch("src.infrastructure.rate_limit.provider.rate_limiter_provider", provider):
        count, is_limited = await increment_and_check(key="test:key", limit=5, period=60, backend_name="test")
        assert is_limited is False

        count, is_limited = await increment_and_check(key="test:key", limit=5, period=60, backend_name="test", fail_open=False)
        assert is_limited is True

        assert mock_backend_fail_open.fail_open is True


@pytest.mark.asyncio
async def test_provider_temp_override_behavior(provider, mock_backend_fail_open):
    """Test that temporary override only affects the current call."""
    provider.register_backend("test", mock_backend_fail_open, default=True)

    fail_open_during_call = None

    def side_effect(key, limit, period):
        nonlocal fail_open_during_call
        fail_open_during_call = mock_backend_fail_open.fail_open
        return 1, False

    mock_backend_fail_open.increment_and_check_mock.side_effect = side_effect

    with patch("src.infrastructure.rate_limit.provider.rate_limiter_provider", provider):
        await increment_and_check(key="test:key", limit=5, period=60, backend_name="test", fail_open=False)
        assert fail_open_during_call is False

        assert mock_backend_fail_open.fail_open is True


@pytest.mark.asyncio
async def test_provider_no_override_needed(provider, mock_backend_fail_open):
    """Test that no override happens if the value matches."""
    provider.register_backend("test", mock_backend_fail_open, default=True)

    original_fail_open = mock_backend_fail_open.fail_open
    assert original_fail_open is True

    with patch("src.infrastructure.rate_limit.provider.rate_limiter_provider", provider):
        await increment_and_check(key="test:key", limit=5, period=60, backend_name="test", fail_open=True)

        assert mock_backend_fail_open.fail_open is original_fail_open
