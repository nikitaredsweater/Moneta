"""
Main FastAPI application module.
"""

from app.routers import app_router
from app.security.middleware import JWTAuthMiddleware
from fastapi import FastAPI

app = FastAPI(
    title='Platform API',
    description='Platform API',
)

app.add_middleware(JWTAuthMiddleware)

app.include_router(app_router)
