"""
FastAPI Routers Package.
"""

from app.routers.admin import router as admin_router
from app.routers.artifacts import router as artifacts_router
from app.routers.auth import router as auth_router
from app.routers.certificates import router as certificates_router
from app.routers.disputes import router as disputes_router
from app.routers.health import router as health_router
from app.routers.projects import router as projects_router
from app.routers.verification import router as verification_router

__all__ = [
    "admin_router",
    "artifacts_router",
    "auth_router",
    "certificates_router",
    "disputes_router",
    "health_router",
    "projects_router",
    "verification_router",
]
