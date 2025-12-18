"""
Request/Response Logging Middleware

This middleware provides comprehensive logging for all HTTP requests and responses.
It logs at different levels based on the operation status and performance metrics.

Logging Levels Used:
    - DEBUG: Request/response body details, headers
    - INFO: Request start/end, successful responses
    - WARNING: Slow requests, large responses
    - ERROR: Failed requests (4xx client errors logged as warnings, 5xx as errors)
    - CRITICAL: Used for system-level failures (handled elsewhere)

See app/utils/logging_config.py for full logging rules and standards.
"""

import json
import logging
import time
import uuid
from typing import Callable, Optional

from app.utils.logging_config import (
    LARGE_RESPONSE_THRESHOLD_BYTES,
    SLOW_REQUEST_THRESHOLD_MS,
    VERY_SLOW_REQUEST_THRESHOLD_MS,
    mask_authorization_header,
)
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

logger = logging.getLogger('app.middleware.request_logging')

# Paths to exclude from detailed logging (health checks, docs, etc.)
EXCLUDED_PATHS = {'/health', '/healthz', '/ready', '/openapi.json', '/docs', '/redoc'}

# Maximum body size to log (to prevent logging huge payloads)
MAX_BODY_LOG_SIZE = 10000  # 10KB


def _get_client_ip(request: Request) -> str:
    """Extract client IP from request, considering proxy headers."""
    forwarded = request.headers.get('x-forwarded-for')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.client.host if request.client else 'unknown'


def _truncate_body(body: str, max_size: int = MAX_BODY_LOG_SIZE) -> str:
    """Truncate body if it exceeds max size."""
    if len(body) > max_size:
        return body[:max_size] + f'... [truncated, total {len(body)} chars]'
    return body


def _sanitize_headers(headers: dict) -> dict:
    """Sanitize headers for logging, masking sensitive values."""
    sanitized = {}
    sensitive_headers = {'authorization', 'x-api-key', 'cookie', 'set-cookie'}

    for key, value in headers.items():
        lower_key = key.lower()
        if lower_key in sensitive_headers:
            if lower_key == 'authorization':
                sanitized[key] = mask_authorization_header(value)
            else:
                sanitized[key] = '***'
        else:
            sanitized[key] = value

    return sanitized


def _get_status_log_level(status_code: int) -> int:
    """Determine appropriate log level based on status code."""
    if status_code >= 500:
        return logging.ERROR
    if status_code >= 400:
        return logging.WARNING
    return logging.INFO


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for comprehensive request/response logging.

    Features:
        - Logs request start with method, path, and client info
        - Logs request completion with status code and duration
        - Logs request/response bodies at DEBUG level
        - Warns on slow requests and large responses
        - Generates unique request IDs for tracing
        - Sanitizes sensitive data in logs
    """

    def __init__(self, app: ASGIApp, exclude_paths: Optional[set] = None):
        """
        Initialize the logging middleware.

        Args:
            app: The ASGI application
            exclude_paths: Set of paths to exclude from logging
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or EXCLUDED_PATHS

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Process and log each request/response cycle.

        Args:
            request: The incoming HTTP request
            call_next: The next middleware or endpoint handler

        Returns:
            The HTTP response
        """
        # Skip logging for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Generate unique request ID for tracing
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        # Extract request metadata
        method = request.method
        path = request.url.path
        query_params = str(request.query_params) if request.query_params else ''
        client_ip = _get_client_ip(request)
        user_agent = request.headers.get('user-agent', 'unknown')

        # Log request start at INFO level
        logger.info(
            '[REQUEST] Started | request_id=%s | method=%s | path=%s | '
            'query=%s | client_ip=%s',
            request_id,
            method,
            path,
            query_params or '[none]',
            client_ip,
        )

        # Log headers at DEBUG level
        if logger.isEnabledFor(logging.DEBUG):
            sanitized_headers = _sanitize_headers(dict(request.headers))
            logger.debug(
                '[REQUEST] Headers | request_id=%s | headers=%s',
                request_id,
                json.dumps(sanitized_headers),
            )

        # Log request body at DEBUG level (for POST, PUT, PATCH)
        request_body = None
        if method in {'POST', 'PUT', 'PATCH'} and logger.isEnabledFor(logging.DEBUG):
            try:
                body_bytes = await request.body()
                if body_bytes:
                    request_body = body_bytes.decode('utf-8', errors='replace')
                    logger.debug(
                        '[REQUEST] Body | request_id=%s | body=%s',
                        request_id,
                        _truncate_body(request_body),
                    )
            except Exception as e:
                logger.debug(
                    '[REQUEST] Body read failed | request_id=%s | error=%s',
                    request_id,
                    str(e),
                )

        # Process request and measure duration
        start_time = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception as e:
            # Log unhandled exceptions at CRITICAL level
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.critical(
                '[RESPONSE] Unhandled exception | request_id=%s | method=%s | '
                'path=%s | duration_ms=%.2f | error_type=%s | error=%s',
                request_id,
                method,
                path,
                duration_ms,
                type(e).__name__,
                str(e),
            )
            raise

        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000
        status_code = response.status_code

        # Determine response size if available
        response_size = response.headers.get('content-length', 'unknown')

        # Determine log level based on status code
        log_level = _get_status_log_level(status_code)

        # Check for performance warnings
        if duration_ms > VERY_SLOW_REQUEST_THRESHOLD_MS:
            logger.error(
                '[RESPONSE] Very slow request | request_id=%s | method=%s | '
                'path=%s | duration_ms=%.2f | threshold_ms=%d',
                request_id,
                method,
                path,
                duration_ms,
                VERY_SLOW_REQUEST_THRESHOLD_MS,
            )
        elif duration_ms > SLOW_REQUEST_THRESHOLD_MS:
            logger.warning(
                '[RESPONSE] Slow request | request_id=%s | method=%s | '
                'path=%s | duration_ms=%.2f | threshold_ms=%d',
                request_id,
                method,
                path,
                duration_ms,
                SLOW_REQUEST_THRESHOLD_MS,
            )

        # Check for large response warning
        if response_size != 'unknown':
            try:
                size_bytes = int(response_size)
                if size_bytes > LARGE_RESPONSE_THRESHOLD_BYTES:
                    logger.warning(
                        '[RESPONSE] Large response | request_id=%s | path=%s | '
                        'size_bytes=%d | threshold_bytes=%d',
                        request_id,
                        path,
                        size_bytes,
                        LARGE_RESPONSE_THRESHOLD_BYTES,
                    )
            except ValueError:
                pass

        # Log response completion
        logger.log(
            log_level,
            '[RESPONSE] Completed | request_id=%s | method=%s | path=%s | '
            'status=%d | duration_ms=%.2f | size=%s',
            request_id,
            method,
            path,
            status_code,
            duration_ms,
            response_size,
        )

        # Log response headers at DEBUG level
        if logger.isEnabledFor(logging.DEBUG):
            sanitized_resp_headers = _sanitize_headers(dict(response.headers))
            logger.debug(
                '[RESPONSE] Headers | request_id=%s | headers=%s',
                request_id,
                json.dumps(sanitized_resp_headers),
            )

        # Add request ID to response headers for client-side tracing
        response.headers['X-Request-ID'] = request_id

        return response
