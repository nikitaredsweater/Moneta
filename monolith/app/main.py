"""
Main FastAPI application module.
"""

from fastapi import FastAPI

from app.routers import app_router
from app.security.middleware import JWTAuthMiddleware

app = FastAPI(
    title='Platform API',
    description='Platform API',
)

app.add_middleware(JWTAuthMiddleware)

app.include_router(app_router)
