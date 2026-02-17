"""
Main FastAPI application module.
"""

import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from app.routers import app_router
from app.security.middleware import JWTAuthMiddleware
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

ENABLE_GRPC = os.getenv('ENABLE_GRPC', 'false').lower() in ('true', '1', 'yes')


@asynccontextmanager
async def lifespan(
    _app: FastAPI,
) -> AsyncGenerator[None, None]:
    """Manage application lifespan: optionally start/stop gRPC server."""
    if ENABLE_GRPC:
        import grpc  # pylint: disable=import-outside-toplevel
        from app.gen import (  # pylint: disable=import-outside-toplevel
            document_ingest_pb2_grpc as pbg,
        )
        from app.servers.grpc_server import (  # pylint: disable=import-outside-toplevel
            DocumentIngestService,
        )

        grpc_addr = os.getenv('GRPC_ADDR', '[::]:50061')
        grpc_server = grpc.aio.server()
        pbg.add_DocumentIngestServicer_to_server(
            DocumentIngestService(), grpc_server
        )
        grpc_server.add_insecure_port(grpc_addr)
        await grpc_server.start()
        logger.info('[SYSTEM] gRPC server started on %s', grpc_addr)
        try:
            yield
        finally:
            await grpc_server.stop(grace=5)
            logger.info('[SYSTEM] gRPC server stopped')
    else:
        logger.info('[SYSTEM] gRPC server disabled (ENABLE_GRPC not set)')
        yield


# CORS origins from environment variable (comma-separated)
_cors_origins_raw = os.getenv(
    'CORS_ORIGINS',
    'http://localhost:3000,http://127.0.0.1:3000',
)
CORS_ORIGINS = [
    origin.strip() for origin in _cors_origins_raw.split(',') if origin.strip()
]

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
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,  # set True only if you use cookies
    allow_methods=['*'],  # or list methods you use
    allow_headers=['*', 'Authorization', 'Content-Type'],
)
app.include_router(app_router)

logger.info('[SYSTEM] Application initialized successfully')
