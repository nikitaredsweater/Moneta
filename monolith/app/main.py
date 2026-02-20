"""
Main FastAPI application module.
"""

import logging
import os
from contextlib import asynccontextmanager

import grpc
from app.gen import document_ingest_pb2_grpc as pbg
from app.routers import app_router
from app.security.middleware import JWTAuthMiddleware
from app.servers.grpc_server import DocumentIngestService
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from moneta_auth import jwt_keys
from moneta_logging import configure_logging
from moneta_logging.middleware import RequestLoggingMiddleware

# Configure logging from environment variables (LOG_LEVEL, LOG_OUTPUT, LOG_FILE_PATH)
# See moneta_logging package or docs/logging.md for logging rules and standards
configure_logging()

logger = logging.getLogger(__name__)
logger.info('[SYSTEM] Application starting')

# Load JWT keys for token signing and verification
# The monolith needs both keys: private for signing, public for verification
# This is REQUIRED - fail fast if keys aren't available
try:
    jwt_keys.load_keys()
    logger.info('[SYSTEM] JWT keys loaded successfully')
except Exception as e:
    logger.error(
        '[SYSTEM] FATAL: JWT keys failed to load. '
        'Ensure JWT_PRIVATE_KEY_PATH and JWT_PUBLIC_KEY_PATH environment variables '
        'are set and point to valid PEM key files. Error: %s',
        e,
    )
    raise RuntimeError(f'JWT keys required but failed to load: {e}') from e

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

# Middleware order matters: they execute in reverse order of addition
# 1. RequestLoggingMiddleware (added last, executes first)
# 2. JWTAuthMiddleware
# 3. CORSMiddleware (added first, executes last for responses)
app.add_middleware(JWTAuthMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        'http://localhost:3000',
        'http://127.0.0.1:3000',
        'http://100.64.0.8:29978',
    ],
    allow_credentials=False,  # set True only if you use cookies
    allow_methods=['*'],  # or list methods you use
    allow_headers=['*', 'Authorization', 'Content-Type'],
)
app.include_router(app_router)

logger.info('[SYSTEM] Application initialized successfully')
