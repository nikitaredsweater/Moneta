# 🚀 Moneta Backend Project Onboarding Guide

Welcome to the Moneta Backend Project! This comprehensive guide will help you understand our microservices architecture, development workflow, and best practices.

## 📋 Table of Contents

- [🏗️ Project Overview](#️-project-overview)
- [🐍 Development Environment Setup](#️-development-environment-setup)
- [📦 Dependency Management with pip-tools](#-dependency-management-with-pip-tools)
- [🐳 Docker Development Environment](#-docker-development-environment)
- [🌐 Service URLs & Access Points](#-service-urls--access-points)
- [🗄️ Database Setup & Migrations](#️-database-setup--migrations)
- [🔐 Authentication & JWT Setup](#-authentication--jwt-setup)
- [🔍 Code Quality & Pre-commit Hooks](#-code-quality--pre-commit-hooks)
- [🌳 Git Workflow & Branching Strategy](#-git-workflow--branching-strategy)
- [📝 Pull Request Guidelines](#-pull-request-guidelines)
- [🧠 Best Practices & Tips](#-best-practices--tips)
- [📁 Service-Specific Documentation](#-service-specific-documentation)

---

## 🏗️ Project Overview

The Moneta Backend is a **microservices architecture** built with modern Python technologies, consisting of two main services:

### **🏛️ Monolith Service**

- **Technology**: FastAPI, PostgreSQL, SQLAlchemy
- **Purpose**: Core business logic, user management, company data, financial instruments
- **Features**:
  - REST API with automatic OpenAPI documentation
  - JWT-based authentication and authorization
  - Role-based access control (Admin, Buyer, Seller, Issuer)
  - Database migrations with Alembic
  - gRPC server for inter-service communication

### **📄 Document Service**

- **Technology**: FastAPI, MongoDB, RabbitMQ, MinIO
- **Purpose**: Document upload, storage, and processing
- **Features**:
  - Event-driven architecture with RabbitMQ
  - File storage with MinIO (S3-compatible)
  - Automatic document processing via webhooks
  - gRPC client for communicating with monolith
  - Presigned URL generation for secure uploads

### **🔧 Supporting Infrastructure**

- **PostgreSQL**: Primary relational database for business data
- **MongoDB**: Document metadata storage
- **RabbitMQ**: Message queue for event-driven processing
- **MinIO**: Object storage for documents
- **Redis**: Caching and session management

### **🏛️ Architecture Benefits**

1. **Scalability**: Services can be scaled independently
2. **Technology Diversity**: Each service uses the best tool for its job
3. **Event-Driven Processing**: Document uploads trigger automatic processing
4. **Data Consistency**: Dual-write patterns ensure data integrity across services
5. **API Documentation**: Automatic OpenAPI/Swagger documentation

---

## 🐍 Development Environment Setup

### ✅ Requirements

- **Python 3.8 or later**
- **Terminal/Command Line**
- **Code editor** like VS Code (recommended)
- **Docker and Docker Compose** (for containerized development)
- **Git** for version control

### 🐍 Step 1: Clone and Set Up Virtual Environment

```bash
# Clone the repository
git clone <repository-url>
cd moneta-backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 📥 Step 2: Install Dependencies

We use **pip-tools** for dependency management to ensure reproducible environments.

---

## 📦 Dependency Management with pip-tools

### Why pip-tools?

**pip-tools** helps manage dependency versions cleanly by separating:

- **`requirements.in`**: Abstract dependencies (what you need)
- **`requirements.txt`**: Pinned versions (exact versions to install)

### Step-by-Step Setup

#### Step 2.1: Install pip-tools

```bash
pip install pip-tools
```

#### Step 2.2: Install from requirements.txt

```bash
# For monolith service
cd monolith
pip install -r requirements.txt

# For document service
cd ../document_service
pip install -r requirements.txt
```

#### Step 2.3: Adding New Dependencies

When adding new dependencies:

```bash
# Edit requirements.in
echo "new-package>=1.0.0" >> requirements.in

# Compile to requirements.txt
pip-compile requirements.in

# Install updated dependencies
pip install -r requirements.txt
```

#### Step 2.4: Updating Dependencies

```bash
# Update all dependencies to latest compatible versions
pip-compile --upgrade requirements.in

# Update specific package
pip-compile --upgrade-package package-name requirements.in

# Install updated dependencies
pip install -r requirements.txt
```

### 📋 requirements.in Structure

Both services follow this pattern:

```txt
fastapi
uvicorn

# --- Database ---
sqlalchemy
alembic
psycopg[binary]
asyncpg

# --- Testing ---
pytest
pytest-asyncio

# --- Formatters & Linters ---
isort
black
flake8
pylint
mypy

# --- Pre-commit ---
pre-commit

# --- Service-specific ---
# monolith: python-jose, bcrypt, grpcio
# document: minio, pymongo, aio-pika
```

### 🔧 Environment Variables

Create `.env` files for each service:

```bash
# Copy template
cp monolith/environment.config.example monolith/.env
cp document_service/environment.config.example document_service/.env

# Edit with your local settings
```

---

## 🐳 Docker Development Environment

Docker provides consistent development environments across all machines.

### 🏗️ Docker Services Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Monolith      │    │  Document       │    │     MinIO       │
│   Service       │◄──►│   Service       │    │   (S3-like)     │
│                 │    │                 │    │                 │
│ • PostgreSQL DB │    │ • MongoDB       │    │ • File Storage  │
│ • JWT Auth      │    │ • RabbitMQ      │    │ • Webhooks      │
│ • REST API      │    │ • Event-driven  │    │ • Presigned URLs│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │    RabbitMQ     │
                    │   Message Bus   │
                    └─────────────────┘
```

### 🚀 Docker Commands

#### **Development Mode** (Default)

```bash
# Start all services in development mode
docker-compose up --build

# Start in background
docker-compose up -d --build

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f app
docker-compose logs -f document_service
docker-compose logs -f minio
```

#### **Production Mode**

```bash
# Start with production configuration
TARGET=production docker-compose up --build app
```

#### **Service-Specific Commands**

```bash
# Start only monolith service
docker-compose up --build app

# Start only document service
docker-compose up --build document_service

# Start only infrastructure (databases, queues)
docker-compose up postgres mongodb rabbitmq minio redis

# Access service containers
docker-compose exec app bash
docker-compose exec document_service bash
docker-compose exec postgres psql -U postgres -d moneta
docker-compose exec mongodb mongo
```

#### **Database Operations**

```bash
# Access PostgreSQL (monolith)
docker-compose exec postgres psql -U postgres -d moneta

# Access MongoDB (document service)
docker-compose exec mongodb mongo

# Run database migrations
docker-compose exec app alembic upgrade head
```

#### **MinIO Operations**

```bash
# Access MinIO management console
docker-compose exec mc mc alias set localminio http://minio:9000 minioadmin minioadmin

# Create documents bucket
docker-compose exec mc mc mb localminio/documents

# Configure MinIO events for RabbitMQ
docker-compose exec mc sh -c '\
  mc alias set localminio http://minio:9000 minioadmin minioadmin && \
  mc admin config set localminio notify_amqp:1 \
    enable=on \
    url=amqp://rabbitmq:5672 \
    exchange=minio-events \
    exchangeType=direct \
    routingKey=document_tasks \
    format=json && \
  mc admin service restart localminio \
'
```

#### **Cleanup Commands**

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (⚠️  DESTROYS DATA)
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Clean everything
docker-compose down -v --rmi all --remove-orphans
```

### 🐛 Docker Troubleshooting

#### **Common Issues**

1. **Port conflicts**: Change ports in docker-compose.yml
2. **Permission issues**: Ensure Docker has proper permissions
3. **Memory issues**: Increase Docker memory allocation
4. **Database connection**: Wait for health checks to pass

#### **Debug Commands**

```bash
# Check service health
docker-compose ps

# View service logs
docker-compose logs service_name

# Restart specific service
docker-compose restart service_name

# Rebuild specific service
docker-compose up --build service_name
```

---

## 🌐 Service URLs & Access Points

When running with Docker, services are accessible at these local URLs:

### **🏛️ Monolith Service**

- **API Base URL**: `http://localhost:8080`
- **Swagger Documentation**: `http://localhost:8080/docs`
- **ReDoc Documentation**: `http://localhost:8080/redoc`

### **📄 Document Service**

- **API Base URL**: `http://localhost:8081`
- **Swagger Documentation**: `http://localhost:8081/docs`
- **ReDoc Documentation**: `http://localhost:8081/redoc`
- **Health Check**: `http://localhost:8081/v1/health`

### **🗄️ Databases**

- **PostgreSQL**: `localhost:5432` (User: `postgres`, Password: `postgres`)
- **MongoDB**: `localhost:27017` (No auth by default)

### **📦 Object Storage**

- **MinIO Console**: `http://localhost:9001`
- **MinIO API**: `http://localhost:9000`
- **Credentials**: `minioadmin` / `minioadmin`

### **📨 Message Queue**

- **RabbitMQ Management**: `http://localhost:15672`
- **Credentials**: `guest` / `guest`
- **AMQP Port**: `localhost:5672`

### **⚡ Cache & Session**

- **Redis**: `localhost:6379` (No password by default)

### Environment Configuration

Update your `.env` files:

```bash
# monolith/.env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/moneta
JWT_PRIVATE_KEY_PATH=app/keys/jwt_private.pem
JWT_PUBLIC_KEY_PATH=app/keys/jwt_public.pem
MONOLITH_GRPC_TARGET=app:50061

# document_service/.env
MONGO_URI=mongodb://localhost:27017/
RABBIT_URL=amqp://guest:guest@localhost:5672/
MINIO_ENDPOINT=localhost:9000
```

---

## 🔍 Code Quality & Pre-commit Hooks

### Automated Code Quality Tools

We use comprehensive code quality checks:

- **Code Formatting**: `black` and `isort`
- **Linting**: `flake8`, `pylint`
- **Type Checking**: `mypy`
- **Security**: `bandit`
- **Pre-commit Hooks**: Automated checks before commits

### Setup Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run on all files (first time setup)
pre-commit run --all-files

# Manual quality checks
black .                  # Format code
isort .                  # Sort imports
flake8 .                 # Lint code
mypy .                   # Type check
bandit -r .              # Security scan
```

### Pre-commit Configuration

Our `.pre-commit-config.yaml` includes:

- **trailing-whitespace**: Remove trailing whitespace
- **end-of-file-fixer**: Ensure files end with newline
- **check-yaml**: Validate YAML files
- **check-added-large-files**: Prevent large files
- **black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking
- **bandit**: Security scanning

### Skipping Pre-commit (Use Sparingly)

```bash
# Skip all checks for this commit
git commit --no-verify -m "commit message"

# Skip specific hooks
SKIP=black,isort git commit -m "commit message"
```

---

## 🌳 Git Workflow & Branching Strategy

### Branch Structure

```
main (protected)
├── dev (integration branch)
│   ├── feature/user-authentication
│   ├── feature/payment-integration
│   ├── fix/login-validation-bug
│   ├── hotfix/critical-security-patch
│   └── release/v1.2.3
```

### Branch Descriptions

#### 🏭 `main` Branch

- **Production-ready code**
- **Protected branch** - requires PR review
- **Automatic deployment** to production

#### 🔧 `dev` Branch

- **Integration branch** for all new features
- **Default target** for feature and fix branches
- **Must always be deployable**

#### 🎯 Feature Branches (`feature/*`)

- **New functionality development**
- **Naming**: `feature/ticket-name` or `feature/description`
- **Workflow**: Create from `dev`, merge back to `dev`

#### 🐛 Fix Branches (`fix/*`)

- **Bug fixes and minor improvements**
- **Naming**: `fix/ticket-name` or `fix/description`
- **Workflow**: Create from `dev`, merge back to `dev`

#### 🚨 Hotfix Branches (`hotfix/*`)

- **Critical production issues**
- **Naming**: `hotfix/ticket-name` or `hotfix/description`
- **Workflow**: Create from `main`, merge to both `main` and `dev`

#### 📦 Release Branches (`release/*`)

- **Release preparation and final testing**
- **Naming**: `release/v1.2.3` or `release/sprint-name`
- **Workflow**: Create from `dev`, merge to both `main` and `dev`

### Standard Development Workflow

#### Step 1: Start from Dev Branch

```bash
git checkout dev
git pull origin dev
```

#### Step 2: Create Feature Branch

```bash
# For new features
git checkout -b feature/user-authentication

# For bug fixes
git checkout -b fix/login-validation-error

# For hotfixes (from main)
git checkout main
git pull origin main
git checkout -b hotfix/critical-security-patch
```

#### Step 3: Develop and Commit

```bash
# Make changes...
git add .
git commit -m "feat: add user authentication endpoint"
```

#### Step 4: Push and Create Pull Request

```bash
git push origin feature/user-authentication
# Create PR via GitHub/GitLab interface
```

### Commit Message Convention

Follow **Conventional Commits** specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

#### Commit Types

- **`feat`**: New feature
- **`fix`**: Bug fix
- **`docs`**: Documentation changes
- **`style`**: Code style changes
- **`refactor`**: Code refactoring
- **`test`**: Adding/updating tests
- **`chore`**: Maintenance tasks

#### Examples

```bash
git commit -m "feat: add user registration endpoint"
git commit -m "fix: resolve validation error in login form"
git commit -m "docs: update API documentation"
git commit -m "refactor: optimize database queries"
git commit -m "test: add unit tests for payment processing"
```

### Branch Protection Rules

#### Protected Branches

- **`main`**: Requires PR review, passing CI/CD
- **`dev`**: Requires passing CI/CD checks

#### Pull Request Requirements

- **Code review** required before merge
- **CI/CD checks** must pass
- **Up-to-date** with base branch
- **Descriptive title** and body

---

## 📝 Pull Request Guidelines

### Pull Request Template

Use this template for all pull requests:

```markdown
## Description

Brief description of changes and what problem this solves.

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring
- [ ] Performance improvement
- [ ] Security enhancement

## Testing

- [ ] All existing tests pass
- [ ] New tests added (if applicable)
- [ ] Manual testing completed
- [ ] Integration tests pass

## Checklist

- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated (if needed)
- [ ] Database migrations included (if applicable)
- [ ] Environment variables documented (if added)

## Additional Notes

Any additional context, breaking changes, or deployment notes.
```

### Work in Progress (WIP)

For incomplete work, prefix PR title with `[WIP]`:

```
[WIP] feature/user-authentication - Add OAuth integration
```

### Ready for Review

When work is complete:

1. Remove `[WIP]` prefix
2. Ensure all tests pass
3. Update documentation
4. Request review from team members

---

## 🧠 Best Practices & Tips

### Development Tips

1. **Always activate virtual environment** before working
2. **Use pre-commit hooks** - don't skip them unless necessary
3. **Test both services** - changes to one may affect the other
4. **Use meaningful commit messages** - follow conventional commits
5. **Keep branches small** - focus on one feature/fix per branch

### Dependency Management

```bash
# When adding dependencies
echo "new-package>=1.0.0" >> requirements.in
pip-compile requirements.in
pip install -r requirements.txt

# When updating dependencies
pip-compile --upgrade requirements.in
pip install -r requirements.txt
```

### Docker Development

```bash
# Start fresh environment
docker-compose down -v
docker-compose up --build

# View logs efficiently
docker-compose logs -f app | head -50
docker-compose logs -f document_service | head -50
```

### Database Best Practices

```bash
# Always backup before migrations
pg_dump moneta > backup.sql

# Test migrations on development first
alembic upgrade head --sql  # Show SQL without executing

# Rollback if needed
alembic downgrade -1
```

### API Testing

```bash
# Test APIs with curl
curl http://localhost:8080/health
curl http://localhost:8081/health

# Or use Swagger UI
open http://localhost:8080/docs
open http://localhost:8081/docs
```

---

## 📁 Service-Specific Documentation

### 🏛️ Monolith Service

- **ONBOARDING.md**: `monolith/ONBOARDING.md`
- **README.md**: `monolith/README.md`
- **Key Areas**:
  - JWT authentication middleware
  - Repository pattern implementation
  - gRPC server for document service communication
  - Role-based permission system
  - Database migrations with Alembic

### 📄 Document Service

- **ONBOARDING.md**: `document_service/ONBOARDING.md`
- **README.md**: `document_service/README.md`
- **Key Areas**:
  - Event-driven architecture with RabbitMQ
  - MinIO integration for file storage
  - Document upload/download workflows
  - gRPC client for monolith communication
  - MongoDB for metadata storage

### 🔧 Development Scripts

Both services include helpful scripts:

- **Protocol buffer generation**: `./scripts/generate_protos.sh`
- **Environment setup**: Check `environment.config.example`
- **Docker configuration**: `Dockerfile` and `docker-compose.yml`

---

## 🎯 Quick Start Checklist

- [ ] Clone repository
- [ ] Set up virtual environment
- [ ] Install dependencies with pip-tools
- [ ] Start Docker services
- [ ] Configure environment variables
- [ ] Generate JWT keys
- [ ] Run database migrations
- [ ] Set up MinIO-RabbitMQ integration
- [ ] Install pre-commit hooks
- [ ] Test APIs are accessible
- [ ] Create your first feature branch

---

## 📞 Need Help?

1. **Check service-specific documentation** first
2. **Review existing issues** in the repository
3. **Ask in team communication channels**
4. **Check Docker logs** for infrastructure issues
5. **Verify environment variables** are correctly set

### Common Issues

#### **Port Conflicts**

```bash
# Find what's using the port
lsof -i :8080

# Change Docker port mapping in docker-compose.yml
ports:
  - "8081:8080"  # Change 8080 to 8081
```

#### **Database Connection Issues**

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Restart database service
docker-compose restart postgres

# Check database logs
docker-compose logs postgres
```

#### **MinIO-RabbitMQ Integration**

```bash
# Verify MinIO events are configured
docker-compose exec mc mc event list localminio/documents

# Restart MinIO after configuration changes
docker-compose exec mc mc admin service restart localminio
```

Happy coding! 🐍🚀

---

_This guide is maintained by the Moneta Backend Team. Please update it as the project evolves._
