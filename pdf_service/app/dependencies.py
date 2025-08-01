"""
Microservice-wide FastAPI dependecies
"""

from typing import Generator

from minio import Minio
from utils.minio_client import minio_client


def get_minio_client() -> Generator[Minio, None, None]:
    """
    FastAPI-compatible dependency that returns the shared MinIO client.
    """
    yield minio_client
