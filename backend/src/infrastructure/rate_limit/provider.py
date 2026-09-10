from .base import RateLimiterBackend
from .exceptions import BackendNotFoundError


class RateLimiterProvider:
    """Provider for rate limiter backends with comprehensive backend management.

    This class manages multiple rate limiter backends and provides a centralized
    access point for all rate limiting operations. It supports dynamic backend
    registration, switching between backends, and health monitoring.

    The provider enables:
    - Multi-backend support for different use cases
    - Dynamic backend switching based on configuration
    - Health monitoring and fallback strategies
    - Centralized rate limiter configuration management

    Example:
        ```python
        # Initialize provider and register backends
        provider = RateLimiterProvider()

        # Register Redis backend for production
        redis_backend = RedisRateLimiterBackend(host="redis.example.com")
        provider.register_backend("redis", redis_backend, default=True)

        # Register in-memory backend for testing
        memory_backend = MemoryRateLimiterBackend()
        provider.register_backend("memory", memory_backend)

        # Use the provider
        backend = provider.get_backend("redis")
        count, is_limited = await backend.increment_and_check("user:123", 10, 60)
        ```
    """

    def __init__(self) -> None:
        """Initialize the rate limiter provider.

        Creates an empty provider with no registered backends. Backends must be
        registered before use via register_backend().

        Note:
            The provider starts with no default backend. The first registered
            backend becomes the default, or you can explicitly set a default
            using the default=True parameter in register_backend().
        """
        self._backends: dict[str, RateLimiterBackend] = {}
        self._default_backend: str | None = None

    def register_backend(self, name: str, backend: RateLimiterBackend, default: bool = False) -> None:
        """Register a rate limiter backend with the provider.

        Adds a backend to the provider's registry, making it available for
        rate limiting operations. Optionally sets the backend as the default.

        Args:
            name: The name of the backend for identification and retrieval.
            backend: The backend instance to register.
            default: Whether this backend should be the default. If True, or if
                    no default is set, this backend becomes the default.

        Note:
            Backend names should be unique within the provider. Registering
            a backend with an existing name will replace the previous backend.

            The first registered backend automatically becomes the default
            unless explicitly overridden.

        Example:
            ```python
            # Register primary Redis backend
            provider.register_backend(
                "redis-primary",
                RedisRateLimiterBackend(host="redis-primary.example.com"),
                default=True
            )

            # Register backup Redis backend
            provider.register_backend(
                "redis-backup",
                RedisRateLimiterBackend(host="redis-backup.example.com")
            )
            ```
        """
        self._backends[name] = backend
        if default or self._default_backend is None:
            self._default_backend = name

    def get_backend(self, name: str | None = None) -> RateLimiterBackend:
        """Get a rate limiter backend by name.

        Retrieves a registered backend by name, or returns the default backend
        if no name is specified.

        Args:
            name: The name of the backend to retrieve. If None, returns the
                 default backend.

        Returns:
            The requested rate limiter backend.

        Raises:
            BackendNotFoundError: If the requested backend is not found or
                                 no default backend is available.

        Example:
            ```python
            # Get default backend
            default_backend = provider.get_backend()

            # Get specific backend
            redis_backend = provider.get_backend("redis")

            # Handle missing backend
            try:
                backend = provider.get_backend("nonexistent")
            except BackendNotFoundError:
                backend = provider.get_backend()  # Fall back to default
            ```
        """
        backend_name = name or self._default_backend
        if not backend_name or backend_name not in self._backends:
            raise BackendNotFoundError(backend_name or "default")
        return self._backends[backend_name]

    def set_default_backend(self, name: str) -> None:
        """Set the default backend for the provider.

        Changes the default backend to the specified registered backend.
        The default backend is used when no specific backend is requested.

        Args:
            name: The name of the backend to set as default.

        Raises:
            BackendNotFoundError: If the requested backend is not found.

        Example:
            ```python
            # Switch to backup backend as default
            provider.set_default_backend("redis-backup")

            # Now all default operations use the backup backend
            backend = provider.get_backend()  # Returns redis-backup
            ```
        """
        if name not in self._backends:
            raise BackendNotFoundError(name)
        self._default_backend = name

    async def ping_all(self) -> dict[str, bool]:
        """Ping all registered backends to check their availability.

        Performs health checks on all registered backends to determine their
        current availability status. This is useful for monitoring, alerting,
        and automatic failover decisions.

        Returns:
            A dictionary mapping backend names to their availability status.
            True indicates the backend is available, False indicates it's not.

        Example:
            ```python
            # Check all backend health
            health_status = await provider.ping_all()

            # Log unhealthy backends
            for backend_name, is_healthy in health_status.items():
                if not is_healthy:
                    logger.warning(f"Backend {backend_name} is unhealthy")

            # Find healthy backends
            healthy_backends = [name for name, status in health_status.items() if status]
            ```
        """
        results = {}
        for name, backend in self._backends.items():
            results[name] = await backend.ping()
        return results

    def list_backends(self) -> dict[str, type[RateLimiterBackend]]:
        """List all registered backends with their types.

        Returns information about all registered backends, including their
        implementation types. Useful for debugging, monitoring, and
        administrative interfaces.

        Returns:
            A dictionary mapping backend names to their implementation types.

        Example:
            ```python
            # List all backends
            backends = provider.list_backends()
            for name, backend_type in backends.items():
                print(f"Backend: {name}, Type: {backend_type.__name__}")

            # Filter for Redis backends
            redis_backends = {
                name: backend_type for name, backend_type in backends.items()
                if "Redis" in backend_type.__name__
            }
            ```
        """
        return {name: type(backend) for name, backend in self._backends.items()}

    @property
    def default_backend_name(self) -> str | None:
        """Get the name of the default backend.

        Returns:
            The name of the default backend, or None if no default backend is set.

        Example:
            ```python
            # Check current default backend
            default_name = provider.default_backend_name
            if default_name:
                print(f"Default backend: {default_name}")
            else:
                print("No default backend configured")
            ```
        """
        return self._default_backend


