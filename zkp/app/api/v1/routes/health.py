from fastapi import APIRouter, HTTPException
from typing import Any, Dict

import time
import app.schemas as schemas

health_check_router = APIRouter()


@health_check_router.get("/health", response_model=schemas.HealthResponse)
async def health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "$SERVICE_NAME",
        "version": "1.0.0"
    }
