from fastapi import HTTPException, status


class RateLimitException(HTTPException):
    """Exception raised when a rate limit is exceeded.

    This HTTP exception is thrown when a client exceeds their allowed request
    rate, providing appropriate HTTP status code and headers for rate limiting.

    The exception automatically sets:
    - HTTP 429 (Too Many Requests) status code
    - Retry-After header indicating when to retry
    - Detailed error message for the client

    Args:
        detail: Custom error message describing the rate limit violation.
                Defaults to "Rate limit exceeded".

    Note:
        This exception follows RFC 6585 standards for HTTP 429 responses.
        The Retry-After header helps clients implement proper backoff strategies.

        Consider including additional information in the detail message:
        - Current rate limit values
        - Time until reset
        - Suggested retry intervals

    Example:
        ```python
        # Basic rate limit exceeded
        raise RateLimitException("Rate limit exceeded")

        # With detailed information
        raise RateLimitException(
            f"Rate limit exceeded. {count}/{limit} requests used. "
            f"Try again in {period} seconds."
        )

        # In middleware or endpoint
        try:
            await rate_limiter.check_limit(user_id, endpoint)
        except RateLimitException as e:
            logger.warning(f"Rate limit exceeded for user {user_id}: {e}")
            raise
        ```
    """

    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers={"Retry-After": "60"},
        )


class RateLimiterBackendException(Exception):
    """Base exception for rate limiter backend errors.

    Serves as the parent class for all rate limiter backend-specific exceptions,
    providing a common interface for error handling throughout the rate limiting
    infrastructure.

    Args:
        message: Detailed error message describing the backend failure.

    Note:
        This base class should not be raised directly. Instead, use
        specific subclasses that better describe the type of backend error.

        All rate limiter backend exceptions inherit from this base class,
        allowing for comprehensive error handling with a single exception
        type when needed.

    Example:
        ```python
        try:
            # Rate limiter backend operations
            await backend.increment_and_check(key, limit, period)
        except RateLimiterBackendException as e:
            logger.error(f"Rate limiter backend error: {e}")
            # Handle any backend-related error
        ```
    """

    def __init__(self, message: str = "Rate limiter backend error"):
        self.message = message
        super().__init__(self.message)


class BackendNotFoundError(RateLimiterBackendException):
    """Raised when a requested rate limiter backend is not found.

    This exception occurs when trying to use a rate limiter backend that hasn't
    been registered with the rate limiter provider or doesn't exist in the
    backend registry.

    Args:
        backend_name: The name of the backend that was not found.

    Note:
        This exception typically indicates:
        - Backend name typo in configuration
        - Backend not properly registered during initialization
        - Missing backend dependencies or imports
        - Configuration mismatch between environments

    Example:
        ```python
        try:
            backend = rate_limiter_provider.get_backend("nonexistent_backend")
        except BackendNotFoundError as e:
            logger.error(f"Rate limiter backend not found: {e}")
            # Fall back to default backend or raise configuration error
        ```
    """

    def __init__(self, backend_name: str):
        self.message = f"Rate limiter backend '{backend_name}' not found."
        super().__init__(self.message)


class BackendInitializationError(RateLimiterBackendException):
    """Raised when a rate limiter backend fails to initialize.

    This exception occurs when a backend cannot be properly initialized due to
    configuration errors, connection failures, or missing dependencies.

    Args:
        backend_name: The name of the backend that failed to initialize.
        reason: The specific reason why initialization failed.

    Note:
        This exception typically indicates:
        - Invalid configuration parameters
        - Network connectivity issues
        - Missing credentials or authentication failures
        - Backend service unavailability
        - Resource constraints or permission issues

    Example:
        ```python
        try:
            redis_backend = RedisRateLimiterBackend(
                host="invalid_host",
                port=6379
            )
            await redis_backend.initialize()
        except BackendInitializationError as e:
            logger.error(f"Failed to initialize rate limiter: {e}")
            # Try alternative backend or raise startup error
        ```
    """

    def __init__(self, backend_name: str, reason: str):
        self.message = f"Failed to initialize rate limiter backend '{backend_name}': {reason}"
        super().__init__(self.message)
