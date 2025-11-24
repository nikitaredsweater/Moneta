"""
v1 API routes
"""

from app.api.v1.routes.health import health_check_router
from app.api.v1.routes.onchain import router as onchain_router
from fastapi import APIRouter

v1_router = APIRouter()

v1_router.include_router(health_check_router, prefix='/health')
v1_router.include_router(onchain_router)
