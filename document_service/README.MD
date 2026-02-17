# Document Service

The Document Service is a microservice responsible for handling document uploads, storage, and metadata management within the Moneta financial platform. It provides REST API endpoints for frontend developers and uses gRPC to communicate with the monolith service for database operations.

## Table of Contents

- [API Endpoints](#api-endpoints)
- [gRPC Messages](#grpc-messages)  
- [Setup Instructions](#setup-instructions)
- [Docker Configuration](#docker-configuration)

## API Endpoints

The service exposes the following REST API endpoints for frontend integration:

### Base URL
All endpoints are prefixed with `/v1`

### Health Check

#### `GET /v1/health/`
Simple health check endpoint to verify service status.

**Response:**
```json
{
  "status": "healthy"
}
```

### Document Upload

#### `POST /v1/document/upload/request`
Requests a presigned upload URL for direct file upload to MinIO storage. This is step 1 of the 2-step upload process.

**Request Body:**
```json
{
  "documentType": "USER_DOCUMENT",
  "extension": "pdf"
}
```

**Parameters:**
- `documentType` (required): Type of document being uploaded. Must be one of:
  - `USER_DOCUMENT` - For user verification documents (passport, trading permissions, etc.)
  - `COMPANY_DOCUMENT` - For company verification documents (legal documents, background checks)
  - `INSTRUMENT_RAW_DOCUMENT` - Raw documents for instrument creation (high security)
  - `INSTRUMENT_PROCESSED_DOCUMENT` - Processed documents supporting instruments
- `extension` (required): File extension (e.g., "pdf", "jpg", "png")

**Response:**
```json
{
  "key": "https://minio:9000/documents/user_docs/70b30fbc-3856-4f2f-89cd-c1c5688ca7c9/20240822-1234-abcd.pdf?X-Amz-Algorithm=..."
}
```

**What to do with the response:**
1. Use the returned `key` (presigned URL) to upload your file directly to MinIO storage
2. Perform a PUT request to this URL with your file as the request body
3. The service will automatically detect the upload via MinIO events and create database records

**Important Notes:**
- This is a synchronous, blocking call to ensure you receive the upload link immediately
- The presigned URL has a limited lifetime (typically 10 minutes)
- After uploading to the presigned URL, the system automatically processes the document and creates database entries

### Document Access

#### `POST /v1/document/access/request`
Requests a presigned download URL to access a document by its exact name.

**Request Body:**
```json
{
  "documentName": "20240822-1234-abcd.pdf"
}
```

**Parameters:**
- `documentName` (required): Exact name of the document as stored in MinIO

**Response:**
```json
{
  "access_url": "https://minio:9000/documents/company-1234/70b30fbc-3856-4f2f-89cd-c1c5688ca7c9/20240822-1234-abcd.pdf?X-Amz-Algorithm=..."
}
```

**What to do with the response:**
1. Use the returned `access_url` (presigned URL) to download the document directly from MinIO
2. Perform a GET request to this URL to retrieve the file
3. The URL is valid for 10 minutes

### Document Version Upload

#### `POST /v1/document/version/upload/request`
Requests a presigned upload URL to upload a new version of an existing document.

**Request Body:**
```json
{
  "documentName": "original-document.pdf",
  "extension": "pdf"
}
```

**Parameters:**
- `documentName` (required): Name of the base document you're creating a version of
- `extension` (required): File extension for the new version (e.g., "pdf", "jpg", "png")

**Response:**
```json
{
  "upload_url": "https://minio:9000/documents/company-1234/70b30fbc-3856-4f2f-89cd-c1c5688ca7c9/20240822-1456-efgh.pdf?X-Amz-Algorithm=...",
  "version_key": "company-1234/70b30fbc-3856-4f2f-89cd-c1c5688ca7c9/20240822-1456-efgh.pdf",
  "base_document": "original-document.pdf"
}
```

**What to do with the response:**
1. Use the returned `upload_url` (presigned URL) to upload the new version directly to MinIO
2. Perform a PUT request to this URL with your file as the request body
3. The `version_key` shows the storage path for the new version
4. The system will automatically process this as a new document version

**Important Notes for All Endpoints:**
- All endpoints currently use hardcoded user and company IDs for development
- No authentication/authorization is implemented yet
- All presigned URLs have a 10-minute expiration time
- The document naming structure follows: `{company_id}/{user_id}/{timestamp}_{uuid}.{extension}`

## gRPC Messages

The service communicates with the monolith service using gRPC for database operations. The proto file defines the following service and messages:

### Service Definition

```protobuf
service DocumentIngest {
  rpc CreateDocument(CreateDocumentRequest) returns (CreateDocumentResponse);
  rpc CreateDocumentVersion(CreateDocumentVersionRequest) returns (CreateDocumentVersionResponse);
  rpc GetDocument(GetDocumentRequest) returns (GetDocumentResponse);
}
```

### Message Structures

#### CreateDocumentRequest
Used to create a new document record in the database.

```protobuf
message CreateDocumentRequest {
  string internal_filename = 1;     // Generated secure filename
  string mime = 2;                  // MIME type (e.g., "application/pdf")
  string storage_bucket = 3;        // MinIO bucket name (e.g., "documents")
  string storage_object_key = 4;    // Full object path in storage
  string created_by = 5;            // User UUID who uploaded the document
  google.protobuf.Timestamp created_at = 6; // Upload timestamp
}
```

#### CreateDocumentResponse
Response when creating a document record.

```protobuf
message CreateDocumentResponse {
  enum CreateStatus {
    CREATE_STATUS_UNSPECIFIED = 0;
    CREATED = 1;                    // Successfully created new document
    ALREADY_EXISTS = 2;             // Document already exists (idempotent)
    FAILED = 3;                     // Creation failed
  }
  CreateStatus status = 1;          // Operation result
  string row_id = 2;               // Database primary key of created document
  string message = 3;              // Optional human-readable message
}
```

#### CreateDocumentVersionRequest
Used to create a new version of an existing document.

```protobuf
message CreateDocumentVersionRequest {
  string document_id = 1;          // UUID of existing document
  uint32 version_number = 2;       // Version number (>= 1)
  string storage_version_id = 3;   // MinIO version ID
  string created_by = 4;           // User UUID who created this version
  google.protobuf.Timestamp created_at = 5; // Version creation timestamp
}
```

#### CreateDocumentVersionResponse
Response when creating a document version.

```protobuf
message CreateDocumentVersionResponse {
  CreateDocumentResponse.CreateStatus status = 1; // Operation result (reuses enum)
  string version_id = 2;           // Database primary key of created version
  string message = 3;              // Optional human-readable message
}
```

#### GetDocumentRequest
Used to retrieve a document by its internal filename.

```protobuf
message GetDocumentRequest {
  string internal_filename = 1;   // Filename to search for
}
```

#### GetDocumentResponse
Response when retrieving a document by filename.

```protobuf
message GetDocumentResponse {
  enum GetStatus {
    GET_STATUS_UNSPECIFIED = 0;
    FOUND = 1;                     // Document found successfully
    NOT_FOUND = 2;                 // Document not found
    FAILED = 3;                    // Retrieval failed
  }
  GetStatus status = 1;            // Operation result
  string document_id = 2;          // Document UUID if found
  string internal_filename = 3;    // Original filename
  string mime = 4;                 // MIME type
  string storage_bucket = 5;       // Storage bucket
  string storage_object_key = 6;   // Storage object key
  string created_by = 7;           // Creator UUID
  google.protobuf.Timestamp created_at = 8; // Creation timestamp
  string message = 9;              // Optional human-readable message
}
```

### When gRPC Messages Are Used

1. **Document Creation**: When a file is uploaded to MinIO, the service receives a MinIO event notification via RabbitMQ
2. **Automatic Processing**: The `handle_new_document_creation` event handler follows this flow:
   - `GetDocument` RPC to check if a document with the same internal_filename already exists
   - If document NOT found: calls `CreateDocument` RPC to create the document metadata record
   - If document IS found: skips document creation and uses existing document_id
   - Always calls `CreateDocumentVersion` RPC to create a new version record (version_number set to 1)
3. **Enhanced Logic**: The system now prevents duplicate document records by checking existence first
4. **Version Management**: Every upload creates a new version, regardless of whether the document already existed

### gRPC Connection Details
- **Target**: Configured via `MONOLITH_GRPC_TARGET` environment variable (default: `app:50061`)
- **Authentication**: Uses Bearer token in metadata (`authorization: Bearer <token>`)
- **Timeout**: 3 seconds per RPC call
- **Transport**: Insecure channel (TLS configuration available)

## Setup Instructions

Before running the service in Docker, you must complete the following setup steps:

### 1. Generate Protocol Buffer Files

The service uses gRPC for communication with the monolith service. You must generate the Python gRPC files from the proto definitions.

**Important**: Run this from the root of the document_service directory:

```bash
# Navigate to document_service root
cd document_service

# Make sure you're in the virtual environment
source venv/bin/activate

# Run the proto generation script
./scripts/generate_protos.sh
```

This script will:
- Create the `app/gen/` directory if it doesn't exist
- Generate `document_ingest_pb2.py` (message classes)
- Generate `document_ingest_pb2_grpc.py` (service stubs)

### 2. Fix Generated Import

After running the proto generation script, you **must manually fix** the import in the generated gRPC file:

**File**: `app/gen/document_ingest_pb2_grpc.py`

**Find this line:**
```python
import gen.document_ingest_pb2 as document__ingest__pb2
```

**Change it to:**
```python
import app.gen.document_ingest_pb2 as document__ingest__pb2
```

This fix is necessary because the generated import doesn't include the `app.` prefix required for the module structure.

### 3. Verify Generated Files

After completing steps 1-2, verify that these files exist:
- `app/gen/document_ingest_pb2.py`
- `app/gen/document_ingest_pb2_grpc.py`

### 4. Install Dependencies

Make sure all Python dependencies are installed:

```bash
pip install -r requirements.txt
```

## Docker Configuration

The service is designed to run in Docker. The `Dockerfile` includes:

1. Python 3.11 slim base image
2. Dependency installation
3. Full source code copy (including generated proto files)
4. Uvicorn server on port 8000

### Important Docker Notes

- **Proto files must be generated BEFORE building the Docker image**
- The container expects the `app/gen/` directory with generated proto files to exist
- Make sure to run the setup steps on your host machine before `docker build`

### Running with Docker Compose

The service integrates with the following dependencies:
- **MinIO**: Object storage for documents
- **RabbitMQ**: Message queue for MinIO event notifications  
- **Monolith**: Main application providing gRPC document service
- **MongoDB**: Document metadata storage (optional/legacy)
