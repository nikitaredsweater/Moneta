'''
Routes for uploading and downloading the actual documents, not metadata
'''

from app.enums import DocumentType
from app.schemas import DocumentUploadRequest
from app.services import generate_presigned_upload_url
from app.utils import generate_secure_key
from fastapi import APIRouter

document_router = APIRouter()


# TODO: Add a permissions check and etc
@document_router.post('/upload/request')
async def request_upload_link(document_data: DocumentUploadRequest):
    '''
    Gets you a link needed to directly upload the file.
    Step 1/2 to upload the file into the system.

    This is a system-blocking call, meaning it is not dealt with in a queue,
    to allow user to actually get the upload link.
    '''
    # Example -- Get a key
    key = generate_secure_key(
        doc_type=document_data.document_type,
        user_id='user-123',
        instrument_id='instr-789',
        extension=document_data.extension,
    )

    # Save the key on the redis DB? <-- skipping this for now

    # Creating the upload link in minIO
    upload_url = generate_presigned_upload_url(key)
    return {'key': upload_url}
