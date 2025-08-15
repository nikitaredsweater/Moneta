"""
gRPC server
"""

import app.gen.document_ingest_pb2 as pb
import app.gen.document_ingest_pb2_grpc as pbg
import grpc


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

        return pb.CreateDocumentRowResponse(
            status=pb.CreateDocumentRowResponse.CREATED,
            row_id=str('test'),
            message='Upserted',
        )
