import functools
from collections.abc import Callable
from typing import Any, TypeVar, cast

from fastapi import Request, Response
from fastapi.encoders import jsonable_encoder

from ..logging import get_logger
from .exceptions import CacheException, InvalidRequestError
from .provider import cache_provider
from .utils import format_extra_data, format_prefix, infer_resource_id


class PatternMatchingNotSupportedError(CacheException):
    """Exception raised when pattern-based deletion is not supported by the backend."""

    def __init__(self, pattern: str):
        self.message = f"Pattern-based deletion is not supported. Pattern '{pattern}' cannot be used."
        super().__init__(self.message)


try:
    from .backends.memcached import (
        PatternMatchingNotSupportedError as MemcachedPatternMatchingNotSupportedError,
    )
except (ImportError, AttributeError):
    pass

logger = get_logger()

T = TypeVar("T", bound=Callable[..., Any])


def cache(
    key_prefix: str,
    resource_id_name: Any = None,
    expiration: int = 3600,
    resource_id_type: type | tuple[type, ...] = int,
    to_invalidate_extra: dict[str, Any] | None = None,
    pattern_to_invalidate_extra: list[str] | None = None,
    backend_name: str | None = None,
) -> Callable[[T], T]:
    """Cache decorator for FastAPI endpoints.

    Args:
        key_prefix: A unique prefix to identify the cache key.
        resource_id_name: The name of the resource ID argument. If None, it will be inferred.
        expiration: The expiration time for the cached data in seconds. Default is 3600 (1 hour).
        resource_id_type: The expected type of the resource ID. Default is int.
        to_invalidate_extra: Additional cache keys to invalidate.
        pattern_to_invalidate_extra: Patterns for additional cache keys to invalidate.
        backend_name: The name of the cache backend to use. If None, the default is used.

    Returns:
        A decorator function for FastAPI endpoint functions.

    Example:
        @app.get("/users/{user_id}")
        @cache(key_prefix="user", resource_id_name="user_id", expiration=600)
        async def get_user(request: Request, user_id: int):
            # Your logic here
            return {"id": user_id, "name": "John Doe"}
    """

    def wrapper(func: T) -> T:
        @functools.wraps(func)
        async def inner(request: Request, *args: Any, **kwargs: Any) -> Response:
            try:
                backend = cache_provider.get_backend(backend_name)
            except Exception as e:
                logger.warning(f"Cache backend not available: {str(e)}")
                return cast(Response, await func(request, *args, **kwargs))

            if resource_id_name:
                resource_id = kwargs[resource_id_name]
            else:
                try:
                    resource_id = infer_resource_id(kwargs=kwargs, resource_id_type=resource_id_type)
                except Exception:
                    logger.warning("Could not infer resource ID, skipping cache")
                    return cast(Response, await func(request, *args, **kwargs))

            formatted_key_prefix = format_prefix(key_prefix, kwargs)
            cache_key = f"{formatted_key_prefix}:{resource_id}"

            if request.method == "GET":
                if to_invalidate_extra is not None or pattern_to_invalidate_extra is not None:
                    raise InvalidRequestError("Cache invalidation not allowed on GET requests")

                cached_data = await backend.get(cache_key)
                if cached_data:
                    return cast(Response, cached_data)

            result = await func(request, *args, **kwargs)

            if request.method == "GET":
                serializable_data = jsonable_encoder(result)
                await backend.set(cache_key, serializable_data, expiration)

            else:
                await backend.delete(cache_key)

                if to_invalidate_extra is not None:
                    formatted_extra = format_extra_data(to_invalidate_extra, kwargs)
                    for prefix, id in formatted_extra.items():
                        extra_cache_key = f"{prefix}:{id}"
                        await backend.delete(extra_cache_key)

                if pattern_to_invalidate_extra is not None:
                    for pattern in pattern_to_invalidate_extra:
                        try:
                            formatted_pattern = format_prefix(pattern, kwargs)
                            await backend.delete_pattern(formatted_pattern)
                        except (
                            PatternMatchingNotSupportedError,
                            MemcachedPatternMatchingNotSupportedError,
                        ) as e:
                            logger.error(str(e))

            return cast(Response, result)

        return cast(T, inner)

    return wrapper
