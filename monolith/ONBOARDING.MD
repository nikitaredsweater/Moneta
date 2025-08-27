# Onboarding

This file will help you to quickly understand some core ideas that are a part of this service. If you do not need to investigate the code, and rather just understand the communication patterns, refer to [this MD file](README.MD).

## Table of Contents

- [Authentication Middleware](#authentication-middleware)
- [Endpoint Permissions](#endpoint-permissions)
- [Repository Pattern and Data Access](#repository-pattern-and-data-access)
- [gRPC Server Architecture](#grpc-server-architecture)
- [Schema Validation System](#schema-validation-system)
- [Exception Handling](#exception-handling)
- [Dual Protocol Architecture](#dual-protocol-architecture)

## Authentication Middleware

By default all of the endpoints will be protected by JWT. Calling any of them will automatically extract the user information and add it to the request. That information is needed for 2 things

1. Verify user has logged in
2. Used in endpoints where permission is required to perform an action (most of the endpoints)

That middleware can be found at [app/security/middleware/jwt_parsing.py](app/security/middleware/jwt_parsing.py).

### Whitelisting Routes

If you find that additional routes need to be available regardless of whether client is logged in or not, in the same file you can find a whitelist. It looks like this:

```python
EXCLUDED_PATH_PATTERNS = ['/', '/v1/auth/login', '/openapi.json', '/docs']
```

This whitelist supports wildcards and exact routes. For example, adding `/` route will only allow the home route to be accessed without a JWT token, but adding `/*` will whitelist all routes in the monolith service.

## Endpoint Permissions

Most of the endpoints are protected by the JWT token. These tokens contain information about the userID, which is then used to set the user object in context. Most of the routes can only be accessed when a user has sufficient permissions. Permissions mapping is static, and currently supports the following roles of users:

```python
class UserRole(str, Enum):
    ADMIN = 'ADMIN'
    BUYER = 'BUYER'
    SELLER = 'SELLER'
    ISSUER = 'ISSUER'
```

The definition of supported roles can be found in [app/enums/roles.py](app/enums/roles.py).

### Permissions Mapping

The list of permissions each role has is defined inside of [app/security/permissions.py](app/security/permissions.py). Here is that mapping:

```python
# Note:
#
# Current implementation limits the ability of 'dynamic' user permissions.
# Once you are assigned to a role, only way to get expanded permissions on the
# Platform for a specific user is to allow the whole role more permissions
# This may be the inteded behavior, but I am not sure.

ROLE_PERMISSIONS = {
    UserRole.ADMIN: {
        # Global data access
        (Verb.VIEW, Entity.ALL_DATA),
        # User management
        (Verb.VIEW, Entity.ALL_USERS),
        (Verb.CREATE, Entity.USER),
        (Verb.UPDATE, Entity.USER),
        (Verb.DELETE, Entity.ALL_USERS),
        # Role management
        (Verb.VIEW, Entity.ALL_ROLES),
        (Verb.ASSIGN, Entity.ROLE),
        # Company
        (Verb.VIEW, Entity.COMPANY),
        (Verb.CREATE, Entity.COMPANY),
        (Verb.UPDATE, Entity.COMPANY),
        (Verb.DELETE, Entity.COMPANY),
        # Company address
        (Verb.VIEW, Entity.COMPANY_ADDRESS),
        (Verb.CREATE, Entity.COMPANY_ADDRESS),
        (Verb.UPDATE, Entity.COMPANY_ADDRESS),
        (Verb.DELETE, Entity.COMPANY_ADDRESS),
    },
    UserRole.BUYER: {
        (Verb.VIEW, Entity.COMPANY),
        (Verb.VIEW, Entity.COMPANY_ADDRESS),
    },
    UserRole.SELLER: {
        (Verb.VIEW, Entity.COMPANY),
        (Verb.VIEW, Entity.COMPANY_ADDRESS),
    },
    UserRole.ISSUER: {
        (Verb.VIEW, Entity.COMPANY),
        (Verb.UPDATE, Entity.COMPANY),
        (Verb.VIEW, Entity.COMPANY_ADDRESS),
        (Verb.CREATE, Entity.COMPANY_ADDRESS),
        (Verb.UPDATE, Entity.COMPANY_ADDRESS),
        (Verb.DELETE, Entity.COMPANY_ADDRESS),
    },
}
```

### has_permission() Dependency Injection in Endpoints

Whenever adding a new endpoint, ensure to include the permission necessary via a dependency injection available at [app/security/permissions.py has_permission()](app/security/permissions.py).
This dependency requires the route to be JWT-protected.

## Repository Pattern and Data Access

**Most Frequently Used Component** - Understanding this pattern is crucial for working with any data in the system.

The repository pattern is implemented through the `BasePGRepository` class and is used extensively throughout the application. Here's how it works:

### Base Repository Structure

Located at [app/repositories/base.py](app/repositories/base.py), this is one of the most complex and critical parts of the system:

```python
class BasePGRepository(Generic[T]):
    """Base Posgtes Repository"""

    class Meta:
        response_model = BaseDTO
        orm_model = BaseEntity
        exclusion_fields: Optional[set]

    async def create(self, model: T) -> T:
        orm_model = self.to_orm(model)
        session: AsyncSession
        async with self.session() as session:
            async with session.begin():
                session.add(orm_model)
                await session.flush()
                await session.refresh(orm_model)
                return self.from_orm(orm_model)
```

### Key Features of the Repository Pattern

1. **Generic Type System**: Uses Python generics to provide type safety
2. **ORM Mapping**: Automatic conversion between Pydantic schemas and SQLAlchemy models
3. **Session Management**: Proper async session handling with context managers
4. **Complex Query Building**: Support for filtering, ordering, and pagination

### Most Used Repository Methods

```python
# Get all records with optional filtering
async def get_all(self, where_list=None, order_list=None) -> list[T]

# Get single record by ID
async def get_by_id(self, pk: MonetaID) -> Optional[T]

# Create new record
async def create(self, model: T) -> T

# Update existing record
async def update_by_id(self, pk: MonetaID, model: T) -> Optional[T]
```

### Repository Implementation Pattern

Each entity follows this pattern, as seen in [app/repositories/user.py](app/repositories/user.py):

```python
class UserRepository(BasePGRepository[schemas.User]):
    """User repository"""

    class Meta:
        response_model = schemas.UserInternal
        orm_model = models.User
        exclusion_fields = None

    async def get_by_email_exact(self, email: str) -> Optional[schemas.UserInternal]:
        """Custom method for email lookup"""
        return await self.get_one([self.Meta.orm_model.email == email])
```
The repository handles complex SQLAlchemy operations, transaction management, and provides a clean abstraction layer between business logic and database operations.

## gRPC Server Architecture

The system runs both FastAPI (HTTP REST) and gRPC servers simultaneously. The gRPC implementation is used for inner communication, between services of Moneta Financial backend. Currently, gRPC communication happens between document_service and monolith.

### Main gRPC Server

Located at [app/servers/grpc_server.py](app/servers/grpc_server.py):

```python
class DocumentIngestService(pbg.DocumentIngestServicer):
    async def CreateDocument(self, request: pb.CreateDocumentRequest, context):
        # Complex validation and type conversion
        created_by_uuid = _to_uuid(request.created_by)
        created_at_dt = _ts_to_datetime(request.created_at)

        # Business logic delegation
        doc = await save_document(...)
        return pb.CreateDocumentResponse(...)
```

### Service Layer Integration

The gRPC server delegates to service functions located at [app/services/grpc_document_service.py](app/services/grpc_document_service.py):

```python
async def save_document(
    internal_filename: str,
    mime: str,
    storage_bucket: str,
    storage_object_key: str,
    created_by_user_id: uuid.UUID,
    created_at: datetime,
) -> schemas.Document:
    # Business logic implementation
    document_repo = DocumentRepository(async_session)
    doc = await document_repo.create(new_doc)
    return doc
```

The gRPC server must handle protocol buffer serialization, type conversions, timezone-aware datetime handling, and proper error propagation across different protocols.

## Schema Validation System

**Foundation of Data Integrity** - Used in every endpoint for request/response validation.

The schema system uses Pydantic for data validation and is implemented across multiple layers:

### Schema Organization

- **Base Schemas**: [app/schemas/base.py](app/schemas/base.py) - Common base classes
- **Entity Schemas**: Individual entity schemas (user.py, company.py, etc.)

### Key Schema Patterns

```python
class BaseDTO(CamelModel):
    """Base schema with camelCase conversion"""
    id: MonetaID
    created_at: datetime
    updated_at: Optional[datetime] = None

class User(BaseDTO):
    """Full user schema"""
    email: str
    first_name: str
    last_name: str
    company_id: MonetaID
    role: UserRole  # Enum validation

class UserCreate(CamelModel):
    """Creation schema - no ID, different validation rules"""
    email: str
    first_name: str
    last_name: str
    password: str
    company_id: MonetaID
    role: UserRole
```

### Schema Features

1. **Automatic CamelCase Conversion**: `CamelModel` base class converts between snake_case (Python) and camelCase (JSON)
2. **Enum Validation**: Fields like `role` and `type` are validated against enum values
3. **Nested Validation**: Complex objects with proper validation chains
4. **Creation vs Full Schemas**: Different validation rules for creation vs retrieval

### Most Common Schema Types

```python
# Full entity schema (for responses)
class Entity(BaseDTO):
    field1: str
    field2: int

# Creation schema (for requests)
class EntityCreate(CamelModel):
    field1: str
    field2: int

# Update schema (for partial updates)
class EntityUpdate(CamelModel):
    field1: Optional[str] = None
    field2: Optional[int] = None
```

Every API request/response goes through schema validation, ensuring data integrity and proper serialization.

#### CamelModel vs BaseDTO
In essence, `CamelModel` and `BaseDTO` have the same functionality. The only difference is in the default fields that are set automatically on all entities that inherit the `BaseDTO`. These are:
1. id
2. created_at
These two fields are **not** present in the `CamelModel`

## Exception Handling

The system uses custom exceptions with consistent HTTP status codes and error messages.

### Exception Hierarchy

Located at [app/exceptions.py](app/exceptions.py):

```python
class BaseHTTPException(HTTPException):
    """Base exception class"""
    status_code: int = status.HTTP_400_BAD_REQUEST
    detail: str = ''

class WasNotFoundException(BaseHTTPException):
    """Entity not found"""
    status_code = status.HTTP_404_NOT_FOUND
    detail = 'Entity was not found'

class EntityAlreadyExistsException(BaseHTTPException):
    """Entity already exists"""
    status_code = status.HTTP_409_CONFLICT
    detail = 'Entity with such unique fields already exists'

class InvalidCredentialsException(BaseHTTPException):
    """Invalid login credentials"""
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = 'Invalid credentials'
```

### Common Exception Patterns

```python
# In endpoint handlers
existing_user = await user_repo.get_by_email_exact(user_data.email)
if existing_user:
    raise EntityAlreadyExistsException

company = await company_repo.get_by_id(user_data.company_id)
if not company:
    raise WasNotFoundException(
        detail=f'Company with ID {user_data.company_id} does not exist'
    )
```

### Exception Usage in Endpoints

Most endpoints follow this pattern:

1. **Validation**: Check required entities exist
2. **Uniqueness**: Verify unique constraints
3. **Authorization**: Check permissions
4. **Execution**: Perform business logic with try/catch
5. **Error Handling**: Raise appropriate exceptions

## Dual Protocol Architecture

### Application Startup

Located at [app/main.py](app/main.py):

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    global grpc_server
    # Create and start gRPC server
    grpc_server = grpc.aio.server()
    pbg.add_DocumentIngestServicer_to_server(
        DocumentIngestService(), grpc_server
    )
    grpc_server.add_insecure_port('[::]:50061')
    await grpc_server.start()
    try:
        yield  # <-- HTTP (FastAPI) runs while gRPC is running
    finally:
        # Graceful shutdown
        if grpc_server:
            await grpc_server.stop(grace=5)

app = FastAPI(lifespan=lifespan)
app.add_middleware(JWTAuthMiddleware)  # JWT for HTTP
app.include_router(app_router)        # HTTP routes
```
### Shared Components

Both protocols share:

- **Business Logic**: Service layer functions
- **Data Access**: Repository classes
- **Validation**: Schema definitions
- **Configuration**: Environment variables and settings

## Key Takeaways for Developers

### Most Complex Areas (Focus on Understanding):

1. **gRPC Server Implementation** - Protocol buffer handling and type conversions
2. **Repository Base Class** - Complex SQLAlchemy operations and session management
3. **Dual Protocol Architecture** - Coordinating HTTP and gRPC servers
4. **Permission System** - Role-based access control with dependency injection

### Most Frequently Used Patterns:

1. **Repository Pattern** - Every data operation goes through repositories
2. **Schema Validation** - Every request/response uses schemas
3. **Permission Dependencies** - Most endpoints require permission checks
4. **Exception Handling** - Consistent error responses across all endpoints

### Development Workflow:

1. **Define Schemas** → Create request/response models
2. **Implement Repository** → Extend BasePGRepository for data access
3. **Add Business Logic** → Create service functions if needed
4. **Create Endpoint** → Add FastAPI route with validation and permissions
5. **Handle Errors** → Use appropriate exceptions for error cases

This architecture provides a robust, scalable foundation for the financial platform while maintaining clean separation of concerns and comprehensive validation.
