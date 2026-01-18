"""
Pydantic Schemas

This module exports all Pydantic schemas for the API.
"""

from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    UserWithRolesResponse,
    RoleResponse,
)
from app.schemas.organization import (
    OrganizationBase,
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    OrganizationSettings,
    OrganizationSettingsUpdate,
    OrganizationSettingsResponse,
    ContactInfoSettings,
)
from app.schemas.role import (
    RoleBase,
    RoleCreate,
    RoleUpdate,
    PermissionDetail,
    PermissionCategory,
    UserRoleAssignment,
    UserRoleResponse,
)

__all__ = [
    # User schemas
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserListResponse",
    "UserWithRolesResponse",
    "RoleResponse",
    # Organization schemas
    "OrganizationBase",
    "OrganizationCreate",
    "OrganizationUpdate",
    "OrganizationResponse",
    "OrganizationSettings",
    "OrganizationSettingsUpdate",
    "OrganizationSettingsResponse",
    "ContactInfoSettings",
    # Role schemas
    "RoleBase",
    "RoleCreate",
    "RoleUpdate",
    "PermissionDetail",
    "PermissionCategory",
    "UserRoleAssignment",
    "UserRoleResponse",
]
