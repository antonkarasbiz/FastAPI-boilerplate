"""Tests for the Memcached rate limiter backend."""

from unittest.mock import AsyncMock, patch

import pytest

from src.infrastructure.rate_limit.backends.memcached import (
    MemcachedBackend,
    MemcachedSettings,
)
from src.infrastructure.rate_limit.exceptions import RateLimiterBackendException


@pytest.fixture
def mock_aiomcache():
    """Create a mock aiomcache client."""
    client_mock = AsyncMock()
    client_mock.get = AsyncMock()
    client_mock.set = AsyncMock()
    client_mock.delete = AsyncMock()
    return client_mock


@pytest.fixture
def memcached_backend(mock_aiomcache):
    """Create a MemcachedBackend with a mock client."""
    with patch("aiomcache.Client", return_value=mock_aiomcache):
        settings = MemcachedSettings(host="localhost", port=11211)
        backend = MemcachedBackend(settings=settings)
        backend.client = mock_aiomcache
        yield backend


@pytest.mark.asyncio
async def test_init_error():
    """Test that initialization errors are properly handled."""
    with patch("aiomcache.Client", side_effect=Exception("Connection error")):
        with pytest.raises(RateLimiterBackendException) as excinfo:
            MemcachedBackend(settings=MemcachedSettings())

        assert "Failed to initialize Memcached client" in str(excinfo.value)


@pytest.mark.asyncio
async def test_increment_and_check_new_key(memcached_backend, mock_aiomcache):
    """Test incrementing a counter for a new key."""
    mock_aiomcache.get.return_value = None

    count, is_limited = await memcached_backend.increment_and_check(key="test:123", limit=5, period=60)

    assert count == 1
    assert is_limited is False

    assert mock_aiomcache.get.called
    assert mock_aiomcache.set.called

    set_args = mock_aiomcache.set.call_args.args
    assert set_args[1] == b"1"
    assert mock_aiomcache.set.call_args.kwargs["exptime"] == 60


@pytest.mark.asyncio
async def test_increment_and_check_existing_key(memcached_backend, mock_aiomcache):
    """Test incrementing a counter for an existing key."""
    mock_aiomcache.get.return_value = b"4"

    count, is_limited = await memcached_backend.increment_and_check(key="test:123", limit=5, period=60)

    assert count == 5
    assert is_limited is False

    mock_aiomcache.get.assert_called_once()
    mock_aiomcache.set.assert_called_once()

    set_args = mock_aiomcache.set.call_args.args
    assert set_args[1] == b"5"


@pytest.mark.asyncio
async def test_rate_limited(memcached_backend, mock_aiomcache):
    """Test that requests are rate limited once limit is exceeded."""
    mock_aiomcache.get.return_value = b"5"

    count, is_limited = await memcached_backend.increment_and_check(key="test:123", limit=5, period=60)

    assert count == 6
    assert is_limited is True


@pytest.mark.asyncio
async def test_get_count(memcached_backend, mock_aiomcache):
    """Test getting the current count for a key."""
    mock_aiomcache.get.return_value = b"3"
    count = await memcached_backend.get_count("test:123")
    assert count == 3

    mock_aiomcache.get.return_value = None
    count = await memcached_backend.get_count("test:456")
    assert count is None


@pytest.mark.asyncio
async def test_reset(memcached_backend, mock_aiomcache):
    """Test resetting the counter for a key."""
    await memcached_backend.reset("test:123")
    mock_aiomcache.delete.assert_called_once_with(b"test:123")


@pytest.mark.asyncio
async def test_ping_success(memcached_backend, mock_aiomcache):
    """Test ping with successful connection."""
    mock_aiomcache.set.return_value = None
    mock_aiomcache.get.return_value = b"1"

    result = await memcached_backend.ping()
    assert result is True


@pytest.mark.asyncio
async def test_ping_failure(memcached_backend, mock_aiomcache):
    """Test ping with failed connection."""
    mock_aiomcache.set.side_effect = Exception("Connection failed")

    result = await memcached_backend.ping()
    assert result is False


@pytest.mark.asyncio
async def test_increment_error_handling(memcached_backend, mock_aiomcache):
    """Test error handling during increment operation."""
    mock_aiomcache.get.side_effect = Exception("Connection error")

    count, is_limited = await memcached_backend.increment_and_check(key="test:123", limit=5, period=60)

    assert count == 0
    assert is_limited is False
