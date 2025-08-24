"""
gRPC server (updated for CreateDocument)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import grpc
from google.protobuf.timestamp_pb2 import Timestamp

import app.gen.document_ingest_pb2 as pb
import app.gen.document_ingest_pb2_grpc as pbg

# NOTE: your module name says "grcp" (typo?). Keeping it as-is to match your codebase.
from app.services.grcp_document_service import save_document, save_document_version


def _to_uuid(value: str) -> uuid.UUID:
    """Validate/convert a string to UUID or raise INVALID_ARGUMENT upstream."""
    return uuid.UUID(value)


def _ts_to_datetime(ts: Timestamp | None) -> datetime:
    """
    Convert google.protobuf.Timestamp -> aware UTC datetime.
    If ts is None/not set, return now(UTC).
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


class DocumentIngestService(pbg.DocumentIngestServicer):
    def __init__(self) -> None:
        pass

    async def CreateDocument(self, request: pb.CreateDocumentRequest, context):
        """
        Create a document row in the database.

        Required fields:
          - internal_filename
          - mime
          - storage_bucket
          - storage_object_key
          - created_by (UUID string)

        Optional:
          - created_at (protobuf Timestamp); defaults to now(UTC)
        """
        # --- Validation ---
        missing = []
        if not request.internal_filename:
            missing.append("internal_filename")
        if not request.mime:
            missing.append("mime")
        if not request.storage_bucket:
            missing.append("storage_bucket")
        if not request.storage_object_key:
            missing.append("storage_object_key")
        if not request.created_by:
            missing.append("created_by")

        if missing:
            await context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                f"Missing required fields: {', '.join(missing)}",
            )

        # Validate created_by as UUID
        try:
            created_by_uuid = _to_uuid(request.created_by)
        except Exception:
            await context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "created_by must be a valid UUID",
            )

        # created_at: use provided or default to now(UTC)
        created_at_dt = (
            _ts_to_datetime(request.created_at)
            if request.HasField("created_at")
            else datetime.now(timezone.utc)
        )

        # --- Persist ---
        try:
            doc = await save_document(
                internal_filename=request.internal_filename,
                mime=request.mime,
                storage_bucket=request.storage_bucket,
                storage_object_key=request.storage_object_key,
                created_by_user_id=created_by_uuid,  # map to your current service signature
                created_at=created_at_dt,            # if your service accepts/uses it
            )
        except Exception as e:
            # Map unknown failures to FAILED status; include message for debugging
            return pb.CreateDocumentResponse(
                status=pb.CreateDocumentResponse.FAILED,
                row_id="",
                message=str(e),
            )

        # If your save_document can signal idempotent "already exists", map it here.
        # For now, assume created/upserted successfully.
        return pb.CreateDocumentResponse(
            status=pb.CreateDocumentResponse.CREATED,
            row_id=str(getattr(doc, "id", "")),
            message="Created",
        )
    
    async def CreateDocumentVersion(
        self, request: pb.CreateDocumentVersionRequest, context
    ):
        missing = []
        if not request.document_id:        missing.append("document_id")
        if request.version_number == 0:    missing.append("version_number (>=1)")
        if not request.storage_version_id: missing.append("storage_version_id")
        if not request.created_by:         missing.append("created_by")
        if missing:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, f"Missing: {', '.join(missing)}")

        # Validate IDs
        try:
            doc_uuid = _to_uuid(request.document_id)
            created_by_uuid = _to_uuid(request.created_by)
        except Exception:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "document_id and created_by must be UUIDs")

        created_at = _ts_to_datetime(request.created_at) if request.HasField("created_at") else datetime.now(timezone.utc)

        try:
            v = await save_document_version(
                document_id=doc_uuid,
                version_number=int(request.version_number),
                storage_version_id=request.storage_version_id,
                created_by=created_by_uuid,
                created_at=created_at,
            )
        except Exception as e:
            return pb.CreateDocumentVersionResponse(
                status=pb.CreateDocumentResponse.FAILED,
                version_id="",
                message=str(e),
            )

        return pb.CreateDocumentVersionResponse(
            status=pb.CreateDocumentResponse.CREATED,
            version_id=str(getattr(v, "id", "")),
            message="Created",
        )
