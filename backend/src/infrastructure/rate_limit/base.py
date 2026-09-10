from abc import ABC, abstractmethod


class RateLimiterBackend(ABC):
    """Abstract base class for rate limiter backends with comprehensive interface.

    Defines the standard interface that all rate limiter backend implementations
    must follow, providing consistent rate limiting operations across different
    backend technologies like Redis, Memcached, or in-memory storage.

    This abstract base class ensures:
    - Consistent API across different rate limiter implementations
    - Flexible failure handling with fail-open/fail-closed policies
    - Comprehensive rate limiting operations including counters and resets
    - Health checking and connection management
    - Proper error handling patterns

    Implementations should handle:
    - Thread-safe counter operations
    - Atomic increment-and-check operations
    - Connection management and retries
    - Backend-specific optimizations
    - Error handling and fallback behavior

    Example:
        ```python
        class RedisRateLimiterBackend(RateLimiterBackend):
            async def increment_and_check(self, key: str, limit: int, period: int) -> tuple[int, bool]:
                try:
                    count = await self.redis.incr(key)
                    if count == 1:
                        await self.redis.expire(key, period)
                    return count, count > limit
                except ConnectionError:
                    return (0, False) if self.fail_open else (limit + 1, True)
        ```
    """

    def __init__(self, fail_open: bool = True):
        """Initialize the rate limiter backend with failure handling policy.

        Args:
            fail_open: Whether to fail open (allow requests) when rate limiting
                      errors occur. If True, allows requests when backend is unavailable.
                      If False, blocks requests when backend errors occur.
                      Default is True for safety and availability.

        Note:
            Fail-open vs fail-closed policies:
            - Fail-open: Prioritizes availability over strict rate limiting
            - Fail-closed: Prioritizes security over availability

            Choose based on your application's requirements:
            - Critical APIs may prefer fail-closed for security
            - Public APIs may prefer fail-open for availability
        """
        self.fail_open = fail_open

    @abstractmethod
    async def increment_and_check(self, key: str, limit: int, period: int) -> tuple[int, bool]:
        """Increment the counter for a key and check if rate limit is exceeded.

        Performs an atomic increment-and-check operation to determine if a
        request should be rate limited. This is the core operation for most
        rate limiting scenarios.

        Args:
            key: The rate limit key to increment. Should be unique per user/IP/resource.
            limit: Maximum number of requests allowed in the period.
            period: Time period in seconds for the rate limit window.

        Returns:
            Tuple of (current_count, is_rate_limited) where:
            - current_count: The current count of requests in the window
            - is_rate_limited: True if the rate limit is exceeded, False otherwise

        Note:
            Implementation should handle:
            - Atomic increment operations to prevent race conditions
            - Automatic key expiration after the period
            - Connection errors according to fail_open policy
            - Efficient sliding window or fixed window algorithms

        Example:
            ```python
            # Check if user can make a request (10 requests per minute)
            count, is_limited = await backend.increment_and_check(
                key="user:123:api_calls",
                limit=10,
                period=60
            )

            if is_limited:
                raise RateLimitException(f"Rate limit exceeded. {count}/{limit} requests used.")
            ```
        """
        pass

    @abstractmethod
    async def get_count(self, key: str) -> int | None:
        """Get the current count for a rate limit key.

        Retrieves the current count without incrementing it. Useful for
        monitoring, dashboards, and providing rate limit information to clients.

        Args:
            key: The rate limit key to check.

        Returns:
            The current count or None if the key doesn't exist or has expired.

        Note:
            Implementation should handle:
            - Key normalization and validation
            - Expired key cleanup where applicable
            - Connection errors gracefully (return None)
            - Efficient read operations

        Example:
            ```python
            # Check current usage for rate limit headers
            current_count = await backend.get_count("user:123:api_calls")
            if current_count is not None:
                remaining = max(0, limit - current_count)
                headers["X-RateLimit-Remaining"] = str(remaining)
            ```
        """
        pass

    @abstractmethod
    async def reset(self, key: str) -> None:
        """Reset the counter for a specific rate limit key.

        Removes or resets the counter for a given key, effectively clearing
        the rate limit for that key. Useful for administrative actions,
        premium users, or error recovery.

        Args:
            key: The rate limit key to reset.

        Note:
            Implementation should handle:
            - Key normalization and validation
            - Idempotent deletion (no error if key doesn't exist)
            - Connection errors gracefully
            - Cleanup of any related metadata

        Example:
            ```python
            # Reset rate limit for premium user
            await backend.reset("user:123:api_calls")

            # Reset after resolving user issue
            await backend.reset(f"user:{user_id}:failed_logins")
            ```
        """
        pass

    @abstractmethod
    async def increment(self, key: str, amount: int = 1, expiry: int = 300) -> int:
        """Increment a counter by the given amount and set expiry.

        Provides flexible counter increment operations with configurable
        expiry times. Useful for custom rate limiting scenarios and
        batched operations.

        Args:
            key: The key to increment.
            amount: Amount to increment by (default: 1).
            expiry: Time in seconds for the key to expire (default: 300).

        Returns:
            The new value after incrementing.

        Note:
            Implementation should handle:
            - Atomic increment operations
            - Automatic key expiration
            - Connection errors according to fail_open policy
            - Efficient batch operations for multiple increments

        Example:
            ```python
            # Increment by custom amount for bulk operations
            new_count = await backend.increment(
                key="user:123:bulk_uploads",
                amount=10,  # 10 files uploaded
                expiry=3600  # 1 hour window
            )
            ```
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a rate limit key.

        Removes a specific key from the rate limiter backend. Similar to reset
        but returns information about whether the key existed.

        Args:
            key: The key to delete.

        Returns:
            True if the key existed and was deleted, False otherwise.

        Note:
            Implementation should handle:
            - Key normalization and validation
            - Atomic deletion operations
            - Connection errors gracefully
            - Cleanup of any related metadata

        Example:
            ```python
            # Clean up expired user session
            existed = await backend.delete("user:123:session_requests")
            if existed:
                logger.info("Cleaned up rate limit data for user session")
            ```
        """
        pass

    @abstractmethod
    async def ping(self) -> bool:
        """Check if the rate limiter backend is available and responsive.

        Performs a health check on the rate limiter backend to determine if it's
        available and responding to requests. This is essential for monitoring
        and graceful degradation.

        Returns:
            True if the backend is available and responsive, False otherwise.

        Note:
            Implementation should handle:
            - Quick connectivity test
            - Timeout handling for unresponsive backends
            - Authentication validation
            - Minimal resource usage for health checks

        Example:
            ```python
            # Health check in monitoring system
            if await backend.ping():
                metrics.gauge("rate_limiter.health", 1)
            else:
                metrics.gauge("rate_limiter.health", 0)
                logger.warning("Rate limiter backend is unavailable")
            ```
        """
        pass
