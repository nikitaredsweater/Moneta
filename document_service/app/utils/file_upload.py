import uuid
from datetime import datetime

from app.enums import DocumentType


# TODO: Turn these errors into excpetions in a separate file
def generate_secure_key(
    doc_type: DocumentType,
    user_id: str,
    extension: str,
    *,
    company_id: str | None = None,
    instrument_id: str | None = None,
) -> str:
    """
    Generate a secure, structured MinIO object key based on document type.

    Args:
        doc_type (DocumentType): Type of document.
        user_id (str): ID of the user initiating the upload.
        extension (str): File extension, e.g. 'pdf'.
        company_id (str, optional): Required for company documents.
        instrument_id (str, optional): Required for instrument documents.

    Returns:
        str: MinIO object key (path).
    """

    now = (
        datetime.utcnow().strftime("%Y%m%d-%H%M")
        + f"-{int(datetime.utcnow().timestamp())}"
    )
    rand = uuid.uuid4().hex

    if doc_type == DocumentType.USER_DOCUMENT:
        return f"user_docs/{user_id}/{now}_{rand}.{extension}"

    elif doc_type == DocumentType.COMPANY_DOCUMENT:
        if not company_id:
            raise ValueError("company_id is required for COMPANY_DOCUMENT")
        return f"company_docs/{company_id}/{now}_{rand}.{extension}"

    elif doc_type == DocumentType.INSTRUMENT_RAW_DOCUMENT:
        if not instrument_id:
            raise ValueError(
                "instrument_id is required for INSTRUMENT_RAW_DOCUMENT"
            )
        return f"instrument_raw/{instrument_id}/{now}_{rand}.{extension}"

    elif doc_type == DocumentType.INSTRUMENT_PROCESSED_DOCUMENT:
        if not instrument_id:
            raise ValueError(
                "instrument_id is required for INSTRUMENT_PROCESSED_DOCUMENT"
            )
        return f"instrument_processed/{instrument_id}/{now}_{rand}.{extension}"

    else:
        raise ValueError(f"Unsupported document type: {doc_type}")
