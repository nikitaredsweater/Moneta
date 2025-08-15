"""
Routers module
"""

from app.api.v1 import v1_router
from fastapi import APIRouter

# TODO: Add v2 router

app_router = APIRouter()

app_router.include_router(v1_router, prefix='/v1')
