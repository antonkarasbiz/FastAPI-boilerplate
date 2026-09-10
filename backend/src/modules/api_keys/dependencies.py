from typing import Annotated

from fastapi import Depends

from .service import APIKeyService


def get_api_key_service() -> APIKeyService:
    return APIKeyService()


APIKeyServiceDep = Annotated[APIKeyService, Depends(get_api_key_service)]
