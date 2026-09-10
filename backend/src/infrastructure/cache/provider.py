from typing import Any

from .base import CacheBackend
from .exceptions import BackendNotFoundError


class CacheProvider:
    """Provider for cache backends.

    This class manages the different cache backends and provides a single point of access
    for all cache operations. It supports registering multiple backends and switching
    between them at runtime.
    """

    def __init__(self) -> None:
        """Initialize the cache provider."""
        self._backends: dict[str, CacheBackend] = {}
        self._default_backend: str | None = None

    def register_backend(self, name: str, backend: CacheBackend, default: bool = False) -> None:
        """Register a cache backend.

        Args:
            name: The name of the backend.
            backend: The backend instance.
            default: Whether this backend should be the default.
        """
        self._backends[name] = backend
        if default or self._default_backend is None:
            self._default_backend = name

    def get_backend(self, name: str | None = None) -> CacheBackend:
        """Get a cache backend by name.

        Args:
            name: The name of the backend to get. If None, the default backend is returned.

        Returns:
            The requested cache backend.

        Raises:
            BackendNotFoundError: If the requested backend is not available.
        """
        backend_name = name or self._default_backend
        if backend_name is None or backend_name not in self._backends:
            raise BackendNotFoundError(f"Backend '{backend_name}' is not available.")

        return self._backends[backend_name]

    def set_default_backend(self, name: str) -> None:
        """Set the default backend to use.

        Args:
            name: The name of the backend to set as default.

        Raises:
            BackendNotFoundError: If the backend does not exist.
        """
        if name not in self._backends:
            raise BackendNotFoundError(f"Backend '{name}' not found. Cannot set as default.")

        self._default_backend = name

    async def ping_all(self) -> dict[str, bool]:
        """Ping all registered backends.

        Returns:
            A dictionary mapping backend names to their availability.
        """
        results = {}
        for name, backend in self._backends.items():
            results[name] = await backend.ping()
        return results

    def list_backends(self) -> dict[str, type[CacheBackend]]:
        """List all registered backends.

        Returns:
            A dictionary mapping backend names to their types.
        """
        return {name: type(backend) for name, backend in self._backends.items()}

    @property
    def default_backend_name(self) -> str | None:
        """Get the name of the default backend.

        Returns:
            The name of the default backend, or None if no backends are registered.
        """
        return self._default_backend


cache_provider = CacheProvider()


async def get(key: str, backend_name: str | None = None) -> Any:
    """Get a value from the cache.

    Args:
        key: The cache key to get.
        backend_name: The name of the backend to use. If None, the default backend is used.

    Returns:
        The cached value, or None if it doesn't exist.
    """
    backend = cache_provider.get_backend(backend_name)
    return await backend.get(key)


async def set(key: str, value: Any, expiration: int = 3600, backend_name: str | None = None) -> None:
    """Set a value in the cache.

    Args:
        key: The cache key to set.
        value: The value to cache.
        expiration: Time in seconds before the key expires (default: 3600).
        backend_name: The name of the backend to use. If None, the default backend is used.
    """
    backend = cache_provider.get_backend(backend_name)
    await backend.set(key, value, expiration)


async def delete(key: str, backend_name: str | None = None) -> None:
    """Delete a key from the cache.

    Args:
        key: The cache key to delete.
        backend_name: The name of the backend to use. If None, the default backend is used.
    """
    backend = cache_provider.get_backend(backend_name)
    await backend.delete(key)


async def delete_pattern(pattern: str, backend_name: str | None = None) -> None:
    """Delete all keys matching a pattern.

    Args:
        pattern: The pattern to match against keys.
        backend_name: The name of the backend to use. If None, the default backend is used.
    """
    backend = cache_provider.get_backend(backend_name)
    await backend.delete_pattern(pattern)


async def exists(key: str, backend_name: str | None = None) -> bool:
    """Check if a key exists in the cache.

    Args:
        key: The cache key to check.
        backend_name: The name of the backend to use. If None, the default backend is used.

    Returns:
        True if the key exists, False otherwise.
    """
    backend = cache_provider.get_backend(backend_name)
    return await backend.exists(key)


async def clear(backend_name: str | None = None) -> None:
    """Clear the entire cache.

    Args:
        backend_name: The name of the backend to use. If None, the default backend is used.
    """
    backend = cache_provider.get_backend(backend_name)
    await backend.clear()
