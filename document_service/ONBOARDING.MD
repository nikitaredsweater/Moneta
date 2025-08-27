# Onboarding

This file will help you to quickly understand some core ideas that are a part of this service. If you do not need to investigate the code, and rather just understand the communication patterns, refer to [this MD file](README.MD).

## Table of Contents

- [Project Structure Overview](#project-structure-overview)
- [Event-Driven Architecture](#event-driven-architecture)
- [Document Upload Flow](#document-upload-flow)
- [gRPC Communication](#grpc-communication)
- [Storage Integration](#storage-integration)
- [Database Layer](#database-layer)
- [Schema Validation System](#schema-validation-system)
- [Exception Handling](#exception-handling)

## Project Structure Overview

Understanding the folder hierarchy is crucial for navigating the codebase efficiently. Here's a comprehensive overview of the document_service project structure:

### Root Level Structure

```
document_service/
├── app/                     # Main application code
├── proto/                   # Protocol buffer definitions
├── scripts/                 # Utility scripts
├── venv/                    # Virtual environment (created during setup)
├── __pycache__/            # Python bytecode cache
├── requirements.txt         # Python dependencies
├── requirements.in          # Dependency source definitions
├── Dockerfile              # Docker container definition
├── alembic.ini             # Alembic configuration (for migrations)
├── pytest.ini              # Testing configuration
├── setup.cfg               # Package configuration
├── .gitignore              # Git ignore rules
└── LICENSE                  # Project license
```

### App Directory Structure

```
app/
├── __init__.py            # Package initialization
├── main.py                # Application entry point with RabbitMQ consumer
├── config.py              # Configuration settings
├── api/                   # REST API routes
│   ├── __init__.py
│   └── v1/                # Version 1 API routes
│       ├── __init__.py
│       ├── routes/        # Individual endpoint handlers
│       │   ├── __init__.py
│       │   ├── document.py # Document upload/download endpoints
│       │   └── health.py   # Health check endpoint
├── clients/               # External service clients
│   ├── __init__.py
│   ├── minio_client.py    # MinIO object storage client
│   ├── monolith_grpc_client.py # gRPC client for monolith
│   └── pika_client.py     # RabbitMQ client
├── database/              # Database layer
│   └── mongo.py          # MongoDB connection and operations
├── enums/                 # Enumeration definitions
│   ├── __init__.py
│   └── document_types.py  # Document type classifications
├── gen/                   # Generated gRPC code
│   ├── __pycache__/
│   ├── document_ingest_pb2_grpc.py
│   └── document_ingest_pb2.py
├── handlers/              # Event handlers
│   ├── __init__.py
│   └── minio/             # MinIO event handlers
│       ├── __init__.py
│       ├── event_handlers/
│       │   └── object_created.py # Handles file upload events
│       └── registry.py    # Event handler registry
├── schemas/               # Pydantic data models
│   ├── __init__.py
│   ├── base.py            # Base schema classes
│   └── document.py        # Document-related schemas
├── services/              # Business logic layer
│   ├── __init__.py
│   ├── monolith_grpc_document_service.py
│   └── storage_service.py # MinIO storage operations
├── utils/                 # Utility functions
│   ├── __init__.py
│   ├── file_upload.py     # File upload utilities
│   └── minio_event_parsing.py # MinIO event parsing
└── workers/               # Background workers
    └── __init__.py
```

### Folder Purpose Overview

#### **Core Application Folders**

**`app/`** - Contains all application source code

- **`main.py`** - FastAPI application with RabbitMQ consumer startup
- **`config.py`** - Environment-based configuration for MongoDB and other services
- **`api/`** - REST API endpoints for document operations

**`handlers/`** - Event-driven architecture handlers

- **`minio/event_handlers/`** - Processes MinIO object creation events
- **`registry.py`** - Registers event handlers with decorators

**`clients/`** - External service integrations

- **`minio_client.py`** - MinIO object storage operations
- **`monolith_grpc_client.py`** - gRPC communication with monolith service
- **`pika_client.py`** - RabbitMQ message queue operations

**`services/`** - Business logic layer

- **`storage_service.py`** - MinIO presigned URL generation
- **`monolith_grpc_document_service.py`** - Document metadata operations

#### **Supporting Folders**

**`database/`** - NoSQL database layer

- **`mongo.py`** - MongoDB connection and CRUD operations

**`enums/`** - Document classification system

- **`document_types.py`** - Document type enums (USER_DOCUMENT, COMPANY_DOCUMENT, etc.)

**`gen/`** - Generated protocol buffer code

- Auto-generated from `.proto` files using protoc

**`schemas/`** - Data validation models

- Pydantic schemas for request/response validation
- **`base.py`** - Common base classes
- **`document.py`** - Document-specific schemas

**`utils/`** - Shared utility functions

- **`file_upload.py`** - File upload helper functions
- **`minio_event_parsing.py`** - Parse MinIO webhook events

**`proto/`** - Protocol buffer definitions

- `.proto` files defining gRPC service interfaces

**`scripts/`** - Development utilities

- **`generate_protos.sh`** - Generate Python code from proto files

### The Importance of `__init__.py` Files

**`__init__.py` files are crucial for Python package management and development:**

#### **Package Recognition**

```python
# Without __init__.py, Python treats directories as regular folders
# With __init__.py, Python recognizes them as packages

from app.api.v1.routes.document import document_router  # ✅ Works
# vs.
from app.api.v1.routes import document  # ❌ Fails without __init__.py
```

#### **Import Organization**

- **`__init__.py` files control what gets imported** when using `from package import *`
- **They serve as package documentation** with module docstrings
- **They can re-export important classes/functions** for cleaner imports

#### **Development Benefits**

1. **IDE Support**: Enables proper autocomplete and navigation
2. **Testing**: Allows proper test discovery and module mocking
3. **Namespace Management**: Prevents naming conflicts between modules
4. **Code Organization**: Makes the project structure explicit and navigable
5. **Import Flexibility**: Enables both specific imports and wildcard imports

#### **Common Patterns in This Project**

```python
# app/api/v1/__init__.py
from .routes import document_router

# app/schemas/__init__.py
from .document import DocumentUploadRequest, DocumentAccessRequest

# app/enums/__init__.py
from .document_types import DocumentType
```

**Without `__init__.py` files:**

- Import statements would be longer and more complex
- IDE autocomplete wouldn't work properly
- Testing frameworks couldn't discover modules
- The package structure would be implicit rather than explicit

**With `__init__.py` files:**

- Clean, readable import statements
- Full IDE support for navigation and refactoring
- Proper test discovery and mocking
- Explicit package boundaries and organization

### Key Takeaways for Navigation

1. **Follow the event flow**: HTTP requests → MinIO events → RabbitMQ → Handlers → gRPC calls
2. **`__init__.py` files make the structure explicit** - they define what's importable
3. **Event-driven architecture**: MinIO events trigger document processing
4. **Dual storage approach**: Files in MinIO, metadata in both MongoDB and PostgreSQL
5. **gRPC for service communication**: Communicates with monolith for document metadata

This structure provides a robust foundation for the document service while maintaining clean separation of concerns and event-driven processing.

## Event-Driven Architecture

**Most Complex and Unique Feature** - The document service uses an event-driven architecture unlike traditional request-response services.

### RabbitMQ Integration

Located at [app/main.py](app/main.py), the service starts both FastAPI and RabbitMQ consumer:

```python
app = FastAPI()
app.include_router(app_router)

# RabbitMQ connection settings
RABBIT_URL = os.getenv('CELERY_BROKER_URL', 'amqp://guest:guest@rabbitmq:5672/')
EXCHANGE_NAME = 'minio-events'
ROUTING_KEY = 'document_tasks'

@app.on_event('startup')
async def startup_event():
    logger.info('FastAPI startup event triggered')
    client = PikaClient(on_minio_message)  # New handler
    logger.info('Created PikaClient, starting consumer...')
    asyncio.create_task(client.consume())
```

### Event Processing Flow

1. **File Upload**: User uploads file to MinIO via presigned URL
2. **MinIO Event**: MinIO sends event to RabbitMQ exchange
3. **Event Consumption**: Document service consumes event from queue
4. **Processing**: Event handler processes the file metadata
5. **gRPC Communication**: Service communicates with monolith to store document metadata
6. **Completion**: Both services updated with document information

### Event Handler Registration

Located at [app/handlers/minio/registry.py](app/handlers/minio/registry.py):

```python
def handles(event_type: str):
    """Decorator to register event handlers"""
    def decorator(func):
        if event_type not in HANDLERS:
            HANDLERS[event_type] = []
        HANDLERS[event_type].append(func)
        return func
    return decorator
```

### MinIO Object Created Handler

Located at [app/handlers/minio/event_handlers/object_created.py](app/handlers/minio/event_handlers/object_created.py):

```python
@handles('s3:ObjectCreated:Put')
async def handle_new_document_creation(event: MinIOEvent, raw: dict) -> None:
    # Complex event processing logic
    async with MonolithGrpcClient(metadata=[('authorization', 'Bearer <token>')]) as client:
        # Check if document exists
        get_resp = await client.get_document(internal_filename=internal_filename)

        if get_resp.status == get_resp.GetStatus.FOUND:
            # Create new version
            document_id = get_resp.document_id
        else:
            # Create new document first
            doc_resp = await client.save_document(...)

        # Always create version
        version_resp = await client.save_document_version(...)
```

**Why it's complex**: The event-driven architecture requires understanding of:

- RabbitMQ message patterns and routing
- MinIO webhook events and their structure
- Asynchronous event processing
- Dual-write operations (MinIO + PostgreSQL via gRPC)
- Error handling in distributed systems

## Document Upload Flow

**Core Business Logic** - Understanding the document upload process is essential for working with this service.

### Two-Step Upload Process

#### Step 1: Request Upload URL

Located at [app/api/v1/routes/document.py](app/api/v1/routes/document.py):

```python
@document_router.post('/upload/request')
async def request_upload_link(document_data: DocumentUploadRequest):
    # Generate secure key for new document
    key = generate_secure_key(
        user_id=HARDCODED_USER_ID,
        extension=document_data.extension,
        company_id=HARDCODED_COMPANY_ID,
    )

    # Create upload URL in MinIO
    upload_url = generate_presigned_upload_url(key)
    return {'key': upload_url}
```

#### Step 2: Automatic Processing

When the file is uploaded to MinIO, the event-driven system automatically processes it:

```python
# MinIO sends event to RabbitMQ
# Document service consumes event
# Handler processes the file and creates metadata
# gRPC call to monolith stores document info
```

### Document Access

Located at [app/api/v1/routes/document.py](app/api/v1/routes/document.py):

```python
@document_router.post('/access/request')
async def request_access_link(document_data: DocumentAccessRequest):
    # Create full object key
    key = f'{HARDCODED_COMPANY_ID}/{HARDCODED_USER_ID}/{document_data.document_name}'

    # Generate download URL
    download_url = generate_presigned_download_url(key)
    return {'access_url': download_url}
```

### Key Generation Logic

Located at [app/utils/file_upload.py](app/utils/file_upload.py):

```python
def generate_secure_key(user_id: str, extension: str, company_id: str) -> str:
    """Generate secure object key for MinIO storage"""
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    uuid_part = str(uuid.uuid4())[:8]
    return f'{company_id}/{user_id}/{timestamp}-{uuid_part}.{extension}'
```

**Why it's important**: The two-step process ensures secure file uploads while maintaining metadata consistency across services.

## gRPC Communication

**Service-to-Service Communication** - The document service communicates with the monolith via gRPC for document metadata operations.

### gRPC Client Architecture

Located at [app/clients/monolith_grpc_client.py](app/clients/monolith_grpc_client.py):

```python
class MonolithGrpcClient:
    """Async gRPC client for monolith's DocumentIngest service"""

    async def save_document(
        self,
        *,
        internal_filename: str,
        mime: str,
        storage_bucket: str,
        storage_object_key: str,
        created_by: str,
        created_at: Optional[datetime] = None,
    ) -> pb.CreateDocumentResponse:
        # Protocol buffer conversion and RPC call
        ts = Timestamp()
        ts.FromDatetime(created_at)

        req = pb.CreateDocumentRequest(
            internal_filename=internal_filename,
            mime=mime,
            storage_bucket=storage_bucket,
            storage_object_key=storage_object_key,
            created_by=created_by,
            created_at=ts,
        )

        return await self._stub.CreateDocument(req, metadata=self.metadata)
```

### Context Manager Pattern

The client uses async context managers for proper resource management:

```python
async with MonolithGrpcClient(metadata=[('authorization', 'Bearer <token>')]) as client:
    resp = await client.save_document(
        internal_filename='file-123.pdf',
        mime='application/pdf',
        storage_bucket='documents',
        storage_object_key='user_docs/u-123/file-123.pdf',
        created_by='70b30fbc-3856-4f2f-89cd-c1c5688ca7c9',
    )
```

### Protocol Buffer Types

Located at [proto/document_ingest.proto](proto/document_ingest.proto):

```protobuf
service DocumentIngest {
  rpc CreateDocument(CreateDocumentRequest) returns (CreateDocumentResponse);
  rpc CreateDocumentVersion(CreateDocumentVersionRequest) returns (CreateDocumentVersionResponse);
  rpc GetDocument(GetDocumentRequest) returns (GetDocumentResponse);
}

message CreateDocumentRequest {
  string internal_filename = 1;
  string mime = 2;
  string storage_bucket = 3;
  string storage_object_key = 4;
  string created_by = 5;
  google.protobuf.Timestamp created_at = 6;
}
```

**Why it's important**: gRPC enables efficient, type-safe communication between the document service and monolith for document metadata operations.

## Storage Integration

**File Storage Layer** - The service integrates with MinIO for object storage operations.

### MinIO Client Configuration

Located at [app/clients/minio_client.py](app/clients/minio_client.py):

```python
from minio import Minio

minio_client = Minio(
    endpoint=os.getenv('MINIO_ENDPOINT', 'minio:9000'),
    access_key=os.getenv('MINIO_ACCESS_KEY', 'minioadmin'),
    secret_key=os.getenv('MINIO_SECRET_KEY', 'minioadmin'),
    secure=False,  # For development
)
```

### Presigned URL Generation

Located at [app/services/storage_service.py](app/services/storage_service.py):

```python
def generate_presigned_upload_url(key: str) -> str:
    """Returns URL for uploading files to MinIO bucket"""
    bucket_name = 'documents'
    expires = timedelta(minutes=10)

    url = minio_client.presigned_put_object(
        bucket_name=bucket_name,
        object_name=key,
        expires=expires,
    )
    return url

def generate_presigned_download_url(key: str) -> str:
    """Returns URL for downloading files from MinIO bucket"""
    bucket_name = 'documents'
    expires = timedelta(minutes=10)

    url = minio_client.presigned_get_object(
        bucket_name=bucket_name,
        object_name=key,
        expires=expires,
    )
    return url
```

### Event Parsing

Located at [app/utils/minio_event_parsing.py](app/utils/minio_event_parsing.py):

```python
class MinIOEvent:
    """Parsed MinIO event data"""
    def __init__(self, event_data: dict):
        self.bucket_name = event_data['Records'][0]['s3']['bucket']['name']
        self.object_key = event_data['Records'][0]['s3']['object']['key']
        self.event_name = event_data['Records'][0]['eventName']
        self.event_time_dt = datetime.fromisoformat(
            event_data['Records'][0]['eventTime'].replace('Z', '+00:00')
        )
```

**Why it's important**: MinIO integration provides scalable object storage with event-driven processing capabilities.

## Database Layer

**NoSQL Document Storage** - The service uses MongoDB for document metadata storage.

### MongoDB Configuration

Located at [app/config.py](app/config.py):

```python
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://mongo:27017/')
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'document_service')
MONGO_COLLECTION = os.getenv('MONGO_COLLECTION', 'documents')
```

### MongoDB Operations

Located at [app/database/mongo.py](app/database/mongo.py):

```python
from pymongo import MongoClient

client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]
collection = db[MONGO_COLLECTION]

def insert_document(doc: dict) -> str:
    """Insert document and return ID"""
    result = collection.insert_one(doc)
    return str(result.inserted_id)

def update_document(query: dict, update_data: dict):
    """Update document by query"""
    collection.update_one(query, {'$set': update_data})

def get_document(query: dict) -> dict:
    """Retrieve document by query"""
    return collection.find_one(query)
```

**Why it's important**: MongoDB provides flexible document storage for document metadata while the monolith uses PostgreSQL for relational document data.

## Schema Validation System

**Data Integrity Layer** - Pydantic schemas ensure data validation and serialization.

### Schema Organization

- **Base Schemas**: [app/schemas/base.py](app/schemas/base.py) - Common base classes
- **Document Schemas**: [app/schemas/document.py](app/schemas/document.py) - Document-specific validation

### Document Schemas

Located at [app/schemas/document.py](app/schemas/document.py):

```python
from pydantic import BaseModel
from app.enums import DocumentType

class DocumentUploadRequest(BaseModel):
    """Schema for document upload requests"""
    document_type: DocumentType
    extension: str

class DocumentAccessRequest(BaseModel):
    """Schema for document access requests"""
    document_name: str

class DocumentVersionUploadRequest(BaseModel):
    """Schema for version upload requests"""
    document_name: str
    extension: str
```

### Document Types Enum

Located at [app/enums/document_types.py](app/enums/document_types.py):

```python
class DocumentType(str, Enum):
    USER_DOCUMENT = 'USER_DOCUMENT'
    COMPANY_DOCUMENT = 'COMAPNY_DOCUMENT'  # Note: Typo in original
    INSTRUMENT_RAW_DOCUMENT = 'INSTRUMENT_RAW_DOCUMENT'
    INSTRUMENT_PROCESSED_DOCUMENT = 'INSTRUMENT_PROCESSED_DOCUMENT'
```

**Why it's important**: Schemas ensure type safety and proper data validation for all API interactions.

## Exception Handling

**Error Management** - The service uses standard Python exceptions and FastAPI error handling.

### FastAPI Error Responses

The service relies on FastAPI's built-in exception handling for HTTP errors and uses standard Python exceptions for internal errors.

### Common Exception Patterns

```python
# In event handlers
try:
    # gRPC operations
    resp = await client.save_document(...)
except Exception as e:
    logger.error('Error creating document: %s', e)
    return

# In API endpoints
# FastAPI automatically converts exceptions to HTTP responses
# Custom validation errors are handled by Pydantic
```

**Why it's important**: Proper exception handling ensures reliable operation in the event-driven architecture.

## Key Takeaways for Developers

### Most Complex Areas (Focus on Understanding):

1. **Event-Driven Architecture** - RabbitMQ and MinIO event processing
2. **gRPC Communication** - Protocol buffer handling and service communication
3. **Dual Storage Systems** - Coordinating MinIO (files) and PostgreSQL (metadata)
4. **Asynchronous Processing** - Event handlers and async context managers

### Most Frequently Used Patterns:

1. **Schema Validation** - Every request/response uses Pydantic schemas
2. **gRPC Client Usage** - All metadata operations go through gRPC
3. **Presigned URLs** - File upload/download uses MinIO presigned URLs
4. **Event Handler Registration** - Decorators for MinIO event processing

### Development Workflow:

1. **Define Schemas** → Create Pydantic models for requests/responses
2. **Add API Endpoints** → Create FastAPI routes with proper validation
3. **Implement Event Handlers** → Add MinIO event processing logic
4. **Test gRPC Communication** → Verify communication with monolith
5. **Handle Errors** → Ensure proper exception handling in async contexts

### Architecture Flow:

```
User Request → FastAPI → MinIO Presigned URL → User Uploads File →
MinIO Event → RabbitMQ → Document Service Consumer →
Event Handler → gRPC Call → Monolith Database → Response
```

This architecture provides a scalable, event-driven foundation for document management while maintaining data consistency across distributed services.
