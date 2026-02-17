"""
Clients package
"""

from app.clients.minio_client import minio_client
from app.clients.monolith_grpc_client import MonolithGrpcClient
from app.clients.pika_client import PikaClient

__all__ = ['minio_client', 'PikaClient', 'MonolithGrpcClient']
