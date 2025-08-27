"""
Main FastAPI application module.
"""

import os
from contextlib import asynccontextmanager

import grpc
from app.gen import document_ingest_pb2_grpc as pbg
from app.routers import app_router
from app.security.middleware import JWTAuthMiddleware
from app.servers.grpc_server import DocumentIngestService
from fastapi import FastAPI

GRPC_ADDR = os.getenv('GRPC_ADDR', '[::]:50061')  # gRPC port


@asynccontextmanager
async def lifespan(app: FastAPI):
    global grpc_server
    # Create and start gRPC server
    grpc_server = grpc.aio.server()
    pbg.add_DocumentIngestServicer_to_server(
        DocumentIngestService(), grpc_server
    )
    grpc_server.add_insecure_port(
        '[::]:50061'
    )  # swap for secure_channel creds if using TLS
    await grpc_server.start()
    try:
        yield  # <-- HTTP (FastAPI) runs while gRPC is running
    finally:
        # Graceful shutdown
        if grpc_server:
            await grpc_server.stop(grace=5)


app = FastAPI(
    title='Platform API', description='Platform API', lifespan=lifespan
)

app.add_middleware(JWTAuthMiddleware)
app.include_router(app_router)