rate_limiter_provider = RateLimiterProvider()


def get_rate_limiter_backend(backend_name: str | None = None) -> RateLimiterBackend:
    """Get a rate limiter backend by name from the global provider.

    This is a convenience function to get a rate limiter backend from the
    global provider instance. It provides a simple interface for accessing
    rate limiter backends throughout the application.

    Args:
        backend_name: The name of the backend to get. If None, the default
                     backend is used.

    Returns:
        The requested rate limiter backend.

    Raises:
        BackendNotFoundError: If the requested backend is not found.

    Example:
        ```python
        # Get default backend
        backend = get_rate_limiter_backend()

        # Get specific backend
        redis_backend = get_rate_limiter_backend("redis")

        # Use in dependency injection
        async def rate_limited_endpoint(
            backend: RateLimiterBackend = Depends(get_rate_limiter_backend)
        ):
            count, is_limited = await backend.increment_and_check("api_calls", 100, 3600)
        ```
    """
    return rate_limiter_provider.get_backend(backend_name)


async def increment_and_check(
    key: str, limit: int, period: int, backend_name: str | None = None, fail_open: bool | None = None
) -> tuple[int, bool]:
    """Increment the counter for a key and check if rate limit is exceeded.

    Convenience function that combines backend retrieval and rate limit checking
    in a single operation. Supports temporary fail-open policy overrides.

    Args:
        key: The rate limit key to increment.
        limit: Maximum number of requests allowed in the period.
        period: Time period in seconds.
        backend_name: The name of the backend to use. If None, the default
                     backend is used.
        fail_open: Whether to fail open if an error occurs. If None, uses
                  the backend's configured setting.

    Returns:
        Tuple of (current_count, is_rate_limited) where:
        - current_count: The current count of requests
        - is_rate_limited: True if the rate limit is exceeded, False otherwise

    Example:
        ```python
        # Basic rate limit check
        count, is_limited = await increment_and_check(
            key="user:123:api_calls",
            limit=100,
            period=3600
        )

        # With specific backend and fail-open override
        count, is_limited = await increment_and_check(
            key="user:123:critical_api",
            limit=10,
            period=60,
            backend_name="redis-primary",
            fail_open=False  # Strict enforcement
        )
        ```
    """
    backend = rate_limiter_provider.get_backend(backend_name)

    original_fail_open = None
    if fail_open is not None and fail_open != backend.fail_open:
        original_fail_open = backend.fail_open
        backend.fail_open = fail_open

    try:
        return await backend.increment_and_check(key, limit, period)
    finally:
        if original_fail_open is not None:
            backend.fail_open = original_fail_open


async def get_count(key: str, backend_name: str | None = None) -> int | None:
    """Get the current count for a key from the specified backend.

    Convenience function to get the current count for a rate limit key
    without incrementing it.

    Args:
        key: The rate limit key to check.
        backend_name: The name of the backend to use. If None, the default
                     backend is used.

    Returns:
        The current count or None if the key doesn't exist.

    Example:
        ```python
        # Check current usage
        current_count = await get_count("user:123:api_calls")
        if current_count is not None:
            remaining = max(0, limit - current_count)
            print(f"Remaining requests: {remaining}")
        ```
    """
    backend = rate_limiter_provider.get_backend(backend_name)
    return await backend.get_count(key)


async def reset(key: str, backend_name: str | None = None) -> None:
    """Reset the counter for a key using the specified backend.

    Convenience function to reset a rate limit counter, effectively
    clearing the rate limit for that key.

    Args:
        key: The rate limit key to reset.
        backend_name: The name of the backend to use. If None, the default
                     backend is used.

    Example:
        ```python
        # Reset rate limit for premium user
        await reset("user:123:api_calls")

        # Reset after resolving issue
        await reset("user:123:failed_logins", backend_name="redis-primary")
        ```
    """
    backend = rate_limiter_provider.get_backend(backend_name)
    await backend.reset(key)
