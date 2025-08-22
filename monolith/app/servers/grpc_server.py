"""
gRPC server
"""

import uuid

import app.gen.document_ingest_pb2 as pb
import app.gen.document_ingest_pb2_grpc as pbg
import grpc
from app.services.grcp_document_service import save_document


class DocumentIngestService(pbg.DocumentIngestServicer):
    def __init__(self):
        pass

    async def CreateDocumentRow(
        self, request: pb.CreateDocumentRowRequest, context
    ):
        """
        Method will add to the database the information about a new file
        """
        if (
            not request.company_id
            or not request.user_id
            or request.document_type == pb.DOCUMENT_TYPE_UNSPECIFIED
        ):
            await context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                'company_id, user_id, document_type required',
            )

        print('HELLLO!')
        # TODO: Update .proto to pass all the required fields
        # For now, just dummy values
        doc = await save_document(
            internal_filename='example.txt',
            mime='text/plain',
            storage_bucket='documents',
            storage_object_key='random/path/example.txt',
            created_by_user_id=uuid.UUID(
                "70b30fbc-3856-4f2f-89cd-c1c5688ca7c9"
            ),
        )  # Testing rn

        return pb.CreateDocumentRowResponse(
            status=pb.CreateDocumentRowResponse.CREATED,
            row_id=str(doc.id),
            message='Upserted',
        )
