"""
Health-related schemas
"""

from app.schemas.base import CamelModel


class HealthResponse(CamelModel):
    """Health check response model"""

    status: str
    timestamp: float
    service: str
    version: str
