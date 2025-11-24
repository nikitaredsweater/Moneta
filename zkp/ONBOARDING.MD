# Onboarding

This file will help you to quickly understand some core ideas that are a part of this service.

## Table of Contents

- [Project Structure Overview](#project-structure-overview)
- [Development Workflow](#development-workflow)

## Project Structure Overview

Understanding the folder hierarchy is crucial for navigating the codebase efficiently.

### Root Level Structure

```
new_microservice/
├── app/                     # Main application code
├── proto/                   # Protocol buffer definitions
├── scripts/                 # Utility scripts
├── Dockerfile              # Docker container definition
├── environment.config.example # Environment variables template
├── requirements.txt        # Python dependencies
└── README.MD               # Service documentation
```

### App Directory Structure

```
app/
├── main.py                # Application entry point
├── config.py              # Configuration settings
├── api/                   # REST API routes
│   ├── v1/                # Version 1 API routes
│   │   └── routes/        # Individual endpoint handlers
│   │       └── health.py  # Health check endpoint
├── schemas/               # Pydantic data models
│   ├── base.py            # Base schema classes
│   └── health.py          # Health-specific schemas
└── services/              # Business logic layer
```

## Development Workflow

1. **Make changes** to the code
2. **Test locally** using `./scripts/run_dev.sh`
3. **Follow coding standards** (black, isort, flake8, mypy)
4. **Add tests** for new functionality
5. **Update documentation** as needed

## Key Takeaways for Developers

1. **Follow the existing patterns** established in the codebase
2. **Use the provided schemas** for request/response validation
3. **Keep business logic** in the services layer
4. **Document your changes** in the README.MD
