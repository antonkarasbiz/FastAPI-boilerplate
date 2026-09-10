"""API Key management enums."""

from enum import StrEnum


class KeyStatus(StrEnum):
    """API key status enumeration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    REVOKED = "revoked"


class KeyPermissionResource(StrEnum):
    """API key permission resources."""

    CONVERSATIONS = "conversations"
    CREDITS = "credits"
    AI_USAGE = "ai_usage"
    USER_PROFILE = "user_profile"
    ANALYTICS = "analytics"
    ADMIN = "admin"
    BILLING = "billing"
    API_KEYS = "api_keys"
    WILDCARD = "*"


class KeyPermissionAction(StrEnum):
    """API key permission actions."""

    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    CREATE = "create"
    UPDATE = "update"
    LIST = "list"
    ADMIN = "admin"
    WILDCARD = "*"


class KeyType(StrEnum):
    """API key type enumeration.

    Types:
        PUBLIC: Limited read-only access
        PRIVATE: Full access for user's data
        ADMIN: Administrative access
        SERVICE: Service-to-service communication
        WEBHOOK: Webhook authentication
    """

    PUBLIC = "public"
    PRIVATE = "private"
    ADMIN = "admin"
    SERVICE = "service"
    WEBHOOK = "webhook"


class HTTPMethod(StrEnum):
    """HTTP method enumeration for API key usage tracking."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"
