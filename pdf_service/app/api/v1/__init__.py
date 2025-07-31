"""
v1 API routes
"""

from fastapi import APIRouter
from app.api.v1.routes.health import health_check_router

v1_router = APIRouter()

v1_router.include_router(health_check_router, prefix='/health')