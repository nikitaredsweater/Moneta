"""
Main FastAPI application module.
"""

from fastapi import FastAPI

from app.routers import app_router

app = FastAPI(
    title='Platform API',
    description='Platform API',
)

app.include_router(app_router)
