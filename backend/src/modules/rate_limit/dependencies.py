from typing import Annotated

from fastapi import Depends

from .service import RateLimitService


def get_rate_limit_service() -> RateLimitService:
    return RateLimitService()


RateLimitServiceDep = Annotated[RateLimitService, Depends(get_rate_limit_service)]
