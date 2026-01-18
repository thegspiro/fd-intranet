"""
API Router v1

Combines all API route modules into a single router.
"""

from fastapi import APIRouter

# Import route modules
from app.api.v1.endpoints import users, organizations

api_router = APIRouter()

# Include route modules
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(organizations.router, prefix="/organization", tags=["organization"])

# Placeholder routes
@api_router.get("/")
async def api_root():
    """API v1 root endpoint"""
    return {
        "message": "The Logbook API v1",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "users": "/api/v1/users",
            "organization_settings": "/api/v1/organization/settings",
        }
    }
