"""
gRPC server for document ingestion.

This module defines the asynchronous gRPC servicer that handles creation and
retrieval of documents and their versions. It validates incoming protobuf
requests, converts types (UUIDs, timestamps), delegates persistence to service
functions, and maps failures to appropriate gRPC statuses or response codes.

Responsibilities:
    - CreateDocument: insert new document metadata
    - CreateDocumentVersion: add a version entry for an existing document
    - GetDocument: fetch a document by its internal filename

All returned datetimes are normalized to aware UTC values. Validation errors
abort the RPC with INVALID_ARGUMENT; unexpected failures are mapped to FAILED
statuses in the response message.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

import app.gen.document_ingest_pb2 as pb
import app.gen.document_ingest_pb2_grpc as pbg
import grpc
from app.services.grpc_document_service import (
    get_document_by_filename,
    save_document,
    save_document_version,
)
from google.protobuf.timestamp_pb2 import Timestamp

logger = logging.getLogger(__name__)


def _to_uuid(value: str) -> uuid.UUID:
    """
    Convert a string to a UUID.

    Args:
        value (str): The UUID string.

    Returns:
        uuid.UUID: Parsed UUID instance.
    """
    return uuid.UUID(value)


def _ts_to_datetime(ts: Timestamp | None) -> datetime:
    """
    Convert google.protobuf.Timestamp -> aware UTC datetime.
    If ts is None/not set, return now(UTC).

    Args:
        ts (Timestamp | None): Protobuf timestamp; if None, returns now(UTC).

    Returns:
        datetime: A timezone-aware datetime in UTC.
    """
    if ts is None:
        return datetime.now(timezone.utc)
    # Timestamp in Python has ToDatetime(); ensure UTC
    dt = ts.ToDatetime()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt


def _datetime_to_ts(dt: datetime) -> Timestamp:
    """
    Convert datetime to google.protobuf.Timestamp.

    Args:
        dt (datetime): A timezone-aware datetime.

    Returns:
        Timestamp: A protobuf timestamp.
    """
    ts = Timestamp()
    # Ensure timezone-aware datetime
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    ts.FromDatetime(dt)
    return ts


class DocumentIngestService(pbg.DocumentIngestServicer):
    """
    gRPC servicer implementing document ingestion operations.

    This class provides async RPC handlers that:
      - Validate request payloads
      - Convert types (UUIDs, timestamps)
      - Delegate to service-layer functions for persistence
      - Map exceptions to gRPC errors or FAILED response statuses
    """

    def __init__(self) -> None:
        """
        Initialize the servicer. Currently a no-op.
        """
        logger.info('[EXTERNAL] gRPC DocumentIngestService initialized')

    async def CreateDocument(self, request: pb.CreateDocumentRequest, context):
        """
        Create a new document row in the database.

        Error Handling:
            - On missing/invalid arguments: aborts with INVALID_ARGUMENT.
            - On unexpected errors: returns FAILED with error message.

        Args:
            request (pb.CreateDocumentRequest): The request message
                containing document metadata.
            context (grpc.ServicerContext): The context for the RPC call.

        Returns:
            pb.CreateDocumentResponse:
                - status: CREATED on success; FAILED otherwise.
                - row_id: The created document UUID (string) on success.
                - message: Contextual information on the outcome.
        """
        logger.debug(
            '[EXTERNAL] gRPC CreateDocument | filename=%s | mime=%s',
            request.internal_filename,
            request.mime,
        )
        # --- Validation ---
        missing = []
        if not request.internal_filename:
            missing.append('internal_filename')
        if not request.mime:
            missing.append('mime')
        if not request.storage_bucket:
            missing.append('storage_bucket')
        if not request.storage_object_key:
            missing.append('storage_object_key')
        if not request.created_by:
            missing.append('created_by')

        if missing:
            logger.warning(
                '[EXTERNAL] gRPC CreateDocument validation failed | missing=%s',
                missing,
            )
            await context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                f'Missing required fields: {", ".join(missing)}',
            )

        # Validate created_by as UUID
        try:
            created_by_uuid = _to_uuid(request.created_by)
        except Exception:
            logger.warning(
                '[EXTERNAL] gRPC CreateDocument invalid UUID | created_by=%s',
                request.created_by,
            )
            await context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                'created_by must be a valid UUID',
            )

        # created_at: use provided or default to now(UTC)
        created_at_dt = (
            _ts_to_datetime(request.created_at)
            if request.HasField('created_at')
            else datetime.now(timezone.utc)
        )

        # --- Persist ---
        try:
            doc = await save_document(
                internal_filename=request.internal_filename,
                mime=request.mime,
                storage_bucket=request.storage_bucket,
                storage_object_key=request.storage_object_key,
                created_by_user_id=created_by_uuid,
                created_at=created_at_dt,
            )
        except Exception as e:
            logger.error(
                '[EXTERNAL] gRPC CreateDocument failed | filename=%s | '
                'error_type=%s | error=%s',
                request.internal_filename,
                type(e).__name__,
                str(e),
            )
            return pb.CreateDocumentResponse(
                status=pb.CreateDocumentResponse.FAILED,
                row_id='',
                message=str(e),
            )

        logger.info(
            '[EXTERNAL] gRPC CreateDocument success | document_id=%s | filename=%s',
            getattr(doc, 'id', ''),
            request.internal_filename,
        )
        return pb.CreateDocumentResponse(
            status=pb.CreateDocumentResponse.CREATED,
            row_id=str(getattr(doc, 'id', '')),
            message='Created',
        )

    async def CreateDocumentVersion(
        self, request: pb.CreateDocumentVersionRequest, context
    ):
        """
        Add a new version entry for an existing document.

        Error Handling:
            - On missing/invalid arguments: aborts with INVALID_ARGUMENT.
            - On unexpected errors: returns FAILED with error message.

        Args:
            request (pb.CreateDocumentVersionRequest): The request message
                containing document version metadata.
            context (grpc.ServicerContext): The context for the RPC call.

        Returns:
            pb.CreateDocumentVersionResponse:
                - status: CREATED on success; FAILED otherwise.
                - version_id: The created document version UUID
                    (string) on success.
                - message: Contextual information on the outcome.
        """
        logger.debug(
            '[EXTERNAL] gRPC CreateDocumentVersion | document_id=%s | version=%s',
            request.document_id,
            request.version_number,
        )
        # --- Validation ---
        missing = []
        if not request.document_id:
            missing.append('document_id')
        if request.version_number == 0:
            missing.append('version_number (>=1)')
        if not request.storage_version_id:
            missing.append('storage_version_id')
        if not request.created_by:
            missing.append('created_by')
        if missing:
            logger.warning(
                '[EXTERNAL] gRPC CreateDocumentVersion validation failed | missing=%s',
                missing,
            )
            await context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                f'Missing: {", ".join(missing)}',
            )

        # Validate IDs
        try:
            doc_uuid = _to_uuid(request.document_id)
            created_by_uuid = _to_uuid(request.created_by)
        except Exception:
            logger.warning(
                '[EXTERNAL] gRPC CreateDocumentVersion invalid UUID | '
                'document_id=%s | created_by=%s',
                request.document_id,
                request.created_by,
            )
            await context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                'document_id and created_by must be UUIDs',
            )

        created_at = (
            _ts_to_datetime(request.created_at)
            if request.HasField('created_at')
            else datetime.now(timezone.utc)
        )

        try:
            v = await save_document_version(
                document_id=doc_uuid,
                storage_version_id=request.storage_version_id,
                created_by=created_by_uuid,
                created_at=created_at,
            )
        except Exception as e:
            logger.error(
                '[EXTERNAL] gRPC CreateDocumentVersion failed | document_id=%s | '
                'error_type=%s | error=%s',
                request.document_id,
                type(e).__name__,
                str(e),
            )
            return pb.CreateDocumentVersionResponse(
                status=pb.CreateDocumentResponse.FAILED,
                version_id='',
                message=str(e),
            )

        logger.info(
            '[EXTERNAL] gRPC CreateDocumentVersion success | version_id=%s | '
            'document_id=%s',
            getattr(v, 'id', ''),
            request.document_id,
        )
        return pb.CreateDocumentVersionResponse(
            status=pb.CreateDocumentResponse.CREATED,
            version_id=str(getattr(v, 'id', '')),
            message='Created',
        )

    async def GetDocument(self, request: pb.GetDocumentRequest, context):
        """
        Retrieve a document by its internal filename.

        Error Handling:
            - On missing argument: aborts with INVALID_ARGUMENT.
            - On unexpected errors: returns FAILED with error message.

        Args:
            request (pb.GetDocumentRequest): The request message
                containing the internal filename.
            context (grpc.ServicerContext): The context for the RPC call.

        Returns:
            pb.GetDocumentResponse:
                - status: FOUND, NOT_FOUND, or FAILED.
                - document_id, internal_filename, mime, storage_*:
                    Populated on FOUND.
                - created_by (str, UUID) and created_at (Timestamp):
                     Populated on FOUND.
                - message: Contextual information on the outcome.
        """
        logger.debug(
            '[EXTERNAL] gRPC GetDocument | filename=%s', request.internal_filename
        )
        # --- Validation ---
        if not request.internal_filename:
            logger.warning('[EXTERNAL] gRPC GetDocument missing filename')
            await context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                'Missing required field: internal_filename',
            )

        # --- Retrieve ---
        try:
            document = await get_document_by_filename(request.internal_filename)

            if document is None:
                # Document not found
                logger.warning(
                    '[EXTERNAL] gRPC GetDocument not found | filename=%s',
                    request.internal_filename,
                )
                return pb.GetDocumentResponse(
                    status=pb.GetDocumentResponse.NOT_FOUND,
                    document_id='',
                    internal_filename=request.internal_filename,
                    mime='',
                    storage_bucket='',
                    storage_object_key='',
                    created_by='',
                    message='Document not found',
                )

            # Document found - populate response
            logger.info(
                '[EXTERNAL] gRPC GetDocument found | document_id=%s | filename=%s',
                document.id,
                request.internal_filename,
            )
            return pb.GetDocumentResponse(
                status=pb.GetDocumentResponse.FOUND,
                document_id=str(document.id),
                internal_filename=document.internal_filename,
                mime=document.mime,
                storage_bucket=document.storage_bucket,
                storage_object_key=document.storage_object_key,
                created_by=str(document.created_by),
                created_at=_datetime_to_ts(document.created_at),
                message='Document found',
            )

        except Exception as e:
            # Map unknown failures to FAILED status
            logger.error(
                '[EXTERNAL] gRPC GetDocument failed | filename=%s | '
                'error_type=%s | error=%s',
                request.internal_filename,
                type(e).__name__,
                str(e),
            )
            return pb.GetDocumentResponse(
                status=pb.GetDocumentResponse.FAILED,
                document_id='',
                internal_filename=request.internal_filename,
                mime='',
                storage_bucket='',
                storage_object_key='',
                created_by='',
                message=f'Error retrieving document: {str(e)}',
            )
