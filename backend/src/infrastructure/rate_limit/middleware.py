from collections.abc import Callable
from typing import Any, cast

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from ...modules.common.utils.logger import get_logger
from ...modules.rate_limit.crud import crud_rate_limits
from ...modules.rate_limit.schemas import RateLimitSelect
from ...modules.tier.crud import crud_tiers
from ...modules.tier.schemas import TierSelect
from ..config import get_settings
from ..database import async_session
from .exceptions import RateLimitException
from .provider import increment_and_check
from .utils import sanitize_path

logger = get_logger(__name__)

settings = get_settings()
DEFAULT_LIMIT = settings.DEFAULT_RATE_LIMIT_LIMIT
DEFAULT_PERIOD = settings.DEFAULT_RATE_LIMIT_PERIOD


async def get_optional_user(request: Request) -> dict[str, Any] | None:
    """Get the current user from the request, or None if not authenticated.

    This is a simplified version that assumes the user is stored in request.state.user.
    In a real application, you would need to implement proper user extraction from
    authentication tokens.
    """
    if hasattr(request.state, "user"):
        return cast(dict[str, Any], request.state.user)
    return None


async def _check_rate_limit(request: Request, db: AsyncSession, user: dict[str, Any] | None = None) -> None:
    """Internal implementation of check_rate_limit without FastAPI dependency injection.

    Args:
        request: The current request.
        db: The database session.
        user: The authenticated user, or None if not authenticated.

    Raises:
        RateLimitException: If the rate limit is exceeded.
    """
    if not settings.RATE_LIMITER_ENABLED:
        return

    if hasattr(request.app.state, "initialization_complete"):
        await request.app.state.initialization_complete.wait()

    original_path = request.url.path
    sanitized_path = sanitize_path(original_path)

    if user:
        user_id = user["id"]
        tier = await crud_tiers.get(db=db, id=user["tier_id"], schema_to_select=TierSelect)

        if tier:
            rate_limit = await crud_rate_limits.get(
                db=db, tier_id=tier["id"], path=sanitized_path, schema_to_select=RateLimitSelect
            )

            if not rate_limit:
                rate_limit = await crud_rate_limits.get(
                    db=db, tier_id=tier["id"], path=original_path, schema_to_select=RateLimitSelect
                )

            if rate_limit:
                limit, period = rate_limit["limit"], rate_limit["period"]
            else:
                logger.warning(
                    f"User {user_id} with tier '{tier['name']}' has no specific rate limit for path '{original_path}'. "
                    "Applying default rate limit."
                )
                limit, period = DEFAULT_LIMIT, DEFAULT_PERIOD
        else:
            logger.warning(f"User {user_id} has no assigned tier. Applying default rate limit.")
            limit, period = DEFAULT_LIMIT, DEFAULT_PERIOD
    else:
        user_id = request.client.host if request.client and hasattr(request.client, "host") else "unknown"
        limit, period = DEFAULT_LIMIT, DEFAULT_PERIOD

    key = f"ratelimit:{user_id}:{sanitized_path}"

    try:
        count, is_limited = await increment_and_check(
            key=key, limit=limit, period=period, fail_open=settings.RATE_LIMITER_FAIL_OPEN
        )

        request.state.rate_limit_headers = {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(max(0, limit - count)),
            "X-RateLimit-Reset": str(period),
        }

        if is_limited:
            logger.warning(f"Rate limit exceeded for {user_id} on path {sanitized_path}. Count: {count}, Limit: {limit}")
            raise RateLimitException(f"Rate limit exceeded. Try again in {period} seconds.")

    except RateLimitException:
        raise
    except Exception as e:
        logger.error(f"Error checking rate limit for {user_id} on path {sanitized_path}: {e}")
        if not settings.RATE_LIMITER_FAIL_OPEN:
            logger.warning("Blocking request due to fail-closed policy")
            raise RateLimitException("Error checking rate limit. Access denied as a precaution.")


async def check_rate_limit(
    request: Request,
    db: AsyncSession = Depends(async_session),
    user: dict[str, Any] | None = Depends(get_optional_user),
) -> None:
    """Check if the current request exceeds rate limits.

    Args:
        request: The current request.
        db: The database session.
        user: The authenticated user, or None if not authenticated.

    Raises:
        RateLimitException: If the rate limit is exceeded.
    """
    await _check_rate_limit(request, db, user)


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Middleware for applying rate limits to all requests."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process a request through the middleware.

        Args:
            request: The incoming request.
            call_next: The next middleware or handler in the chain.

        Returns:
            The response from the next middleware or handler.
        """
        response = await call_next(request)

        if hasattr(request.state, "rate_limit_headers"):
            for key, value in request.state.rate_limit_headers.items():
                response.headers[key] = value

        return cast(Response, response)
