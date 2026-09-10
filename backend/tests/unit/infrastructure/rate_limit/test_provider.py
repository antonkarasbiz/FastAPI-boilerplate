"""Tests for the rate limiter provider module."""

from unittest.mock import AsyncMock, patch

import pytest

from src.infrastructure.rate_limit.base import RateLimiterBackend
from src.infrastructure.rate_limit.exceptions import BackendNotFoundError
from src.infrastructure.rate_limit.provider import (
    RateLimiterProvider,
    get_count,
    increment_and_check,
    reset,
)


class MockBackend(RateLimiterBackend):
    """Mock implementation of RateLimiterBackend for testing."""

    def __init__(self):
        super().__init__()
        self.increment_and_check_mock = AsyncMock(return_value=(1, False))
        self.get_count_mock = AsyncMock(return_value=1)
        self.reset_mock = AsyncMock()
        self.ping_mock = AsyncMock(return_value=True)
        self.increment_mock = AsyncMock(return_value=1)
        self.delete_mock = AsyncMock(return_value=True)

    async def increment_and_check(self, key, limit, period):
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
def mock_backend():
    """Create a mock rate limiter backend."""
    return MockBackend()


@pytest.mark.asyncio
async def test_register_backend(provider, mock_backend):
    """Test registering a backend."""
    provider.register_backend("test", mock_backend)

    assert provider.get_backend("test") == mock_backend

    assert provider.default_backend_name == "test"


@pytest.mark.asyncio
async def test_register_multiple_backends(provider, mock_backend):
    """Test registering multiple backends."""
    provider.register_backend("test1", mock_backend)

    mock_backend2 = MockBackend()
    provider.register_backend("test2", mock_backend2, default=True)

    assert provider.get_backend("test1") == mock_backend
    assert provider.get_backend("test2") == mock_backend2

    assert provider.default_backend_name == "test2"
    assert provider.get_backend() == mock_backend2


@pytest.mark.asyncio
async def test_get_backend_not_found(provider):
    """Test getting a non-existent backend."""
    with pytest.raises(BackendNotFoundError):
        provider.get_backend("nonexistent")


@pytest.mark.asyncio
async def test_set_default_backend(provider, mock_backend):
    """Test setting the default backend."""
    provider.register_backend("test1", mock_backend)
    mock_backend2 = MockBackend()
    provider.register_backend("test2", mock_backend2)

    assert provider.default_backend_name == "test1"

    provider.set_default_backend("test2")
    assert provider.default_backend_name == "test2"
    assert provider.get_backend() == mock_backend2


@pytest.mark.asyncio
async def test_set_default_backend_not_found(provider, mock_backend):
    """Test setting a non-existent backend as default."""
    provider.register_backend("test", mock_backend)

    with pytest.raises(BackendNotFoundError):
        provider.set_default_backend("nonexistent")


@pytest.mark.asyncio
async def test_ping_all(provider, mock_backend):
    """Test pinging all backends."""
    provider.register_backend("test1", mock_backend)

    mock_backend2 = MockBackend()
    mock_backend2.ping_mock.return_value = False
    provider.register_backend("test2", mock_backend2)

    results = await provider.ping_all()

    assert results == {"test1": True, "test2": False}


@pytest.mark.asyncio
async def test_list_backends(provider, mock_backend):
    """Test listing all registered backends."""
    provider.register_backend("test1", mock_backend)
    mock_backend2 = MockBackend()
    provider.register_backend("test2", mock_backend2)

    backends = provider.list_backends()

    assert set(backends.keys()) == {"test1", "test2"}
    assert all(issubclass(cls, MockBackend) for cls in backends.values())


@pytest.mark.asyncio
async def test_increment_and_check_convenience(mock_backend):
    """Test the increment_and_check convenience function."""
    with patch(
        "src.infrastructure.rate_limit.provider.rate_limiter_provider.get_backend",
        return_value=mock_backend,
    ):
        result = await increment_and_check("test:key", 5, 60)

        mock_backend.increment_and_check_mock.assert_called_once_with("test:key", 5, 60)
        assert result == (1, False)


@pytest.mark.asyncio
async def test_get_count_convenience(mock_backend):
    """Test the get_count convenience function."""
    with patch(
        "src.infrastructure.rate_limit.provider.rate_limiter_provider.get_backend",
        return_value=mock_backend,
    ):
        result = await get_count("test:key")

        mock_backend.get_count_mock.assert_called_once_with("test:key")
        assert result == 1


@pytest.mark.asyncio
async def test_reset_convenience(mock_backend):
    """Test the reset convenience function."""
    with patch(
        "src.infrastructure.rate_limit.provider.rate_limiter_provider.get_backend",
        return_value=mock_backend,
    ):
        await reset("test:key")

        mock_backend.reset_mock.assert_called_once_with("test:key")
