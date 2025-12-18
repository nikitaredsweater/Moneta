"""
Bundling module that will set the auto stub creation and handler registry, as
well as providing a method that needs to be called to access the handler loop.
"""

import logging

from app.handlers.minio.registry import (
    autoload_handlers,
    dispatch_event,
    generate_stub_handlers,
)
from app.utils.minio_event_parsing import parse_minio_event

logger = logging.getLogger(__name__)

autoload_handlers('app.handlers.minio.event_handlers')
# auto-create stubs for any events not yet covered (exact or wildcard)
generate_stub_handlers(logging.INFO)

logger.info('[SYSTEM] MinIO event handlers loaded')


async def on_minio_message(raw_event: dict) -> None:
    """
    Main entry point for processing MinIO events from RabbitMQ.

    Parses the raw event and dispatches it to the appropriate handler.
    """
    logger.debug('[BUSINESS] Processing MinIO message')

    try:
        parsed = parse_minio_event(raw_event)
        logger.debug(
            '[BUSINESS] MinIO event parsed | event_name=%s | bucket=%s | object_key=%s',
            parsed.event_name,
            parsed.bucket_name,
            parsed.object_key,
        )
        await dispatch_event(parsed, raw_event)
    except Exception as e:
        logger.error(
            '[BUSINESS] Failed to process MinIO message | error_type=%s | error=%s',
            type(e).__name__,
            str(e),
        )
        raise


__all__ = ['on_minio_message']
