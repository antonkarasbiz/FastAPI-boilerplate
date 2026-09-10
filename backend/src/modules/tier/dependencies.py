from typing import Annotated

from fastapi import Depends

from .service import TierService


def get_tier_service() -> TierService:
    return TierService()


TierServiceDep = Annotated[TierService, Depends(get_tier_service)]
