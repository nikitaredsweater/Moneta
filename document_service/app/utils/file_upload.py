import uuid
from datetime import datetime


def generate_secure_key(
    user_id: str,
    extension: str,
    *,
    company_id: str | None = None,
) -> str:
    """
    Generate a secure, structured MinIO object key based on document type.

    Args:
        user_id (str): ID of the user initiating the upload.
        extension (str): File extension, e.g. 'pdf'.
        company_id (str, optional): Required for company documents.

    Returns:
        str: MinIO object key (path).
    """

    now = (
        datetime.utcnow().strftime("%Y%m%d-%H%M")
        + f"-{int(datetime.utcnow().timestamp())}"
    )
    rand = uuid.uuid4().hex

    return f'{company_id}/{user_id}/{now}_{rand}.{extension}'
