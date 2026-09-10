"""SQLAdmin model views for the admin interface."""

from sqladmin import Admin

from .tiers import TierAdmin
from .users import UserAdmin

__all__ = [
    "UserAdmin",
    "TierAdmin",
    "register_admin_views",
]


def register_admin_views(admin: Admin) -> None:
    """Register all model views with the admin interface."""
    admin.add_view(UserAdmin)
    admin.add_view(TierAdmin)
