"""
gRPC client that can be used to make calls to monolith.
"""
from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone
from typing import Dict, Iterable, Optional, Tuple

import grpc
from grpc import aio
from google.protobuf.timestamp_pb2 import Timestamp

# Generated modules (re-run your protoc script after changing the .proto)
import app.gen.document_ingest_pb2 as pb
import app.gen.document_ingest_pb2_grpc as pbg


class MonolithGrpcClient:
    """
    Thin, reusable client wrapper for the DocumentIngest gRPC service.

    Usage (async):
        async with MonolithGrpcClient() as client:
            resp = await client.save_document(
                internal_filename="20250822-0652-...txt",
                mime="text/plain",
                storage_bucket="documents",
                storage_object_key="user_docs/user-123/20250822-....txt",
                created_by="70b30fbc-3856-4f2f-89cd-c1c5688ca7c9",
                # created_at optional; defaults to now (UTC)
            )
    """

    def __init__(
        self,
        target: Optional[str] = None,
        timeout_sec: float = 3.0,
        metadata: Optional[Iterable[Tuple[str, str]]] = None,
        tls_root_cert: Optional[bytes] = None,
    ):
        """
        :param target: host:port of the gRPC server. Defaults to env MONOLITH_GRPC_TARGET or 'app:50061'.
        :param timeout_sec: per-RPC deadline (seconds).
        :param metadata: iterable of (key, value) tuples to attach to each RPC (e.g., auth).
        :param tls_root_cert: if provided, uses TLS with given root cert; otherwise insecure channel.
        """
        self.target = target or os.getenv('MONOLITH_GRPC_TARGET', 'app:50061')
        self.timeout_sec = timeout_sec
        self.metadata = list(metadata or [])
        self._channel: Optional[aio.Channel] = None
        self._stub: Optional[pbg.DocumentIngestStub] = None
        self._tls_root_cert = tls_root_cert

    async def start(self) -> None:
        if self._channel:
            return
        if self._tls_root_cert:
            creds = grpc.ssl_channel_credentials(root_certificates=self._tls_root_cert)
            self._channel = aio.secure_channel(self.target, creds)
        else:
            self._channel = aio.insecure_channel(self.target)
        self._stub = pbg.DocumentIngestStub(self._channel)

    async def close(self) -> None:
        if self._channel:
            await self._channel.close()
            self._channel = None
            self._stub = None

    async def __aenter__(self) -> "MonolithGrpcClient":
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
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

        Returns pb.CreateDocumentResponse with status/row_id/message.
        Raises grpc.aio.AioRpcError on transport/status failures.
        """
        if not self._stub:
            raise RuntimeError(
                "Client not started. Call await client.start() or use 'async with'."
            )

        # Default created_at to "now" in UTC if not provided
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

        return await self._stub.CreateDocument(req, timeout=deadline, metadata=md)


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
    For occasional sync contexts (scripts, management commands).
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
