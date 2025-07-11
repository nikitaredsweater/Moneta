"""
Routers module
"""

from fastapi import APIRouter

from app.routers.v1.api import v1_router

# TODO: Add v2 router
# TODO: Add health router

app_router = APIRouter()

app_router.include_router(v1_router, prefix='/v1')
