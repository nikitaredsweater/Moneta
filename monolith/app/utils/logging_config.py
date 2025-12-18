"""
Logging Configuration and Rules for Moneta Platform API

This module defines the logging standards, formats, and configuration
for the Moneta platform. All logging across the application should
adhere to these rules for consistency and maintainability.

================================================================================
LOGGING LEVELS AND THEIR USAGE
================================================================================

Python's logging module provides five standard levels. Use them as follows:

DEBUG (10) - Detailed diagnostic information
    - Use for: Variable values, execution flow, internal state
    - Examples:
        * Request body contents
        * Query parameters being processed
        * Intermediate calculation results
    - When to use: Development, troubleshooting production issues
    - Production: Usually disabled (set level to INFO or higher)

INFO (20) - Confirmation that things are working as expected
    - Use for: Request start/end, successful operations, routine milestones
    - Examples:
        * "Request started: GET /v1/companies/123"
        * "User authenticated successfully"
        * "Entity created: Company(id=abc-123)"
    - When to use: Always in production
    - Production: Primary operational logging level

WARNING (30) - Something unexpected happened, but the system handled it
    - Use for: Deprecated features, recoverable errors, approaching limits
    - Examples:
        * "Slow query detected: 2.5s for /v1/instruments/search"
        * "Retry attempt 2/3 for external service"
        * "Rate limit 80% reached for user xyz"
    - When to use: Situations that may need attention but aren't failures
    - Production: Always enabled

ERROR (40) - A serious problem that prevented an operation from completing
    - Use for: Failed operations, exceptions caught, business rule violations
    - Examples:
        * "Failed to create company: duplicate registration_number"
        * "Database connection failed"
        * "External service timeout after 30s"
    - When to use: When an operation fails but the application continues
    - Production: Always enabled, should trigger alerts

CRITICAL (50) - A very serious error that may prevent the program from running
    - Use for: System-wide failures, unrecoverable states, security breaches
    - Examples:
        * "Database connection pool exhausted"
        * "Authentication service unavailable"
        * "Data corruption detected"
    - When to use: Rare, only for severe system issues
    - Production: Always enabled, should trigger immediate alerts

================================================================================
LOG MESSAGE FORMAT STANDARD
================================================================================

All log messages should follow this format:

    [COMPONENT] Action description | key1=value1 | key2=value2

Components:
    - REQUEST     : Incoming HTTP requests
    - RESPONSE    : Outgoing HTTP responses
    - AUTH        : Authentication/authorization events
    - DATABASE    : Database operations
    - EXTERNAL    : External service calls
    - BUSINESS    : Business logic events
    - SYSTEM      : System-level events

Examples:
    [REQUEST] Started | method=GET | path=/v1/companies | client_ip=192.168.1.1
    [RESPONSE] Completed | status=200 | duration_ms=45 | path=/v1/companies
    [AUTH] Login successful | user_id=abc-123 | email=user@example.com
    [DATABASE] Query executed | table=companies | operation=SELECT | rows=10
    [ERROR] Operation failed | error=DuplicateKeyError | entity=Company

================================================================================
STRUCTURED LOGGING FIELDS
================================================================================

Standard fields to include in logs:

Request Context:
    - request_id     : Unique identifier for the request (UUID)
    - method         : HTTP method (GET, POST, PUT, DELETE, PATCH)
    - path           : Request path (e.g., /v1/companies)
    - client_ip      : Client IP address
    - user_agent     : Client user agent string

Response Context:
    - status_code    : HTTP status code (200, 400, 500, etc.)
    - duration_ms    : Request processing time in milliseconds
    - response_size  : Response body size in bytes

User Context:
    - user_id        : Authenticated user's ID
    - company_id     : User's company ID (if applicable)

Error Context:
    - error_type     : Exception class name
    - error_message  : Error description
    - stack_trace    : Full stack trace (DEBUG level only)

================================================================================
SENSITIVE DATA HANDLING
================================================================================

NEVER log the following:
    - Passwords or password hashes
    - API keys or tokens (mask with asterisks: "Bearer ***...")
    - Full credit card numbers (show last 4 only: "****1234")
    - Personal identification numbers
    - Private keys or secrets

MASK or TRUNCATE:
    - Email addresses in DEBUG logs (show domain only: "***@example.com")
    - Request bodies containing sensitive fields
    - Response bodies in DEBUG mode

================================================================================
PERFORMANCE THRESHOLDS
================================================================================

Log warnings when exceeding these thresholds:

    - Request duration > 1000ms    : WARNING
    - Request duration > 5000ms    : ERROR
    - Database query > 500ms       : WARNING
    - External API call > 2000ms   : WARNING
    - Response size > 1MB          : WARNING

================================================================================
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# Default format for console output
DEFAULT_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Detailed format for file output
DETAILED_FORMAT = (
    '%(asctime)s | %(levelname)-8s | %(name)s | '
    '%(filename)s:%(lineno)d | %(message)s'
)

# JSON-like format for structured logging
STRUCTURED_FORMAT = (
    '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
    '"logger": "%(name)s", "message": "%(message)s"}'
)

# Performance thresholds in milliseconds
SLOW_REQUEST_THRESHOLD_MS = 1000
VERY_SLOW_REQUEST_THRESHOLD_MS = 5000
SLOW_QUERY_THRESHOLD_MS = 500
SLOW_EXTERNAL_CALL_THRESHOLD_MS = 2000

# Response size threshold in bytes (1MB)
LARGE_RESPONSE_THRESHOLD_BYTES = 1024 * 1024

# Log file settings
DEFAULT_LOG_FILE_PATH = 'logs/moneta.log'
DEFAULT_LOG_FILE_MAX_BYTES = 10 * 1024 * 1024  # 10MB
DEFAULT_LOG_FILE_BACKUP_COUNT = 5

# Valid logging levels mapping
LOG_LEVEL_MAP = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL,
}

# Valid output modes
LOG_OUTPUT_CONSOLE = 'console'
LOG_OUTPUT_FILE = 'file'
LOG_OUTPUT_BOTH = 'both'


def get_log_level_from_env() -> int:
    """
    Get logging level from LOG_LEVEL environment variable.

    Returns:
        int: Logging level (defaults to INFO if not set or invalid)
    """
    level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
    return LOG_LEVEL_MAP.get(level_str, logging.INFO)


def get_log_output_from_env() -> str:
    """
    Get logging output mode from LOG_OUTPUT environment variable.

    Returns:
        str: Output mode ('console', 'file', or 'both')
    """
    output = os.getenv('LOG_OUTPUT', LOG_OUTPUT_CONSOLE).lower()
    if output not in (LOG_OUTPUT_CONSOLE, LOG_OUTPUT_FILE, LOG_OUTPUT_BOTH):
        return LOG_OUTPUT_CONSOLE
    return output


def get_log_file_path_from_env() -> str:
    """
    Get log file path from LOG_FILE_PATH environment variable.

    Returns:
        str: Path to log file (defaults to 'logs/moneta.log')
    """
    return os.getenv('LOG_FILE_PATH', DEFAULT_LOG_FILE_PATH)


def configure_logging(
    level: Optional[int] = None,
    log_format: str = DETAILED_FORMAT,
    output: Optional[str] = None,
    file_path: Optional[str] = None,
) -> None:
    """
    Configure the root logger with settings from environment variables or parameters.

    Environment Variables:
        LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        LOG_OUTPUT: Output destination ('console', 'file', 'both')
        LOG_FILE_PATH: Path to log file (when output includes 'file')

    Args:
        level: Logging level (overrides LOG_LEVEL env var if provided)
        log_format: Format string for log messages
        output: Output destination (overrides LOG_OUTPUT env var if provided)
        file_path: Path to log file (overrides LOG_FILE_PATH env var if provided)
    """
    # Get settings from env vars or use provided parameters
    effective_level = level if level is not None else get_log_level_from_env()
    effective_output = output if output is not None else get_log_output_from_env()
    effective_file_path = file_path if file_path is not None else get_log_file_path_from_env()

    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(effective_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(log_format)

    # Add console handler if needed
    if effective_output in (LOG_OUTPUT_CONSOLE, LOG_OUTPUT_BOTH):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(effective_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Add file handler if needed
    if effective_output in (LOG_OUTPUT_FILE, LOG_OUTPUT_BOTH):
        # Ensure log directory exists
        log_path = Path(effective_file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            effective_file_path,
            maxBytes=DEFAULT_LOG_FILE_MAX_BYTES,
            backupCount=DEFAULT_LOG_FILE_BACKUP_COUNT,
        )
        file_handler.setLevel(effective_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Log the configuration (only if at least one handler exists)
    if root_logger.handlers:
        root_logger.debug(
            '[SYSTEM] Logging configured | level=%s | output=%s | file_path=%s',
            logging.getLevelName(effective_level),
            effective_output,
            effective_file_path if effective_output != LOG_OUTPUT_CONSOLE else 'N/A',
        )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Use this function to create loggers for different components:
        logger = get_logger(__name__)
        logger = get_logger("app.routers.company")

    Args:
        name: Logger name (typically __name__ or component path)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def mask_sensitive_value(value: str, visible_chars: int = 4) -> str:
    """
    Mask a sensitive value, showing only the last few characters.

    Args:
        value: The sensitive value to mask
        visible_chars: Number of characters to show at the end

    Returns:
        Masked string (e.g., "****1234")
    """
    if not value or len(value) <= visible_chars:
        return '***'
    return '*' * (len(value) - visible_chars) + value[-visible_chars:]


def mask_authorization_header(auth_header: Optional[str]) -> str:
    """
    Mask an Authorization header value for safe logging.

    Args:
        auth_header: The Authorization header value

    Returns:
        Masked authorization value (e.g., "Bearer ***...")
    """
    if not auth_header:
        return '[none]'
    if auth_header.startswith('Bearer '):
        return 'Bearer ***...'
    return '***...'
