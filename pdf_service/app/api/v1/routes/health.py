"""
Health check route
"""

from fastapi import APIRouter


health_check_router = APIRouter()

@health_check_router.get("/")
async def health_check():
    return {"status": "healthy"}