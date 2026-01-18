"""
Users API Endpoints

Endpoints for user management and listing.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.user import UserListResponse
from app.services.user_service import UserService
from app.services.organization_service import OrganizationService
# NOTE: Authentication is not yet implemented, so these endpoints are currently open
# from app.api.dependencies import get_current_active_user, get_user_organization
# from app.models.user import User, Organization


router = APIRouter()


@router.get("/", response_model=List[UserListResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    # Uncomment when authentication is implemented:
    # current_user: User = Depends(get_current_active_user),
    # organization: Organization = Depends(get_user_organization),
):
    """
    List all members in the organization

    Contact information (email, phone, mobile) will be included only if:
    1. The organization has enabled contact info visibility in settings
    2. The specific fields (email, phone, mobile) are enabled

    A privacy notice should be displayed when contact information is shown,
    stating that it is for department purposes only and should not be used
    for commercial purposes.

    **Authentication required** (currently not implemented)
    """
    # TODO: Remove this once authentication is implemented
    # For now, we'll use a hardcoded organization ID for testing
    # In production, this would come from the authenticated user
    from uuid import UUID
    test_org_id = UUID("00000000-0000-0000-0000-000000000001")

    user_service = UserService(db)
    org_service = OrganizationService(db)

    # Get organization settings
    settings = await org_service.get_organization_settings(test_org_id)

    # Check if contact info visibility is enabled
    include_contact_info = settings.contact_info_visibility.enabled

    # Get users with conditional contact info
    users = await user_service.get_users_for_organization(
        organization_id=test_org_id,
        include_contact_info=include_contact_info,
        contact_settings={
            "contact_info_visibility": {
                "show_email": settings.contact_info_visibility.show_email,
                "show_phone": settings.contact_info_visibility.show_phone,
                "show_mobile": settings.contact_info_visibility.show_mobile,
            }
        }
    )

    return users


@router.get("/contact-info-enabled")
async def check_contact_info_enabled(
    db: AsyncSession = Depends(get_db),
    # Uncomment when authentication is implemented:
    # organization: Organization = Depends(get_user_organization),
):
    """
    Check if contact information display is enabled for the organization

    This endpoint can be used by the frontend to determine whether to show
    the privacy notice and contact information fields.

    **Authentication required** (currently not implemented)
    """
    # TODO: Remove this once authentication is implemented
    from uuid import UUID
    test_org_id = UUID("00000000-0000-0000-0000-000000000001")

    org_service = OrganizationService(db)
    settings = await org_service.get_organization_settings(test_org_id)

    return {
        "enabled": settings.contact_info_visibility.enabled,
        "show_email": settings.contact_info_visibility.show_email,
        "show_phone": settings.contact_info_visibility.show_phone,
        "show_mobile": settings.contact_info_visibility.show_mobile,
    }
