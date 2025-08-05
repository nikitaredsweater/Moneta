"""
v1 API routes
"""

from app.api.v1.routes.document import document_router
from app.api.v1.routes.health import health_check_router
from fastapi import APIRouter

v1_router = APIRouter()

v1_router.include_router(health_check_router, prefix='/health')
v1_router.include_router(document_router, prefix='/document')
