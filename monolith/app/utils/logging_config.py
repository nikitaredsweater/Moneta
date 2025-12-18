"""
Logging Configuration for Moneta Platform API.

DEPRECATED: This module is now a compatibility shim.
Use the moneta_logging package directly for new code:

    from moneta_logging import configure_logging, get_logger
    from moneta_logging.middleware import RequestLoggingMiddleware

See docs/logging.md for logging rules and standards.
"""

# Re-export everything from moneta_logging for backward compatibility
from moneta_logging import (
    # Configuration functions
    configure_logging,
    get_logger,
    get_log_level_from_env,
    get_log_output_from_env,
    get_log_file_path_from_env,
    # Masking utilities
    mask_sensitive_value,
    mask_authorization_header,
    # Format strings
    DEFAULT_FORMAT,
    DETAILED_FORMAT,
    STRUCTURED_FORMAT,
    # Threshold constants
    SLOW_REQUEST_THRESHOLD_MS,
    VERY_SLOW_REQUEST_THRESHOLD_MS,
    SLOW_QUERY_THRESHOLD_MS,
    SLOW_EXTERNAL_CALL_THRESHOLD_MS,
    LARGE_RESPONSE_THRESHOLD_BYTES,
    # Output mode constants
    LOG_OUTPUT_CONSOLE,
    LOG_OUTPUT_FILE,
    LOG_OUTPUT_BOTH,
)

__all__ = [
    'configure_logging',
    'get_logger',
    'get_log_level_from_env',
    'get_log_output_from_env',
    'get_log_file_path_from_env',
    'mask_sensitive_value',
    'mask_authorization_header',
    'DEFAULT_FORMAT',
    'DETAILED_FORMAT',
    'STRUCTURED_FORMAT',
    'SLOW_REQUEST_THRESHOLD_MS',
    'VERY_SLOW_REQUEST_THRESHOLD_MS',
    'SLOW_QUERY_THRESHOLD_MS',
    'SLOW_EXTERNAL_CALL_THRESHOLD_MS',
    'LARGE_RESPONSE_THRESHOLD_BYTES',
    'LOG_OUTPUT_CONSOLE',
    'LOG_OUTPUT_FILE',
    'LOG_OUTPUT_BOTH',
]
