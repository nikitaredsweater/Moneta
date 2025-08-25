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

logger = logging.getLogger()

autoload_handlers('app.handlers.minio.event_handlers')
# auto-create stubs for any events not yet covered (exact or wildcard)
generate_stub_handlers(logging.INFO)


async def on_minio_message(raw_event: dict) -> None:
    """
    Main loop that will call the specific handler for the event
    """
    parsed = parse_minio_event(raw_event)
    await dispatch_event(parsed, raw_event)


__all__ = ['on_minio_message']
