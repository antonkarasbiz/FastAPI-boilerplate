"""Rate limiter backend implementations.

This package contains implementations of rate limiter backends for different storage engines.
"""

import importlib.util

MEMCACHED_INSTALLED = importlib.util.find_spec("aiomcache") is not None
REDIS_INSTALLED = importlib.util.find_spec("redis") is not None

if MEMCACHED_INSTALLED:
    from .memcached import MemcachedBackend, MemcachedSettings  # noqa: F401

    __all__ = ["MemcachedBackend", "MemcachedSettings"]
else:
    MemcachedBackendType: type | None = None
    MemcachedSettingsType: type | None = None
    __all__ = []

if REDIS_INSTALLED:
    from .redis import RedisBackend, RedisSettings  # noqa: F401

    __all__.extend(["RedisBackend", "RedisSettings"])
else:
    RedisBackendType: type | None = None
    RedisSettingsType: type | None = None
