from abc import ABC, abstractmethod
from typing import Any


class CacheBackend(ABC):
    """Abstract base class for cache backends with comprehensive caching interface.

    Defines the standard interface that all cache backend implementations must follow,
    providing consistent caching operations across different backend technologies
    like Redis, Memcached, or in-memory storage.

    This abstract base class ensures:
    - Consistent API across different cache implementations
    - Type safety with proper return types
    - Comprehensive cache operations including pattern-based deletion
    - Health checking and connection management
    - Proper error handling patterns

    Implementations should handle:
    - Serialization/deserialization of cached values
    - Connection management and retries
    - Backend-specific optimizations
    - Error handling and fallback behavior

    Example:
        ```python
        class RedisCacheBackend(CacheBackend):
            async def get(self, key: str) -> Optional[Any]:
                try:
                    return await self.redis.get(key)
                except ConnectionError:
                    return None
        ```
    """

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """Retrieve a value from the cache by key.

        Attempts to fetch a cached value for the given key. Returns None
        if the key doesn't exist, has expired, or if there's a connection error.

        Args:
            key: The cache key to retrieve. Should be a string identifier.

        Returns:
            The cached value if found, None otherwise. The value is automatically
            deserialized from the backend's storage format.

        Note:
            Implementation should handle:
            - Key normalization and validation
            - Automatic deserialization of stored values
            - Connection errors gracefully (return None)
            - Expired key cleanup where applicable

        Example:
            ```python
            # Get user data from cache
            user_data = await cache.get("user:123")
            if user_data is None:
                # Cache miss - load from database
                user_data = await load_user_from_db(123)
                await cache.set("user:123", user_data, 3600)
            ```
        """
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, expiration: int = 3600) -> None:
        """Store a value in the cache with optional expiration.

        Stores a value in the cache with the specified key and expiration time.
        The value is automatically serialized for storage in the backend.

        Args:
            key: The cache key to store the value under.
            value: The value to cache. Will be automatically serialized.
            expiration: Time in seconds before the key expires (default: 3600).

        Note:
            Implementation should handle:
            - Automatic serialization of values
            - Key normalization and validation
            - Expiration time validation and limits
            - Connection errors gracefully
            - Backend-specific storage optimizations

        Example:
            ```python
            # Cache user data for 1 hour
            await cache.set("user:123", user_data, 3600)

            # Cache with default expiration (1 hour)
            await cache.set("session:abc", session_data)
            ```
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Remove a specific key from the cache.

        Deletes a single cache entry by key. Operations should be idempotent
        and not raise errors if the key doesn't exist.

        Args:
            key: The cache key to delete.

        Note:
            Implementation should handle:
            - Key normalization and validation
            - Idempotent deletion (no error if key doesn't exist)
            - Connection errors gracefully
            - Cleanup of any related metadata

        Example:
            ```python
            # Delete user cache when user is updated
            await cache.delete("user:123")

            # Delete session on logout
            await cache.delete(f"session:{session_id}")
            ```
        """
        pass

    @abstractmethod
    async def delete_pattern(self, pattern: str) -> None:
        """Delete all keys matching a specific pattern.

        Removes multiple cache entries that match the given pattern.
        This is useful for invalidating related cache entries or
        clearing cache namespaces.

        Args:
            pattern: The pattern to match against keys. Pattern syntax
                    depends on the backend implementation (e.g., Redis glob patterns).

        Note:
            Implementation should handle:
            - Backend-specific pattern syntax
            - Efficient bulk deletion operations
            - Connection errors gracefully
            - Large result set handling with pagination

        Example:
            ```python
            # Delete all user-related cache entries
            await cache.delete_pattern("user:*")

            # Delete all cache entries for a specific tenant
            await cache.delete_pattern("tenant:123:*")
            ```
        """
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if a key exists in the cache.

        Determines whether a key exists in the cache without retrieving its value.
        This is more efficient than getting the value when you only need to
        check existence.

        Args:
            key: The cache key to check for existence.

        Returns:
            True if the key exists and hasn't expired, False otherwise.

        Note:
            Implementation should handle:
            - Key normalization and validation
            - Expired key detection
            - Connection errors gracefully (return False)
            - Backend-specific existence checks

        Example:
            ```python
            # Check if user is cached before expensive operation
            if await cache.exists("user:123"):
                user_data = await cache.get("user:123")
            else:
                user_data = await load_user_from_db(123)
                await cache.set("user:123", user_data)
            ```
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear the entire cache.

        Removes all cache entries from the backend. This is a destructive
        operation that should be used with caution.

        Note:
            Implementation should handle:
            - Efficient bulk deletion of all entries
            - Connection errors gracefully
            - Backend-specific clear operations
            - Cleanup of any metadata or indexes

        Example:
            ```python
            # Clear all cache during deployment
            await cache.clear()

            # Clear cache in test cleanup
            await cache.clear()
            ```
        """
        pass

    @abstractmethod
    async def ping(self) -> bool:
        """Check if the cache backend is available and responsive.

        Performs a health check on the cache backend to determine if it's
        available and responding to requests. This is useful for health
        checks and monitoring.

        Returns:
            True if the cache backend is available and responsive, False otherwise.

        Note:
            Implementation should handle:
            - Quick connectivity test
            - Timeout handling for unresponsive backends
            - Authentication validation
            - Minimal resource usage for health checks

        Example:
            ```python
            # Health check endpoint
            if await cache.ping():
                return {"cache": "healthy"}
            else:
                return {"cache": "unhealthy"}
            ```
        """
        pass
