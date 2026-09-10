from unittest.mock import AsyncMock, patch

import pytest
from fastapi import Request

from src.infrastructure.cache.decorator import cache
from src.infrastructure.cache.exceptions import InvalidRequestError


@pytest.fixture
def mock_backend():
    mock = AsyncMock()
    mock.get = AsyncMock()
    mock.set = AsyncMock()
    mock.delete = AsyncMock()
    mock.delete_pattern = AsyncMock()
    return mock


@pytest.fixture
def mock_cache_provider():
    with patch("src.infrastructure.cache.decorator.cache_provider") as mock_provider:
        yield mock_provider


@pytest.mark.asyncio
async def test_cache_get_request_hit(mock_backend, mock_cache_provider):
    mock_cache_provider.get_backend.return_value = mock_backend
    cached_response = {"data": "cached_value"}
    mock_backend.get.return_value = cached_response

    @cache(key_prefix="test", resource_id_name="item_id")
    async def mock_endpoint(request: Request, item_id: int):
        pytest.fail("Endpoint was called despite cache hit")

    mock_request = AsyncMock()
    mock_request.method = "GET"

    result = await mock_endpoint(mock_request, item_id=123)

    assert result == cached_response
    mock_backend.get.assert_called_once_with("test:123")
    mock_backend.set.assert_not_called()


@pytest.mark.asyncio
async def test_cache_get_request_miss(mock_backend, mock_cache_provider):
    mock_cache_provider.get_backend.return_value = mock_backend
    mock_backend.get.return_value = None
    expected_response = {"data": "fresh_value"}

    @cache(key_prefix="test", resource_id_name="item_id")
    async def mock_endpoint(request: Request, item_id: int):
        return expected_response

    mock_request = AsyncMock()
    mock_request.method = "GET"

    result = await mock_endpoint(mock_request, item_id=123)

    assert result == expected_response
    mock_backend.get.assert_called_once_with("test:123")
    mock_backend.set.assert_called_once()


@pytest.mark.asyncio
async def test_cache_non_get_request_invalidation(mock_backend, mock_cache_provider):
    mock_cache_provider.get_backend.return_value = mock_backend
    expected_response = {"data": "updated_value"}

    @cache(key_prefix="test", resource_id_name="item_id")
    async def mock_endpoint(request: Request, item_id: int):
        return expected_response

    mock_request = AsyncMock()
    mock_request.method = "PUT"

    result = await mock_endpoint(mock_request, item_id=123)

    assert result == expected_response
    mock_backend.get.assert_not_called()
    mock_backend.set.assert_not_called()
    mock_backend.delete.assert_called_once_with("test:123")


@pytest.mark.asyncio
async def test_cache_extra_invalidation(mock_backend, mock_cache_provider):
    mock_cache_provider.get_backend.return_value = mock_backend
    expected_response = {"data": "updated_value"}

    @cache(
        key_prefix="test",
        resource_id_name="item_id",
        to_invalidate_extra={"related": "related_id"},
    )
    async def mock_endpoint(request: Request, item_id: int, related_id: int):
        return expected_response

    mock_request = AsyncMock()
    mock_request.method = "PUT"

    result = await mock_endpoint(mock_request, item_id=123, related_id=456)

    assert result == expected_response
    mock_backend.delete.assert_any_call("test:123")
    mock_backend.delete.assert_any_call("related:456")


@pytest.mark.asyncio
async def test_cache_pattern_invalidation(mock_backend, mock_cache_provider):
    mock_cache_provider.get_backend.return_value = mock_backend
    expected_response = {"data": "updated_value"}

    @cache(
        key_prefix="test",
        resource_id_name="item_id",
        pattern_to_invalidate_extra=["pattern_*"],
    )
    async def mock_endpoint(request: Request, item_id: int):
        return expected_response

    mock_request = AsyncMock()
    mock_request.method = "PUT"

    result = await mock_endpoint(mock_request, item_id=123)

    assert result == expected_response
    mock_backend.delete.assert_called_once_with("test:123")
    mock_backend.delete_pattern.assert_called_once_with("pattern_*")


@pytest.mark.asyncio
async def test_cache_get_with_invalidation_raises_error(mock_backend, mock_cache_provider):
    mock_cache_provider.get_backend.return_value = mock_backend

    @cache(
        key_prefix="test",
        resource_id_name="item_id",
        to_invalidate_extra={"related": "related_id"},
    )
    async def mock_endpoint(request: Request, item_id: int, related_id: int):
        return {"data": "value"}

    mock_request = AsyncMock()
    mock_request.method = "GET"

    with pytest.raises(InvalidRequestError):
        await mock_endpoint(mock_request, item_id=123, related_id=456)
