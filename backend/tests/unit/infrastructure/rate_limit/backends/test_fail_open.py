"""Tests for the fail_open behavior in rate limiter backends."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from redis.exceptions import RedisError

from src.infrastructure.rate_limit.backends.memcached import MemcachedBackend, MemcachedSettings
from src.infrastructure.rate_limit.backends.redis import RedisBackend, RedisSettings


@pytest.fixture
def mock_redis_client():
    """Create a mock Redis client."""
    pipeline_mock = MagicMock()
    pipeline_mock.incr = MagicMock()
    pipeline_mock.expire = MagicMock()
    pipeline_mock.execute = AsyncMock(return_value=[1])

    client_mock = AsyncMock()
    client_mock.pipeline = MagicMock(return_value=pipeline_mock)
    client_mock.get = AsyncMock(return_value="1")
    client_mock.delete = AsyncMock(return_value=1)
    client_mock.ping = AsyncMock(return_value=True)

    return client_mock, pipeline_mock


@pytest.fixture
def mock_memcached_client():
    """Create a mock Memcached client."""
    client_mock = AsyncMock()
    client_mock.get = AsyncMock(return_value=b"1")
    client_mock.set = AsyncMock(return_value=True)
    client_mock.delete = AsyncMock(return_value=True)

    return client_mock


@pytest.fixture
def redis_backend_fail_open(mock_redis_client):
    """Create a RedisBackend with fail_open=True."""
    client_mock, pipeline_mock = mock_redis_client

    settings = RedisSettings(host="localhost", port=6379)
    backend = RedisBackend(settings=settings, fail_open=True)
    backend.client = client_mock

    yield backend, client_mock, pipeline_mock


@pytest.fixture
def redis_backend_fail_closed(mock_redis_client):
    """Create a RedisBackend with fail_open=False."""
    client_mock, pipeline_mock = mock_redis_client

    settings = RedisSettings(host="localhost", port=6379)
    backend = RedisBackend(settings=settings, fail_open=False)
    backend.client = client_mock

    yield backend, client_mock, pipeline_mock


@pytest.fixture
def memcached_backend_fail_open(mock_memcached_client):
    """Create a MemcachedBackend with fail_open=True."""
    settings = MemcachedSettings(host="localhost", port=11211)
    backend = MemcachedBackend(settings=settings, fail_open=True)
    backend.client = mock_memcached_client

    yield backend, mock_memcached_client


@pytest.fixture
def memcached_backend_fail_closed(mock_memcached_client):
    """Create a MemcachedBackend with fail_open=False."""
    settings = MemcachedSettings(host="localhost", port=11211)
    backend = MemcachedBackend(settings=settings, fail_open=False)
    backend.client = mock_memcached_client

    yield backend, mock_memcached_client


@pytest.mark.asyncio
async def test_redis_error_handling_fail_open(redis_backend_fail_open):
    """Test Redis error handling with fail_open=True."""
    backend, _, pipeline_mock = redis_backend_fail_open

    pipeline_mock.execute.side_effect = RedisError("Test Redis error")

    count, is_limited = await backend.increment_and_check(key="test:123", limit=5, period=60)

    assert count == 0
    assert is_limited is False


@pytest.mark.asyncio
async def test_redis_error_handling_fail_closed(redis_backend_fail_closed):
    """Test Redis error handling with fail_open=False."""
    backend, _, pipeline_mock = redis_backend_fail_closed

    pipeline_mock.execute.side_effect = RedisError("Test Redis error")

    count, is_limited = await backend.increment_and_check(key="test:123", limit=5, period=60)

    assert count == 0
    assert is_limited is True


@pytest.mark.asyncio
async def test_redis_general_error_fail_open(redis_backend_fail_open):
    """Test general error handling with fail_open=True in Redis backend."""
    backend, _, pipeline_mock = redis_backend_fail_open

    pipeline_mock.execute.side_effect = Exception("General error")

    count, is_limited = await backend.increment_and_check(key="test:123", limit=5, period=60)

    assert count == 0
    assert is_limited is False


@pytest.mark.asyncio
async def test_redis_general_error_fail_closed(redis_backend_fail_closed):
    """Test general error handling with fail_open=False in Redis backend."""
    backend, _, pipeline_mock = redis_backend_fail_closed

    pipeline_mock.execute.side_effect = Exception("General error")

    count, is_limited = await backend.increment_and_check(key="test:123", limit=5, period=60)

    assert count == 0
    assert is_limited is True


@pytest.mark.asyncio
async def test_memcached_error_fail_open(memcached_backend_fail_open):
    """Test error handling with fail_open=True in Memcached backend."""
    backend, client_mock = memcached_backend_fail_open

    client_mock.get.side_effect = Exception("Memcached error")

    count, is_limited = await backend.increment_and_check(key="test:123", limit=5, period=60)

    assert count == 0
    assert is_limited is False


@pytest.mark.asyncio
async def test_memcached_error_fail_closed(memcached_backend_fail_closed):
    """Test error handling with fail_open=False in Memcached backend."""
    backend, client_mock = memcached_backend_fail_closed

    client_mock.get.side_effect = Exception("Memcached error")

    count, is_limited = await backend.increment_and_check(key="test:123", limit=5, period=60)

    assert count == 0
    assert is_limited is True
