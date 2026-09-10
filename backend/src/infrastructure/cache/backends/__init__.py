"""
Caching backend implementations.

This module contains implementations of various cache backends that follow the
CacheBackend interface.
"""

from importlib.util import find_spec

MEMCACHED_INSTALLED = find_spec("aiomcache") is not None
REDIS_INSTALLED = find_spec("redis.asyncio") is not None

if MEMCACHED_INSTALLED:
    from .memcached import (
        MemcachedBackend,
        MemcachedSettings,
        PatternMatchingNotSupportedError,
    )
else:
    MemcachedBackend = None  # type: ignore
    MemcachedSettings = None  # type: ignore
    PatternMatchingNotSupportedError = None  # type: ignore

if REDIS_INSTALLED:
    from .redis import RedisBackend, RedisSettings
else:
    RedisBackend = None  # type: ignore
    RedisSettings = None  # type: ignore

__all__ = ["MemcachedBackend", "MemcachedSettings", "RedisBackend", "RedisSettings"]
if MEMCACHED_INSTALLED:
    __all__.append("PatternMatchingNotSupportedError")
