"""API Key Management Module.

This module provides comprehensive API key management functionality
for developer-facing products and API-first business models.

Key Features:
- Secure API key generation and storage
- Permission-based access control
- Usage tracking per API key
- Key rotation and revocation
- Analytics and usage reporting
- Granular permissions system
"""

from .crud import crud_api_keys, crud_key_permissions, crud_key_usage
from .enums import HTTPMethod, KeyPermissionAction, KeyPermissionResource, KeyStatus, KeyType
from .models import APIKey, KeyPermission, KeyUsage
from .schemas import (
    APIKeyBase,
    APIKeyCreate,
    APIKeyRead,
    APIKeyResponse,
    APIKeyUpdate,
    APIKeyValidationRequest,
    APIKeyValidationResponse,
    APIKeyWithPermissions,
    KeyPermissionBase,
    KeyPermissionCreate,
    KeyPermissionRead,
    KeyPermissionUpdate,
    KeyUsageAnalytics,
    KeyUsageBase,
    KeyUsageCreate,
    KeyUsageRead,
    UserAPIKeySummary,
)
from .service import APIKeyService

__all__ = [
    # Models
    "APIKey",
    "KeyUsage",
    "KeyPermission",
    # Schemas
    "APIKeyBase",
    "APIKeyCreate",
    "APIKeyRead",
    "APIKeyResponse",
    "APIKeyUpdate",
    "KeyUsageBase",
    "KeyUsageCreate",
    "KeyUsageRead",
    "KeyPermissionBase",
    "KeyPermissionCreate",
    "KeyPermissionRead",
    "KeyPermissionUpdate",
    "APIKeyWithPermissions",
    "KeyUsageAnalytics",
    "UserAPIKeySummary",
    "APIKeyValidationRequest",
    "APIKeyValidationResponse",
    # CRUD
    "crud_api_keys",
    "crud_key_usage",
    "crud_key_permissions",
    # Service
    "APIKeyService",
    # Enums
    "HTTPMethod",
    "KeyPermissionAction",
    "KeyPermissionResource",
    "KeyStatus",
    "KeyType",
]
