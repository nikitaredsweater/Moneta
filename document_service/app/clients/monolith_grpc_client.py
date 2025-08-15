"""
gRPC client that can be used to make calls to monolith.
"""

from __future__ import annotations

import asyncio
import os
from typing import Dict, Iterable, Optional, Tuple

# Note: Ensure that you run the generate_protos.sh script
import app.gen.document_ingest_pb2 as pb
import app.gen.document_ingest_pb2_grpc as pbg
import grpc
from grpc import aio

# If you already have a Python Enum for DocumentType, you can import it and map to pb.DocumentType.
# Example:
# from app.enums.document_type import DocumentType as PyDocType
# def to_pb_doc_type(py_type: PyDocType) -> pb.DocumentType: return pb.DocumentType.Value(py_type.name)


class MonolithGrpcClient:
    """
    Thin, reusable client wrapper for the DocumentIngest gRPC service.

    Usage (async):
        client = MonolithGrpcClient()
        await client.start()
        resp = await client.save_document(company_id='...', user_id='...', document_type=pb.USER_DOCUMENT)
        await client.close()

    Or as a context manager:
        async with MonolithGrpcClient() as client:
            resp = await client.save_document(...)

    If you need blocking use, see the sync helper at the bottom.
    """

    def __init__(
        self,
        target: Optional[str] = None,
        timeout_sec: float = 3.0,
        metadata: Optional[Iterable[Tuple[str, str]]] = None,
        tls_root_cert: Optional[bytes] = None,
    ):
        """
        :param target: host:port of the gRPC server. Defaults to env MONOLITH_GRPC_TARGET or 'localhost:50061'.
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
            creds = grpc.ssl_channel_credentials(
                root_certificates=self._tls_root_cert
            )
            self._channel = aio.secure_channel(self.target, creds)
        else:
            self._channel = aio.insecure_channel(self.target)

        self._stub = pbg.DocumentIngestStub(self._channel)

    async def close(self) -> None:
        if self._channel:
            await self._channel.close()
            self._channel = None
            self._stub = None

    async def __aenter__(self) -> 'MonolithGrpcClient':
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    # --------------------------
    # Public API (add more later)
    # --------------------------

    async def save_document(
        self,
        *,
        company_id: str,
        user_id: str,
        document_type: int,  # pb.DocumentType enum value (e.g., pb.USER_DOCUMENT)
        extra_metadata: Optional[Dict[str, str]] = None,
        timeout_sec: Optional[float] = None,
    ) -> pb.CreateDocumentRowResponse:
        """
        Create (or idempotently upsert) a document row.

        Returns pb.CreateDocumentRowResponse with status/row_id/message.
        Raises grpc.aio.AioRpcError on transport/status failures.
        """
        if not self._stub:
            raise RuntimeError(
                'Client not started. Call await client.start() or use 'async with'.'
            )

        req = pb.CreateDocumentRowRequest(
            company_id=company_id,
            user_id=user_id,
            document_type=document_type,
        )

        md = list(self.metadata)
        if extra_metadata:
            md.extend(extra_metadata.items())

        deadline = timeout_sec if timeout_sec is not None else self.timeout_sec

        return await self._stub.CreateDocumentRow(
            req, timeout=deadline, metadata=md
        )


# --------------------------
# Optional: simple sync helper
# --------------------------


def save_document_blocking(
    company_id: str,
    user_id: str,
    document_type: int,  # pb.DocumentType enum value
    target: Optional[str] = None,
    timeout_sec: float = 3.0,
    metadata: Optional[Iterable[Tuple[str, str]]] = None,
) -> pb.CreateDocumentRowResponse:
    """
    For occasional sync contexts (scripts, management commands).
    """

    async def _run():
        async with MonolithGrpcClient(
            target=target, timeout_sec=timeout_sec, metadata=metadata
        ) as client:
            return await client.save_document(
                company_id=company_id,
                user_id=user_id,
                document_type=document_type,
            )

    return asyncio.run(_run())
