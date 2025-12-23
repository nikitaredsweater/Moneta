"""
Decorator, registry, auto-discovery, and dispatch.
- @handles(...) decorator to auto-register handlers
- wildcard support (e.g., 's3:ObjectCreated:*')
- dispatcher
- optional auto-stubs for all known MinIO events (so nothing is unhandled)

Usage:
    from app.handlers.minio.registry import dispatch_event, handles, MinIOEvent, generate_stub_handlers

    # Define specific handlers anywhere (or import before generate_stub_handlers())
    @handles('s3:ObjectCreated:Put')
    async def on_put(evt: MinIOEvent, raw: dict) -> None:
        ...

    # Optionally register stubs for everything else:
    generate_stub_handlers()

    # In your consumer:
    parsed = MinIOEvent(event_name=..., bucket_name=..., object_key=..., ...)
    await dispatch_event(parsed, raw_event_dict)
"""

from __future__ import annotations

import fnmatch
import importlib
import logging
import pkgutil
from typing import Awaitable, Callable, Dict, List, Optional, Tuple

from app.utils.minio_event_parsing import MinIOEvent

logger = logging.getLogger(__name__)

################################################################################
#                       List of supported MinIO events
################################################################################
OBJECT_CREATED = [
    's3:ObjectCreated:CompleteMultipartUpload',
    's3:ObjectCreated:Copy',
    's3:ObjectCreated:DeleteTagging',
    's3:ObjectCreated:Post',
    's3:ObjectCreated:Put',
    's3:ObjectCreated:PutLegalHold',
    's3:ObjectCreated:PutRetention',
    's3:ObjectCreated:PutTagging',
]

OBJECT_ACCESSED = [
    's3:ObjectAccessed:Head',
    's3:ObjectAccessed:Get',
    's3:ObjectAccessed:GetRetention',
    's3:ObjectAccessed:GetLegalHold',
]

OBJECT_REMOVED = [
    's3:ObjectRemoved:Delete',
    's3:ObjectRemoved:DeleteMarkerCreated',
]

REPLICATION = [
    's3:Replication:OperationCompletedReplication',
    's3:Replication:OperationFailedReplication',
    's3:Replication:OperationMissedThreshold',
    's3:Replication:OperationNotTracked',
    's3:Replication:OperationReplicatedAfterThreshold',
]

ILM = [
    's3:ObjectTransition:Failed',
    's3:ObjectTransition:Complete',
    's3:ObjectRestore:Post',
    's3:ObjectRestore:Completed',
]

SCANNER = [
    's3:Scanner:ManyVersions',
    's3:Scanner:BigPrefix',
]

ALL_MINIO_EVENT_NAMES: List[str] = (
    OBJECT_CREATED
    + OBJECT_ACCESSED
    + OBJECT_REMOVED
    + REPLICATION
    + ILM
    + SCANNER
)

################################################################################
#                       Registry + decorator + dispatcher
################################################################################

Handler = Callable[[MinIOEvent, dict], Awaitable[None]]

_exact: Dict[str, Handler] = {}
_patterns: List[Tuple[str, Handler]] = []
_default_handler: Optional[Handler] = None


def handles(*event_names_or_patterns: str) -> Callable[[Handler], Handler]:
    """
    Decorator to register a handler for one or more event names or wildcard patterns.

    Examples:
        @handles('s3:ObjectCreated:Put')
        async def on_put(evt, raw): ...

        @handles('s3:ObjectCreated:*', 's3:ObjectRemoved:*')
        async def on_create_or_remove(evt, raw): ...
    """

    def decorator(fn: Handler) -> Handler:
        for name in event_names_or_patterns:
            if any(ch in name for ch in '*?[]'):  # wildcard pattern
                _patterns.append((name, fn))
            else:
                _exact[name] = fn
        return fn

    return decorator


def set_default_handler(fn: Handler) -> None:
    """
    Set a fallback handler used when no exact/pattern handler matches.
    """
    global _default_handler
    _default_handler = fn


def best_handler_for(event_name: Optional[str]) -> Optional[Handler]:
    """
    Returns the most specific handler:
      1) exact match
      2) first wildcard match (registration order)
      3) None
    """
    if not event_name:
        return None
    if event_name in _exact:
        return _exact[event_name]
    for pattern, fn in _patterns:
        if fnmatch.fnmatchcase(event_name, pattern):
            return fn
    return None


async def dispatch_event(parsed_event: MinIOEvent, raw_event: dict) -> None:
    """
    Dispatch a parsed MinIOEvent to the appropriate handler.
    """
    fn = best_handler_for(parsed_event.event_name) or _default_handler
    if fn is None:
        logger.warning(
            '[BUSINESS] No handler for MinIO event | event_name=%s | bucket=%s | object_key=%s',
            parsed_event.event_name,
            parsed_event.bucket_name,
            parsed_event.object_key,
        )
        return

    logger.debug(
        '[BUSINESS] Dispatching MinIO event | event_name=%s | bucket=%s | object_key=%s | handler=%s',
        parsed_event.event_name,
        parsed_event.bucket_name,
        parsed_event.object_key,
        fn.__name__,
    )

    try:
        await fn(parsed_event, raw_event)
        logger.info(
            '[BUSINESS] MinIO event handled | event_name=%s | bucket=%s | object_key=%s',
            parsed_event.event_name,
            parsed_event.bucket_name,
            parsed_event.object_key,
        )
    except Exception as e:
        logger.error(
            '[BUSINESS] MinIO event handler failed | event_name=%s | bucket=%s | object_key=%s | error_type=%s | error=%s',
            parsed_event.event_name,
            parsed_event.bucket_name,
            parsed_event.object_key,
            type(e).__name__,
            str(e),
        )
        raise


def autoload_handlers(package: str) -> None:
    """
    Import all submodules in `package` so their @handles decorators run and register.

    Example:
        autoload_handlers('app.handlers.minio')
    """
    pkg = importlib.import_module(package)
    if not hasattr(pkg, '__path__'):
        return  # single module already imported
    for modinfo in pkgutil.iter_modules(pkg.__path__):
        importlib.import_module(f'{package}.{modinfo.name}')


def generate_stub_handlers(log_level: int = logging.DEBUG) -> None:
    """
    Auto-register no-op stub handlers for every known MinIO event name
    that doesn't already have a specific or wildcard handler.

    - Helpful during bootstrap: you get visibility for every event
      without writing tons of boilerplate.
    - You can later add real handlers with @handles('...'), which
      will override the stub because exact handlers are checked first.
    """
    for name in ALL_MINIO_EVENT_NAMES:
        if name in _exact:
            continue
        # If a wildcard already covers it, you may skip creating a stub:
        if best_handler_for(name) is not None:
            continue

        async def _stub(evt: MinIOEvent, raw: dict, *, _n=name) -> None:
            logger.log(
                log_level,
                'Stub handler: %s key=%s bucket=%s',
                _n,
                evt.object_key,
                evt.bucket_name,
            )

        _exact[name] = _stub  # register exact stub
