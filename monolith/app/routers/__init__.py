"""
Routers module
"""

from app.routers.v1.api import v1_router
from fastapi import APIRouter
from fastapi.responses import JSONResponse

# TODO: Add v2 router

app_router = APIRouter()

app_router.include_router(v1_router, prefix='/v1')


@app_router.get('/health')
async def health_check() -> JSONResponse:
    """
    Health check endpoint for Railway and load balancers.

    Returns:
        JSONResponse: A JSON response with status 'ok'.
    """
    return JSONResponse(content={'status': 'ok'}, status_code=200)
