"""
Microservice-wide FastAPI dependecies
"""

from typing import Generator

from clients.minio_client import minio_client
from minio import Minio


def get_minio_client() -> Generator[Minio, None, None]:
    """
    FastAPI-compatible dependency that returns the shared MinIO client.
    """
    yield minio_client
