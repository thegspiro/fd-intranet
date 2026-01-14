"""
API Router v1

Combines all API route modules into a single router.
"""

from fastapi import APIRouter

# Import route modules (will be created)
# from app.api.v1.endpoints import auth, users, audit

api_router = APIRouter()

# Include route modules
# api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
# api_router.include_router(users.router, prefix="/users", tags=["users"])
# api_router.include_router(audit.router, prefix="/audit", tags=["audit"])

# Placeholder routes
@api_router.get("/")
async def api_root():
    """API v1 root endpoint"""
    return {
        "message": "The Logbook API v1",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
        }
    }
