# 🚀 Moneta Microservice Template

This document serves as the definitive guide for creating new microservices within the Moneta backend ecosystem. It establishes the standard structure, patterns, and best practices that all microservices should follow.

## Table of Contents

- [Overview](#overview)
- [Required Files & Structure](#required-files--structure)
- [FastAPI Setup Guide](#fastapi-setup-guide)
- [Development Workflow](#development-workflow)
- [Best Practices](#best-practices)
- [Integration Patterns](#integration-patterns)
- [Script Template](#script-template)

## Overview

All Moneta microservices follow a consistent architecture that emphasizes:

- **Separation of Concerns** - Clear boundaries between layers
- **Event-Driven Design** - Asynchronous processing where appropriate
- **Type Safety** - Pydantic schemas and proper typing
- **Service Communication** - gRPC for service-to-service calls
- **Observability** - Health checks, logging, and monitoring
- **Testing** - Comprehensive test coverage

## Required Files & Structure

### Root Directory Structure

```
microservice_name/
├── app/                          # Main application code
├── proto/                        # Protocol buffer definitions
├── scripts/                      # Utility scripts
├── Dockerfile                    # Docker container definition
├── environment.config.example    # Environment variables template
├── requirements.in               # Abstract dependencies
├── requirements.txt              # Pinned dependencies
├── pytest.ini                    # Testing configuration
├── setup.cfg                     # Package configuration
├── alembic.ini                   # Database migration config (if needed)
├── README.MD                     # Service documentation
├── ONBOARDING.MD                 # Developer onboarding guide
└── .gitignore                    # Git ignore rules
```

### App Directory Structure

```
app/
├── __init__.py                 # Package initialization
├── main.py                     # FastAPI application entry point
├── config.py                   # Configuration management
├── dependencies.py             # FastAPI dependency injection
├── api/                        # REST API layer
│   ├── __init__.py
│   └── v1/                     # API version namespace
│       ├── __init__.py
│       ├── routes/             # Endpoint definitions
│       │   ├── __init__.py
│       │   ├── health.py       # Health check endpoint
│       │   └── domain.py       # Domain-specific endpoints
│       └── dependencies.py     # API-specific dependencies
├── clients/                    # External service clients
│   ├── __init__.py
│   └── monolith_grpc_client.py # gRPC client for monolith
├── database/                   # Database layer (if needed)
│   └── connection.py           # Database connection management
├── enums/                      # Enumeration definitions
│   ├── __init__.py
│   └── domain_types.py         # Domain-specific enums
├── handlers/                   # Event handlers (if event-driven)
│   ├── __init__.py
│   └── event_type/             # Event-specific handlers
│       ├── __init__.py
│       ├── event_handlers/
│       │   └── event_created.py
│       └── registry.py
├── schemas/                    # Pydantic data models
│   ├── __init__.py
│   ├── base.py                 # Base schema classes
│   └── domain.py               # Domain-specific schemas
├── services/                   # Business logic layer
│   ├── __init__.py
│   └── domain_service.py       # Domain business logic
├── utils/                      # Utility functions
│   ├── __init__.py
│   └── helpers.py              # Helper functions
└── workers/                    # Background workers (if needed)
    └── __init__.py
```

### Purpose of Each Folder

#### **Root Level Folders**

- **`app/`** - Contains all application source code following the layered architecture
- **`proto/`** - Protocol buffer definitions for gRPC communication
- **`scripts/`** - Utility scripts for development, deployment, and maintenance

#### **App Directory Folders**

- **`main.py`** - FastAPI application factory and startup logic
- **`config.py`** - Environment-based configuration management
- **`dependencies.py`** - FastAPI dependency injection providers
- **`api/`** - REST API endpoints organized by version
- **`clients/`** - External service integrations (gRPC, message queues, etc.)
- **`database/`** - Database connection and ORM management (if service needs database)
- **`enums/`** - Strongly-typed enumerations for domain values
- **`handlers/`** - Event-driven processing handlers (if service is event-driven)
- **`schemas/`** - Pydantic models for request/response validation
- **`services/`** - Business logic layer implementing domain rules
- **`utils/`** - Shared utility functions and helpers
- **`workers/`** - Background job processors (if needed)

### Required Files

#### **Core Application Files**

- `app/main.py` - FastAPI application entry point
- `app/config.py` - Configuration management
- `app/api/v1/routes/health.py` - Health check endpoint
- `requirements.in` & `requirements.txt` - Dependency management
- `Dockerfile` - Container definition
- `environment.config.example` - Environment template

#### **Package Management**

- `app/__init__.py` - Package initialization
- All `__init__.py` files in subdirectories for proper package structure

#### **Documentation**

- `README.MD` - Service documentation and API reference
- `ONBOARDING.MD` - Developer onboarding guide

#### **Development Tools**

- `pytest.ini` - Testing configuration
- `setup.cfg` - Development tool configuration
- `.gitignore` - Git ignore rules

## FastAPI Setup Guide

### 1. Project Initialization

```bash
# Create project directory
mkdir new_microservice
cd new_microservice

# Initialize virtual environment
python3 -m venv venv
source venv/bin/activate

# Create initial project structure
mkdir -p app/api/v1/routes
mkdir -p app/schemas
mkdir -p app/services
mkdir -p scripts
mkdir -p proto

# Create required __init__.py files
touch app/__init__.py
touch app/api/__init__.py
touch app/api/v1/__init__.py
touch app/api/v1/routes/__init__.py
touch app/schemas/__init__.py
touch app/services/__init__.py
```

### 2. Dependencies Setup

#### **requirements.in** (Abstract Dependencies)

```txt
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
python-dotenv>=1.0.0
httpx>=0.25.0
structlog>=23.1.0
```

#### **requirements.txt** (Pinned Versions)

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
python-dotenv==1.0.0
httpx==0.25.2
structlog==23.2.0
```

#### **Install Dependencies**

```bash
# Install from pinned requirements
pip install -r requirements.txt

# For development, also install dev dependencies
pip install black isort flake8 mypy pytest pre-commit
```

### 3. Core Application Setup

#### **app/config.py**

```python
from typing import Optional
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Application
    app_name: str = "New Microservice"
    app_version: str = "1.0.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # External Services
    monolith_grpc_target: str = "app:50061"

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
```

#### **app/main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from app.api.v1.routes import health_router
from app.config import settings

# Configure structured logging
logger = structlog.get_logger()


def create_application() -> FastAPI:
    """Create and configure FastAPI application"""

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health_router, prefix="/v1", tags=["health"])

    @app.on_event("startup")
    async def startup_event():
        logger.info("Starting microservice", service=settings.app_name)

    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Shutting down microservice", service=settings.app_name)

    return app


app = create_application()
```

### 4. Health Check Endpoint

#### **app/api/v1/routes/health.py**

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import time

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    timestamp: float
    service: str
    version: str


@router.get("/health", response_model=HealthResponse)
async def health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "new_microservice",
        "version": "1.0.0"
    }
```

#### **app/api/v1/routes/**init**.py**

```python
from .health import router as health_router

__all__ = ["health_router"]
```

### 5. Schema Definitions

#### **app/schemas/base.py**

```python
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class BaseSchema(BaseModel):
    """Base schema with common configuration"""

    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        populate_by_name=True,
    )


class TimestampedSchema(BaseSchema):
    """Schema with timestamp fields"""

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
```

### 6. Service Layer

#### **app/services/base_service.py**

```python
from typing import Generic, TypeVar, Optional, List
from abc import ABC, abstractmethod
import structlog

T = TypeVar('T')
logger = structlog.get_logger()


class BaseService(ABC):
    """Base service class with common functionality"""

    def __init__(self):
        self.logger = logger.bind(service=self.__class__.__name__)

    @abstractmethod
    async def create(self, data: dict) -> T:
        """Create a new resource"""
        pass

    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[T]:
        """Get resource by ID"""
        pass

    @abstractmethod
    async def get_all(self) -> List[T]:
        """Get all resources"""
        pass

    @abstractmethod
    async def update(self, id: str, data: dict) -> Optional[T]:
        """Update resource"""
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Delete resource"""
        pass
```

### 7. gRPC Client Setup (if needed)

#### **app/clients/monolith_grpc_client.py**

```python
from typing import Optional, List
import grpc
import structlog
from google.protobuf.timestamp_pb2 import Timestamp
from datetime import datetime

# Import generated proto classes
# from app.gen import document_ingest_pb2 as pb
# from app.gen import document_ingest_pb2_grpc as pb_grpc

logger = structlog.get_logger()


class MonolithGrpcClient:
    """gRPC client for monolith service communication"""

    def __init__(self, target: str = "app:50061", metadata: Optional[List[tuple]] = None):
        self.target = target
        self.metadata = metadata or []
        self._channel: Optional[grpc.Channel] = None
        self._stub = None

    async def __aenter__(self):
        """Async context manager entry"""
        self._channel = grpc.aio.insecure_channel(self.target)
        # self._stub = pb_grpc.DocumentIngestStub(self._channel)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._channel:
            await self._channel.close()

    def _datetime_to_timestamp(self, dt: datetime) -> Timestamp:
        """Convert datetime to protobuf timestamp"""
        ts = Timestamp()
        ts.FromDatetime(dt)
        return ts
```

### 8. Docker Configuration

#### **Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/v1/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 9. Environment Configuration

#### **environment.config.example**

```bash
# Application Configuration
APP_NAME=New Microservice
APP_VERSION=1.0.0
DEBUG=false

# Server Configuration
HOST=0.0.0.0
PORT=8000

# External Services
MONOLITH_GRPC_TARGET=app:50061

# Logging
LOG_LEVEL=INFO

# Database (if needed)
DATABASE_URL=postgresql://user:password@db:5432/dbname

# Message Queue (if needed)
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
```

### 10. Development Tools Configuration

#### **pytest.ini**

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
```

#### **setup.cfg**

```ini
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = .git,__pycache__,build,dist,venv

[isort]
profile = black
multi_line_output = 3
line_length = 88
known_first_party = app

[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = True
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_unreachable = True
strict_equality = True

[tool:black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'
extend-exclude = '''
/(
    \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | _build
  | buck-out
  | build
  | dist
)/
'''

[tool:bandit]
exclude_dirs = ["venv", "tests"]
skips = ["B101", "B601"]
```

### 11. Utility Scripts

#### **scripts/run_dev.sh**

```bash
#!/bin/bash
# Development server runner

set -e

# Activate virtual environment
source venv/bin/activate

# Run with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### **scripts/generate_protos.sh** (if using gRPC)

```bash
#!/bin/bash
# Generate Python code from proto files

set -e

# Create gen directory if it doesn't exist
mkdir -p app/gen

# Generate Python files from proto definitions
python -m grpc_tools.protoc \
    --proto_path=proto \
    --python_out=app/gen \
    --grpc_python_out=app/gen \
    proto/*.proto

echo "Proto files generated successfully!"
```

## Development Workflow

### 1. **Project Setup**

```bash
# Clone template or create from scratch
# Follow FastAPI Setup Guide sections 1-3

# Copy environment template
cp environment.config.example .env

# Install dependencies
pip install -r requirements.txt

# Run initial setup
./scripts/generate_protos.sh  # If using gRPC
```

### 2. **Development Cycle**

```bash
# Run development server
./scripts/run_dev.sh

# Run tests
pytest

# Format code
black app/
isort app/

# Lint code
flake8 app/
mypy app/

# Run security checks
bandit -r app/
```

### 3. **Adding New Features**

#### **API Endpoint Pattern**

```python
# 1. Create schema in app/schemas/
# 2. Create service method in app/services/
# 3. Create route handler in app/api/v1/routes/
# 4. Register router in app/api/v1/routes/__init__.py
# 5. Add to main app in app/main.py
```

#### **Event Handler Pattern** (if event-driven)

```python
# 1. Define event schema in app/schemas/
# 2. Create handler in app/handlers/domain/event_handlers/
# 3. Register handler in app/handlers/registry.py
# 4. Configure event source (RabbitMQ, etc.)
```

### 4. **Database Integration** (if needed)

```python
# 1. Add database dependencies to requirements.in
# 2. Create database models in app/models/
# 3. Configure connection in app/database/
# 4. Add Alembic configuration for migrations
# 5. Create repositories in app/repositories/
```

### 5. **Testing Strategy**

```python
# Unit tests for services
# Integration tests for API endpoints
# Event handler tests for async processing
# gRPC client tests for external communication
```

## Best Practices

### **Code Organization**

- Keep `__init__.py` files minimal and focused
- Use absolute imports throughout the codebase
- Follow naming conventions (snake_case for functions/variables, PascalCase for classes)
- Group related functionality in dedicated modules

### **Error Handling**

```python
# Use custom exceptions for business logic errors
# Implement proper HTTP status codes
# Log errors with appropriate context
# Use FastAPI's built-in exception handlers
```

### **Logging**

```python
# Use structured logging with context
# Include relevant IDs and metadata
# Log at appropriate levels (DEBUG, INFO, WARNING, ERROR)
# Use correlation IDs for request tracing
```

### **Configuration**

```python
# Use Pydantic settings for configuration
# Validate configuration at startup
# Support environment variable overrides
# Document all configuration options
```

### **Security**

```python
# Validate all input data with Pydantic
# Implement proper authentication/authorization
# Use HTTPS in production
# Sanitize logs and error messages
# Implement rate limiting where appropriate
```

## Integration Patterns

### **Communication with Monolith**

- Use gRPC for synchronous service-to-service communication
- Implement proper error handling and timeouts
- Use metadata for authentication and tracing
- Follow established proto patterns

### **Event-Driven Communication**

- Use RabbitMQ for asynchronous event processing
- Implement proper message serialization
- Handle message delivery failures gracefully
- Use dead letter queues for unprocessable messages

### **Database Patterns**

- Use repositories for data access abstraction
- Implement proper transaction management
- Use migrations for schema changes
- Follow established naming conventions

### **API Design**

- Use RESTful conventions
- Implement proper HTTP status codes
- Provide comprehensive API documentation
- Version APIs appropriately
- Implement pagination for list endpoints

This template provides a solid foundation for building maintainable, scalable microservices within the Moneta ecosystem. All new microservices should follow these patterns and structures to ensure consistency and maintainability across the platform.

## Script Template

In order to speed up the process of the development, use the script to generate the boilerplate.

```bash
cd scripts/
chmod +x create_microservice.sh
cd ../
./scripts/create_microservice.sh <microservice_name>
```
