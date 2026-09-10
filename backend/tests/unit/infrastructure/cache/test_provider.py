from unittest.mock import MagicMock

import pytest

from src.infrastructure.cache.exceptions import BackendNotFoundError
from src.infrastructure.cache.provider import CacheProvider


@pytest.fixture
def mock_backends():
    return {"redis": MagicMock(), "memcached": MagicMock()}


@pytest.fixture
def cache_provider(mock_backends):
    provider = CacheProvider()
    provider._backends = mock_backends
    provider._default_backend = "redis"
    return provider


def test_get_backend_default(cache_provider):
    backend = cache_provider.get_backend()
    assert backend == cache_provider._backends["redis"]


def test_get_backend_specific(cache_provider):
    backend = cache_provider.get_backend("memcached")
    assert backend == cache_provider._backends["memcached"]


def test_get_backend_not_found(cache_provider):
    with pytest.raises(BackendNotFoundError):
        cache_provider.get_backend("nonexistent")


def test_register_backend(cache_provider):
    new_backend = MagicMock()
    cache_provider.register_backend("new_backend", new_backend)
    assert cache_provider._backends["new_backend"] == new_backend

    returned_backend = cache_provider.get_backend("new_backend")
    assert returned_backend == new_backend


def test_set_default_backend(cache_provider):
    cache_provider.set_default_backend("memcached")
    assert cache_provider._default_backend == "memcached"

    backend = cache_provider.get_backend()
    assert backend == cache_provider._backends["memcached"]


def test_set_default_backend_not_found(cache_provider):
    with pytest.raises(BackendNotFoundError):
        cache_provider.set_default_backend("nonexistent")
