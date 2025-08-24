"""
Helper functions to parse different minIO events into dictioanries
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List
from urllib.parse import unquote
from pathlib import PurePosixPath
import mimetypes


@dataclass
class MinIOEvent:
    """
    Unified representation of a MinIO/S3 object event.

    All fields are optional. If a value is not present in the original
    event payload, it will be set to None.

    This class is designed to cover both ObjectCreated and ObjectRemoved
    event types, plus any additional metadata that MinIO may include.

    Fields are grouped as follows:
    - Top-level event info
    - Schema/configuration info
    - User identity and request source
    - Response metadata (IDs from MinIO/S3)
    - Bucket information
    - Object information (key, size, content type, etc.)
    - User-defined metadata
    - Convenience fields (parsed from object key)
    """

    # Top-level event info
    event_name: Optional[str] = None
    key: Optional[str] = None  # Top-level key (may duplicate object key)
    event_version: Optional[str] = None
    event_source: Optional[str] = None
    aws_region: Optional[str] = None
    event_time: Optional[str] = None  # raw string
    event_time_dt: Optional[datetime] = None  # parsed datetime object

    # Schema/config
    s3_schema_version: Optional[str] = None
    configuration_id: Optional[str] = None

    # Identity
    user_identity_principal_id: Optional[str] = None   # uploader's identity
    request_principal_id: Optional[str] = None         # principal from request

    # Request/source
    source_ip_address: Optional[str] = None
    source_host: Optional[str] = None
    source_port: Optional[str] = None
    user_agent: Optional[str] = None

    # Response
    amz_id_2: Optional[str] = None
    request_id: Optional[str] = None
    deployment_id: Optional[str] = None
    origin_endpoint: Optional[str] = None

    # Bucket
    bucket_name: Optional[str] = None
    bucket_arn: Optional[str] = None
    bucket_owner_principal_id: Optional[str] = None

    # Object
    object_key: Optional[str] = None           # decoded, human-readable path
    object_key_raw: Optional[str] = None       # raw from event
    object_size: Optional[int] = None
    object_etag: Optional[str] = None
    object_content_type: Optional[str] = None  # raw event content-type
    mime: Optional[str] = None                 # effective/guessed mime
    object_sequencer: Optional[str] = None
    object_version_id: Optional[str] = None
    object_is_delete_marker: Optional[bool] = None
    object_storage_class: Optional[str] = None
    object_checksum_algorithm: Optional[List[str]] = None

    # User metadata
    user_metadata: Optional[Dict[str, str]] = None
    
    # Version (if versioning is enabled)
    version_id: Optional[str] = None

    # Convenience (from key)
    filename: Optional[str] = None
    file_path: Optional[str] = None


def _parse_iso_time(value: Optional[str]) -> Optional[datetime]:
    """
    Parse an ISO8601 timestamp string from MinIO into a datetime.
    Returns None if parsing fails.
    """
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except Exception:
        return None


def _to_int(v: Any) -> Optional[int]:
    """
    Safely cast a value to int. Returns None if not possible.
    """
    try:
        return int(v) if v is not None else None
    except Exception:
        return None


def parse_minio_event(event: Dict[str, Any]) -> MinIOEvent:
    """
    Convert a raw MinIO/S3 event dictionary into a MinIOEvent object.

    This function supports events with the AWS-style "Records" array as well
    as simpler top-level MinIO formats. It extracts and normalizes all
    possible fields into a single dataclass.

    Args:
        event: Raw event dictionary from MinIO/S3 notification.

    Returns:
        MinIOEvent: Populated object with as many fields as could be parsed.
    """
    # Use first record if available
    if isinstance(event.get("Records"), list) and event["Records"]:
        rec = event["Records"][0]
    else:
        rec = event  # fallback to top-level keys

    # Top-level info
    event_name = rec.get("eventName") or event.get("EventName")
    key_top = event.get("Key")
    aws_region = rec.get("awsRegion") or (rec.get("requestParameters") or {}).get("region") or event.get("Region")
    event_time_raw = rec.get("eventTime") or event.get("EventTime")
    event_time_dt = _parse_iso_time(event_time_raw)

    # Identity and request info
    user_identity_principal_id = (rec.get("userIdentity") or {}).get("principalId")
    request_params = rec.get("requestParameters") or {}
    request_principal_id = request_params.get("principalId")
    source_ip_address = request_params.get("sourceIPAddress")
    source_block = rec.get("source") or {}
    source_host = source_block.get("host")
    source_port = source_block.get("port")
    user_agent = source_block.get("userAgent")

    # Response elements
    resp = rec.get("responseElements") or {}
    amz_id_2 = resp.get("x-amz-id-2")
    request_id = resp.get("x-amz-request-id")
    deployment_id = resp.get("x-minio-deployment-id")
    origin_endpoint = resp.get("x-minio-origin-endpoint")

    # S3 structure
    s3 = rec.get("s3") or {}
    s3_schema_version = s3.get("s3SchemaVersion")
    configuration_id = s3.get("configurationId")

    # Bucket
    bucket_info = s3.get("bucket") or {}
    bucket_name = bucket_info.get("name") or event.get("Bucket")
    bucket_arn = bucket_info.get("arn") or event.get("BucketArn")
    bucket_owner_principal_id = (bucket_info.get("ownerIdentity") or {}).get("principalId")

    # Object info
    obj = s3.get("object") or {}
    object_key_raw = obj.get("key") or key_top
    object_key = unquote(object_key_raw) if object_key_raw else None
    filename = PurePosixPath(object_key).name if object_key else None
    file_path = str(PurePosixPath(object_key).parent) if object_key else None

    object_size = _to_int(obj.get("size") or event.get("Size"))
    object_etag = obj.get("eTag") or event.get("ETag")
    object_content_type = obj.get("contentType") or event.get("ContentType")
    object_sequencer = obj.get("sequencer")
    object_version_id = obj.get("versionId") or event.get("VersionId")
    object_is_delete_marker = obj.get("isDeleteMarker")
    object_storage_class = obj.get("storageClass")
    checksum_alg = obj.get("checksumAlgorithm")
    if isinstance(checksum_alg, str):
        object_checksum_algorithm: Optional[List[str]] = [checksum_alg]
    elif isinstance(checksum_alg, list):
        object_checksum_algorithm = checksum_alg
    else:
        object_checksum_algorithm = None

    # User metadata (normalize keys to lower-case)
    user_metadata_raw = obj.get("userMetadata") or event.get("UserMetadata") or {}
    user_metadata = {str(k).lower(): v for k, v in user_metadata_raw.items()} if user_metadata_raw else None

    # Versioning
    version_id = obj.get('versionId') or ''

    # Effective MIME
    if object_content_type and object_content_type.lower() != "binary/octet-stream":
        mime = object_content_type
    elif filename:
        guessed, _ = mimetypes.guess_type(filename)
        mime = guessed or "application/octet-stream"
    else:
        mime = None

    return MinIOEvent(
        event_name=event_name,
        key=key_top,
        event_version=rec.get("eventVersion") or event.get("EventVersion"),
        event_source=rec.get("eventSource") or event.get("EventSource"),
        aws_region=aws_region,
        event_time=event_time_raw,
        event_time_dt=event_time_dt,
        s3_schema_version=s3_schema_version,
        configuration_id=configuration_id,
        user_identity_principal_id=user_identity_principal_id,
        request_principal_id=request_principal_id,
        source_ip_address=source_ip_address,
        source_host=source_host,
        source_port=source_port,
        user_agent=user_agent,
        amz_id_2=amz_id_2,
        request_id=request_id,
        deployment_id=deployment_id,
        origin_endpoint=origin_endpoint,
        bucket_name=bucket_name,
        bucket_arn=bucket_arn,
        bucket_owner_principal_id=bucket_owner_principal_id,
        object_key=object_key,
        object_key_raw=object_key_raw,
        object_size=object_size,
        object_etag=object_etag,
        object_content_type=object_content_type,
        mime=mime,
        object_sequencer=object_sequencer,
        object_version_id=object_version_id,
        object_is_delete_marker=object_is_delete_marker,
        object_storage_class=object_storage_class,
        object_checksum_algorithm=object_checksum_algorithm,
        user_metadata=user_metadata,
        version_id=version_id,
        filename=filename,
        file_path=file_path,
    )
