"""
gRPC client for the monolith's DocumentIngest service.

This module exposes an async-friendly client (`MonolithGrpcClient`) plus a few
synchronous helper functions for occasional script/CLI usage. It wraps the
generated gRPC stubs and handles common concerns:

- Channel lifecycle (secure or insecure)
- Per-RPC deadlines
- Attaching request metadata (e.g., auth headers)
- Converting `datetime` to `google.protobuf.Timestamp`

Environment:
    MONOLITH_GRPC_TARGET: if unset, defaults to 'app:50061'

TLS:
    Provide `tls_root_cert` to enable TLS (secure channel); otherwise an
    insecure channel is used.

Typical async usage:
    async with MonolithGrpcClient(metadata=[('authorization', 'Bearer <token>')]) as client:
        resp = await client.save_document(
            internal_filename='file-123.pdf',
            mime='application/pdf',
            storage_bucket='documents',
            storage_object_key='user_docs/u-123/file-123.pdf',
            created_by='70b30fbc-3856-4f2f-89cd-c1c5688ca7c9',
        )
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Dict, Iterable, Optional, Tuple

# Generated modules (re-run your protoc script after changing the .proto)
import app.gen.document_ingest_pb2 as pb
import app.gen.document_ingest_pb2_grpc as pbg
import grpc
from google.protobuf.timestamp_pb2 import Timestamp
from grpc import aio

logger = logging.getLogger(__name__)


class MonolithGrpcClient:
    """
    Thin, reusable client wrapper for the DocumentIngest gRPC service.

    Manages an `grpc.aio.Channel` and a `DocumentIngestStub`, and provides
    typed async helpers for CreateDocument, CreateDocumentVersion, and
    GetDocument RPCs.

    Example:
        async with MonolithGrpcClient(
            metadata=[('authorization', 'Bearer <token>')],
            timeout_sec=3.0,
        ) as client:
            resp = await client.get_document(internal_filename='file-123.pdf')
            if resp.status == pb.GetDocumentResponse.FOUND:
                ...

    Notes:
        - All per-RPC deadlines default to `timeout_sec` unless overridden.
        - If you need TLS, pass `tls_root_cert` (PEM bytes) to the constructor.
    """

    def __init__(
        self,
        target: Optional[str] = None,
        timeout_sec: float = 3.0,
        metadata: Optional[Iterable[Tuple[str, str]]] = None,
        tls_root_cert: Optional[bytes] = None,
    ) -> None:
        """
        Initialize a client with channel configuration.

        Args:
            target (str | None): host:port of the gRPC server.
                Defaults to env `MONOLITH_GRPC_TARGET` or 'app:50061'.
            timeout_sec (float): Default per-RPC deadline (in seconds).
            metadata (Iterable[tuple[str, str]] | None): Static metadata to attach
                to each RPC (e.g., authorization).
            tls_root_cert (bytes | None): If provided, uses a secure channel with
                these root certificates; otherwise an insecure channel is used.

        Returns:
            None
        """
        self.target = target or os.getenv('MONOLITH_GRPC_TARGET', 'app:50061')
        self.timeout_sec = timeout_sec
        self.metadata = list(metadata or [])
        self._channel: Optional[aio.Channel] = None
        self._stub: Optional[pbg.DocumentIngestStub] = None
        self._tls_root_cert = tls_root_cert

    async def start(self) -> None:
        """
        Create and open the underlying channel and stub.

        Returns:
            None
        """
        if self._channel:
            logger.debug('[EXTERNAL] gRPC channel already open | target=%s', self.target)
            return

        logger.debug('[EXTERNAL] Opening gRPC channel | target=%s | tls=%s', self.target, bool(self._tls_root_cert))
        if self._tls_root_cert:
            creds = grpc.ssl_channel_credentials(
                root_certificates=self._tls_root_cert
            )
            self._channel = aio.secure_channel(self.target, creds)
        else:
            self._channel = aio.insecure_channel(self.target)
        self._stub = pbg.DocumentIngestStub(self._channel)
        logger.info('[EXTERNAL] gRPC channel opened | target=%s', self.target)

    async def close(self) -> None:
        """
        Close the underlying channel (if open) and clear the stub.

        Returns:
            None
        """
        if self._channel:
            logger.debug('[EXTERNAL] Closing gRPC channel | target=%s', self.target)
            await self._channel.close()
            self._channel = None
            self._stub = None
            logger.info('[EXTERNAL] gRPC channel closed | target=%s', self.target)

    async def __aenter__(self) -> 'MonolithGrpcClient':
        """Start the client when entering an async context manager."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        """Close the client when exiting an async context manager."""
        await self.close()

    # --------------------------
    # Public API
    # --------------------------

    async def save_document(
        self,
        *,
        internal_filename: str,
        mime: str,
        storage_bucket: str,
        storage_object_key: str,
        created_by: str,  # MonetaID (UUID string)
        created_at: Optional[datetime] = None,
        extra_metadata: Optional[Dict[str, str]] = None,
        timeout_sec: Optional[float] = None,
    ) -> pb.CreateDocumentResponse:
        """
        Create (or idempotently upsert) a document row.

        Args:
            internal_filename (str): System-assigned filename used as a stable key.
            mime (str): MIME type (e.g., 'application/pdf').
            storage_bucket (str): Object store bucket name.
            storage_object_key (str): Object key/path within the bucket.
            created_by (str): UUID (string) of the user who created/uploaded the doc.
            created_at (datetime | None): If None, defaults to now(UTC).
                Naive datetimes are assumed to be UTC.
            extra_metadata (dict[str, str] | None): Extra metadata to attach to the RPC.
            timeout_sec (float | None): Per-call timeout in seconds; falls back to
                the client's default if None.

        Returns:
            pb.CreateDocumentResponse: Contains:
                - status (CreateStatus)
                - row_id (str; UUID) when created/found
                - message (str) with additional info

        Raises:
            RuntimeError: If the client has not been started.
        """
        if not self._stub:
            logger.error('[EXTERNAL] gRPC client not started')
            raise RuntimeError(
                'Client not started. Call await client.start() or use "async with".'
            )

        logger.debug(
            '[EXTERNAL] gRPC CreateDocument | filename=%s | bucket=%s | created_by=%s',
            internal_filename,
            storage_bucket,
            created_by,
        )

        # Default created_at to 'now' in UTC if not provided
        if created_at is None:
            created_at = datetime.now(timezone.utc)
        elif created_at.tzinfo is None:
            # Assume naive datetimes are UTC
            created_at = created_at.replace(tzinfo=timezone.utc)

        ts = Timestamp()
        ts.FromDatetime(created_at)

        req = pb.CreateDocumentRequest(
            internal_filename=internal_filename,
            mime=mime,
            storage_bucket=storage_bucket,
            storage_object_key=storage_object_key,
            created_by=created_by,
            created_at=ts,
        )

        md = list(self.metadata)
        if extra_metadata:
            md.extend(extra_metadata.items())

        deadline = timeout_sec if timeout_sec is not None else self.timeout_sec

        try:
            response = await self._stub.CreateDocument(
                req, timeout=deadline, metadata=md
            )
            logger.info(
                '[EXTERNAL] gRPC CreateDocument completed | filename=%s | status=%s | row_id=%s',
                internal_filename,
                response.status,
                response.row_id,
            )
            return response
        except grpc.RpcError as e:
            logger.error(
                '[EXTERNAL] gRPC CreateDocument failed | filename=%s | error_code=%s | error=%s',
                internal_filename,
                e.code() if hasattr(e, 'code') else 'unknown',
                str(e),
            )
            raise

    async def save_document_version(
        self,
        *,
        document_id: str,  # UUID string
        version_number: int,  # >= 1
        storage_version_id: str,  # MinIO/S3 versionId
        created_by: str,  # UUID string
        created_at: Optional[datetime] = None,
        extra_metadata: Optional[Dict[str, str]] = None,
        timeout_sec: Optional[float] = None,
    ) -> pb.CreateDocumentVersionResponse:
        """
        Create a new document version row.

        Args:
            document_id (str): Parent document UUID (string).
            version_number (int): Version number (>= 1). May be ignored if
                the server computes the next version.
            storage_version_id (str): Object store version ID (e.g., MinIO versionId).
            created_by (str): UUID (string) of the user who created this version.
            created_at (datetime | None): If None, defaults to now(UTC).
                Naive datetimes are assumed to be UTC.
            extra_metadata (dict[str, str] | None): Extra metadata to attach to the RPC.
            timeout_sec (float | None): Per-call timeout in seconds; falls back to
                the client's default if None.

        Returns:
            pb.CreateDocumentVersionResponse: Contains:
                - status (CreateStatus)
                - version_id (str; UUID) on success
                - message (str)

        Raises:
            RuntimeError: If the client has not been started.
        """
        if not self._stub:
            logger.error('[EXTERNAL] gRPC client not started')
            raise RuntimeError(
                'Client not started. Call await client.start() or use "async with".'
            )

        logger.debug(
            '[EXTERNAL] gRPC CreateDocumentVersion | document_id=%s | version=%d | created_by=%s',
            document_id,
            version_number,
            created_by,
        )

        if created_at is None:
            created_at = datetime.now(timezone.utc)
        elif created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        ts = Timestamp()
        ts.FromDatetime(created_at)

        req = pb.CreateDocumentVersionRequest(
            document_id=document_id,
            version_number=version_number,
            storage_version_id=storage_version_id,
            created_by=created_by,
            created_at=ts,
        )

        md = list(self.metadata)
        if extra_metadata:
            md.extend(extra_metadata.items())

        deadline = timeout_sec if timeout_sec is not None else self.timeout_sec

        try:
            response = await self._stub.CreateDocumentVersion(
                req, timeout=deadline, metadata=md
            )
            logger.info(
                '[EXTERNAL] gRPC CreateDocumentVersion completed | document_id=%s | status=%s | version_id=%s',
                document_id,
                response.status,
                response.version_id,
            )
            return response
        except grpc.RpcError as e:
            logger.error(
                '[EXTERNAL] gRPC CreateDocumentVersion failed | document_id=%s | error_code=%s | error=%s',
                document_id,
                e.code() if hasattr(e, 'code') else 'unknown',
                str(e),
            )
            raise

    async def get_document(
        self,
        *,
        internal_filename: str,
        extra_metadata: Optional[Dict[str, str]] = None,
        timeout_sec: Optional[float] = None,
    ) -> pb.GetDocumentResponse:
        """
        Retrieve a document by its internal filename.

        Args:
            internal_filename (str): The system-internal filename (unique lookup key).
            extra_metadata (dict[str, str] | None): Extra metadata to attach to the RPC.
            timeout_sec (float | None): Per-call timeout in seconds; falls back to
                the client's default if None.

        Returns:
            pb.GetDocumentResponse: Contains:
                - status (FOUND | NOT_FOUND | FAILED)
                - document fields populated when FOUND
                - message (str)

        Raises:
            RuntimeError: If the client has not been started.
        """
        if not self._stub:
            logger.error('[EXTERNAL] gRPC client not started')
            raise RuntimeError(
                'Client not started. Call await client.start() or use "async with".'
            )

        logger.debug('[EXTERNAL] gRPC GetDocument | filename=%s', internal_filename)

        req = pb.GetDocumentRequest(internal_filename=internal_filename)

        md = list(self.metadata)
        if extra_metadata:
            md.extend(extra_metadata.items())

        deadline = timeout_sec if timeout_sec is not None else self.timeout_sec

        try:
            response = await self._stub.GetDocument(req, timeout=deadline, metadata=md)
            logger.info(
                '[EXTERNAL] gRPC GetDocument completed | filename=%s | status=%s',
                internal_filename,
                response.status,
            )
            return response
        except grpc.RpcError as e:
            logger.error(
                '[EXTERNAL] gRPC GetDocument failed | filename=%s | error_code=%s | error=%s',
                internal_filename,
                e.code() if hasattr(e, 'code') else 'unknown',
                str(e),
            )
            raise


# --------------------------
# Optional: simple sync helper
# --------------------------


def save_document_blocking(
    *,
    internal_filename: str,
    mime: str,
    storage_bucket: str,
    storage_object_key: str,
    created_by: str,
    created_at: Optional[datetime] = None,
    target: Optional[str] = None,
    timeout_sec: float = 3.0,
    metadata: Optional[Iterable[Tuple[str, str]]] = None,
) -> pb.CreateDocumentResponse:
    """
    Synchronous convenience wrapper for `save_document()`.

    Warning:
        Uses `asyncio.run(...)`. Do **not** call from a running event loop
        (e.g., within an async framework or some REPLs/Jupyter) or it will raise
        `RuntimeError: asyncio.run() cannot be called from a running event loop`.

    Args:
        internal_filename (str): See `save_document()`.
        mime (str): See `save_document()`.
        storage_bucket (str): See `save_document()`.
        storage_object_key (str): See `save_document()`.
        created_by (str): See `save_document()`.
        created_at (datetime | None): See `save_document()`.
        target (str | None): Override gRPC target for this call.
        timeout_sec (float): Per-RPC deadline.
        metadata (Iterable[tuple[str, str]] | None): Extra metadata headers.

    Returns:
        pb.CreateDocumentResponse: Same as `save_document()`.
    """

    async def _run():
        async with MonolithGrpcClient(
            target=target, timeout_sec=timeout_sec, metadata=metadata
        ) as client:
            return await client.save_document(
                internal_filename=internal_filename,
                mime=mime,
                storage_bucket=storage_bucket,
                storage_object_key=storage_object_key,
                created_by=created_by,
                created_at=created_at,
            )

    return asyncio.run(_run())


def save_document_version_blocking(
    *,
    document_id: str,
    version_number: int,
    storage_version_id: str,
    created_by: str,
    created_at: Optional[datetime] = None,
    target: Optional[str] = None,
    timeout_sec: float = 3.0,
    metadata: Optional[Iterable[Tuple[str, str]]] = None,
) -> pb.CreateDocumentVersionResponse:
    """
    Synchronous convenience wrapper for `save_document_version()`.

    Warning:
        Uses `asyncio.run(...)`. Do **not** call from a running event loop.

    Args:
        document_id (str): See `save_document_version()`.
        version_number (int): See `save_document_version()`.
        storage_version_id (str): See `save_document_version()`.
        created_by (str): See `save_document_version()`.
        created_at (datetime | None): See `save_document_version()`.
        target (str | None): Override gRPC target for this call.
        timeout_sec (float): Per-RPC deadline.
        metadata (Iterable[tuple[str, str]] | None): Extra metadata headers.

    Returns:
        pb.CreateDocumentVersionResponse: Same as `save_document_version()`.
    """
    async def _run():
        async with MonolithGrpcClient(
            target=target, timeout_sec=timeout_sec, metadata=metadata
        ) as client:
            return await client.save_document_version(
                document_id=document_id,
                version_number=version_number,
                storage_version_id=storage_version_id,
                created_by=created_by,
                created_at=created_at,
            )

    return asyncio.run(_run())


def get_document_blocking(
    *,
    internal_filename: str,
    target: Optional[str] = None,
    timeout_sec: float = 3.0,
    metadata: Optional[Iterable[Tuple[str, str]]] = None,
) -> pb.GetDocumentResponse:
    """
    Synchronous convenience wrapper for `get_document()`.

    Warning:
        Uses `asyncio.run(...)`. Do **not** call from a running event loop.

    Args:
        internal_filename (str): See `get_document()`.
        target (str | None): Override gRPC target for this call.
        timeout_sec (float): Per-RPC deadline.
        metadata (Iterable[tuple[str, str]] | None): Extra metadata headers.

    Returns:
        pb.GetDocumentResponse: Same as `get_document()`.
    """

    async def _run():
        async with MonolithGrpcClient(
            target=target, timeout_sec=timeout_sec, metadata=metadata
        ) as client:
            return await client.get_document(
                internal_filename=internal_filename
            )

    return asyncio.run(_run())
