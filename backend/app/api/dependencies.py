"""
API Dependencies

FastAPI dependencies for authentication, authorization, and database access.
"""

from typing import Optional, List
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.core.database import get_db
from app.models.user import User, Organization, Role


class PermissionChecker:
    """
    Dependency class for checking user permissions

    Usage:
        @app.get("/admin")
        async def admin_route(
            current_user: User = Depends(require_permission("admin.access"))
        ):
            ...
    """

    def __init__(self, required_permissions: List[str]):
        self.required_permissions = required_permissions

    async def __call__(
        self,
        current_user: User = Depends(lambda: get_current_user()),
    ) -> User:
        """Check if user has required permissions"""
        # Get user's permissions from all their roles
        user_permissions = []
        for role in current_user.roles:
            user_permissions.extend(role.permissions or [])

        # Check if user has any of the required permissions
        for perm in self.required_permissions:
            if perm in user_permissions:
                return current_user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )


def require_permission(*permissions: str):
    """
    Create a permission checker dependency

    Usage:
        @app.get("/settings")
        async def update_settings(
            user: User = Depends(require_permission("settings.edit"))
        ):
            ...
    """
    return PermissionChecker(list(permissions))


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get the current authenticated user from the request

    In a real implementation, this would:
    1. Extract the JWT token from the Authorization header
    2. Verify the token signature
    3. Extract the user ID from the token
    4. Load the user from the database

    For now, this is a placeholder that assumes authentication is handled elsewhere.
    """
    # TODO: Implement JWT token verification
    # This is a placeholder implementation
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Placeholder: In production, decode JWT and get user_id
    # For now, we'll just raise an exception
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Authentication not yet implemented. This endpoint requires authentication."
    )


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user (not deleted, not suspended)"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    return current_user


async def get_user_organization(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Organization:
    """Get the organization for the current user"""
    result = await db.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    organization = result.scalar_one_or_none()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    return organization


# Convenience function for checking secretary role
def require_secretary():
    """Require user to have secretary permissions"""
    return require_permission(
        "settings.manage_contact_visibility",
        "organization.edit_settings"
    )
