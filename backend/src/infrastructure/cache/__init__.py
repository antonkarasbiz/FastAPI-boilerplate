from importlib.util import find_spec

from .base import CacheBackend
from .decorator import cache
from .provider import cache_provider, clear, delete, delete_pattern, exists, get, set

MEMCACHED_INSTALLED = find_spec("aiomcache") is not None
REDIS_INSTALLED = find_spec("redis.asyncio") is not None

if MEMCACHED_INSTALLED:
    from .backends.memcached import MemcachedBackend, MemcachedSettings
else:
    MemcachedBackend = None  # type: ignore
    MemcachedSettings = None  # type: ignore

if REDIS_INSTALLED:
    from .backends.redis import RedisBackend, RedisSettings
else:
    RedisBackend = None  # type: ignore
    RedisSettings = None  # type: ignore

__all__ = [
    "CacheBackend",
    "MemcachedBackend",
    "RedisBackend",
    "MemcachedSettings",
    "RedisSettings",
    "cache",
    "cache_provider",
    "get",
    "set",
    "delete",
    "delete_pattern",
    "exists",
    "clear",
    "REDIS_INSTALLED",
    "MEMCACHED_INSTALLED",
]
