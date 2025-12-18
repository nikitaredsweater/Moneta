# Logging Standards and Guidelines

This document outlines the logging standards, formats, and best practices for the Moneta platform. All logging across the application should adhere to these rules for consistency, maintainability, and effective debugging.

## Table of Contents

- [Configuration](#configuration)
- [Logging Levels](#logging-levels)
- [Log Message Format](#log-message-format)
- [Component Tags](#component-tags)
- [What to Log](#what-to-log)
- [When to Log](#when-to-log)
- [Sensitive Data Handling](#sensitive-data-handling)
- [Performance Thresholds](#performance-thresholds)
- [Implementation Examples](#implementation-examples)

---

## Configuration

Logging is configured through environment variables in the `.env` file. The configuration is loaded automatically when the application starts.

### Environment Variables

| Variable | Description | Options | Default |
|----------|-------------|---------|---------|
| `LOG_LEVEL` | Logging verbosity level | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` | `INFO` |
| `LOG_OUTPUT` | Where to send log output | `console`, `file`, `both` | `console` |
| `LOG_FILE_PATH` | Path to log file | Any valid file path | `logs/moneta.log` |

### Example Configuration

```bash
# .env file

# Logging Configuration
LOG_LEVEL="INFO"           # Set to DEBUG for development
LOG_OUTPUT="console"       # Use "both" for production
LOG_FILE_PATH="logs/moneta.log"
```

### Recommended Settings by Environment

| Environment | LOG_LEVEL | LOG_OUTPUT | Notes |
|-------------|-----------|------------|-------|
| Development | `DEBUG` | `console` | Full verbosity in terminal |
| Testing | `WARNING` | `console` | Reduce noise during tests |
| Staging | `INFO` | `both` | Console + file for debugging |
| Production | `INFO` | `file` or `both` | Persistent logs for auditing |

### File Logging Features

When `LOG_OUTPUT` is set to `file` or `both`:

- **Automatic Directory Creation**: The log directory is created if it doesn't exist
- **Log Rotation**: Files rotate at 10MB with 5 backup files retained
- **Rotated Files**: Named `moneta.log.1`, `moneta.log.2`, etc.

---

## Logging Levels

Python's logging module provides five standard levels. Use them as follows:

| Level | Value | Usage | Production |
|-------|-------|-------|------------|
| **DEBUG** | 10 | Detailed diagnostic information | Usually disabled |
| **INFO** | 20 | Confirmation that things work as expected | Primary level |
| **WARNING** | 30 | Something unexpected but handled | Always enabled |
| **ERROR** | 40 | Serious problem preventing operation completion | Always enabled |
| **CRITICAL** | 50 | System-wide failure, unrecoverable state | Always enabled |

### DEBUG (10)
Use for detailed diagnostic information during development and troubleshooting.

**Examples:**
- Request body contents
- Query parameters being processed
- Entry into functions with parameters
- Intermediate calculation results

```python
logger.debug('[BUSINESS] Fetching user | user_id=%s', user_id)
logger.debug('[BUSINESS] Searching companies | limit=%d | offset=%d', filters.limit, filters.offset)
```

### INFO (20)
Use for confirmation that operations completed successfully.

**Examples:**
- Request completion
- Successful entity creation/update/deletion
- Successful authentication
- Operation results with counts

```python
logger.info('[BUSINESS] User created | user_id=%s | email=%s', user.id, user.email)
logger.info('[BUSINESS] Company search completed | results=%d', len(companies))
```

### WARNING (30)
Use when something unexpected happened but the system handled it gracefully.

**Examples:**
- Entity not found (404 responses)
- Permission denied (403 responses)
- Entity already exists (409 responses)
- Slow queries or requests
- Approaching resource limits
- Deprecated feature usage

```python
logger.warning('[BUSINESS] User not found | user_id=%s', user_id)
logger.warning('[BUSINESS] Forbidden delete attempt | user_id=%s | requester_company=%s', user_id, company_id)
logger.warning('[RESPONSE] Slow request | path=%s | duration_ms=%.2f', path, duration_ms)
```

### ERROR (40)
Use when a serious problem prevented an operation from completing.

**Examples:**
- Failed database operations
- External service failures
- Unhandled exceptions in business logic
- Very slow requests (performance degradation)

```python
logger.error('[BUSINESS] Failed to create user | email=%s | error_type=%s | error=%s', email, type(e).__name__, str(e))
logger.error('[RESPONSE] Very slow request | path=%s | duration_ms=%.2f', path, duration_ms)
```

### CRITICAL (50)
Use for severe system-level issues that may prevent the program from running.

**Examples:**
- Database connection pool exhausted
- Authentication service unavailable
- Data corruption detected
- Unhandled exceptions at middleware level

```python
logger.critical('[SYSTEM] Database connection failed | error=%s', str(e))
logger.critical('[RESPONSE] Unhandled exception | path=%s | error_type=%s', path, type(e).__name__)
```

---

## Log Message Format

All log messages must follow this standardized format:

```
[COMPONENT] Action description | key1=value1 | key2=value2
```

### Format Rules

1. **Component Tag**: Always start with a component tag in square brackets
2. **Action Description**: Brief, clear description of what happened
3. **Key-Value Pairs**: Separated by ` | ` (space-pipe-space)
4. **No Trailing Punctuation**: Don't end messages with periods

### Examples

```
[REQUEST] Started | request_id=abc123 | method=GET | path=/v1/companies
[RESPONSE] Completed | request_id=abc123 | status=200 | duration_ms=45.23
[BUSINESS] User created | user_id=uuid-here | email=user@example.com
[AUTH] Login successful | user_id=uuid-here
[DATABASE] Query executed | table=companies | operation=SELECT | rows=10
```

---

## Component Tags

Use these standardized component tags to categorize log messages:

| Tag | Usage |
|-----|-------|
| `[REQUEST]` | Incoming HTTP request information |
| `[RESPONSE]` | Outgoing HTTP response information |
| `[BUSINESS]` | Business logic operations (CRUD, validations, workflows) |
| `[AUTH]` | Authentication and authorization events |
| `[DATABASE]` | Database operations and queries |
| `[EXTERNAL]` | External service calls (APIs, gRPC, etc.) |
| `[SYSTEM]` | System-level events (startup, shutdown, configuration) |

---

## What to Log

### Always Log

| Event | Level | Required Fields |
|-------|-------|-----------------|
| Request start | INFO | request_id, method, path, client_ip |
| Request completion | INFO/WARN/ERROR | request_id, status, duration_ms |
| Entity created | INFO | entity_id, entity_type, key identifiers |
| Entity updated | INFO | entity_id, updated_by |
| Entity deleted | INFO | entity_id, deleted_by |
| Entity not found | WARNING | entity_id, entity_type |
| Permission denied | WARNING | user_id, attempted_action, reason |
| Validation failure | WARNING | field, reason |
| Operation failure | ERROR | operation, error_type, error_message |
| System startup/shutdown | INFO | component, status |

### Log at DEBUG Level Only

- Full request/response bodies
- Request/response headers
- Function entry with all parameters
- Intermediate state during complex operations
- SQL queries (if needed for debugging)

### Never Log

- Passwords or password hashes
- API keys or tokens (full values)
- Credit card numbers (show last 4 only)
- Personal identification numbers (SSN, etc.)
- Private keys or secrets
- Session tokens

---

## When to Log

### Endpoint Lifecycle

```python
@router.get('/{entity_id}')
async def get_entity(entity_id: MonetaID, repo: Repository):
    # 1. DEBUG: Entry point with parameters
    logger.debug('[BUSINESS] Fetching entity | entity_id=%s', entity_id)

    entity = await repo.get_by_id(entity_id)

    if not entity:
        # 2. WARNING: Not found
        logger.warning('[BUSINESS] Entity not found | entity_id=%s', entity_id)
        raise WasNotFoundException

    # 3. INFO: Success
    logger.info('[BUSINESS] Entity retrieved | entity_id=%s', entity_id)
    return entity
```

### Create Operations

```python
@router.post('/')
async def create_entity(data: CreateSchema, repo: Repository, current_user):
    # DEBUG: Entry with key fields (not sensitive data)
    logger.debug('[BUSINESS] Creating entity | name=%s | created_by=%s', data.name, current_user.id)

    # Check for conflicts
    existing = await repo.get_by_unique_field(data.unique_field)
    if existing:
        # WARNING: Conflict
        logger.warning('[BUSINESS] Entity already exists | field=%s', data.unique_field)
        raise EntityAlreadyExistsException

    try:
        entity = await repo.create(data)
        # INFO: Success with created entity ID
        logger.info('[BUSINESS] Entity created | entity_id=%s | name=%s', entity.id, entity.name)
        return entity
    except Exception as e:
        # ERROR: Creation failed
        logger.error('[BUSINESS] Failed to create entity | error_type=%s | error=%s', type(e).__name__, str(e))
        raise
```

### Update Operations

```python
@router.patch('/{entity_id}')
async def update_entity(entity_id: MonetaID, data: UpdateSchema, repo: Repository, current_user):
    # DEBUG: Entry
    logger.debug('[BUSINESS] Updating entity | entity_id=%s | requested_by=%s', entity_id, current_user.id)

    entity = await repo.get_by_id(entity_id)
    if not entity:
        # WARNING: Not found
        logger.warning('[BUSINESS] Entity not found for update | entity_id=%s', entity_id)
        raise WasNotFoundException

    # Check permissions
    if entity.owner_id != current_user.company_id:
        # WARNING: Forbidden
        logger.warning('[BUSINESS] Forbidden update attempt | entity_id=%s | owner=%s | requester=%s',
                      entity_id, entity.owner_id, current_user.company_id)
        raise ForbiddenException

    updated = await repo.update_by_id(entity_id, data)
    # INFO: Success
    logger.info('[BUSINESS] Entity updated | entity_id=%s | updated_by=%s', entity_id, current_user.id)
    return updated
```

### Delete Operations

```python
@router.delete('/{entity_id}')
async def delete_entity(entity_id: MonetaID, repo: Repository, current_user):
    # DEBUG: Entry
    logger.debug('[BUSINESS] Deleting entity | entity_id=%s | requested_by=%s', entity_id, current_user.id)

    entity = await repo.get_by_id(entity_id)
    if not entity:
        # WARNING: Not found
        logger.warning('[BUSINESS] Entity not found for deletion | entity_id=%s', entity_id)
        raise WasNotFoundException

    await repo.delete_by_id(entity_id)
    # INFO: Success
    logger.info('[BUSINESS] Entity deleted | entity_id=%s | deleted_by=%s', entity_id, current_user.id)
    return entity
```

### Search Operations

```python
@router.post('/search')
async def search_entities(filters: FilterSchema, repo: Repository):
    # DEBUG: Entry with filter summary
    logger.debug('[BUSINESS] Searching entities | limit=%d | offset=%d', filters.limit, filters.offset)

    results = await repo.get_all(...)

    # INFO: Success with count
    logger.info('[BUSINESS] Search completed | results=%d', len(results))
    return results
```

---

## Sensitive Data Handling

### Masking Functions

Use these utilities from `app.utils.logging_config`:

```python
from app.utils.logging_config import mask_sensitive_value, mask_authorization_header

# Mask general sensitive values (shows last 4 chars)
masked = mask_sensitive_value("1234567890")  # "******7890"

# Mask authorization headers
masked = mask_authorization_header("Bearer eyJhbG...")  # "Bearer ***..."
```

### What to Mask

| Data Type | Masking Rule | Example |
|-----------|--------------|---------|
| Authorization headers | Show type only | `Bearer ***...` |
| API keys | Last 4 characters | `****abcd` |
| Credit cards | Last 4 digits | `****1234` |
| Emails (DEBUG only) | Domain only | `***@example.com` |
| Tokens | Truncate | `***...` |

---

## Performance Thresholds

The middleware automatically logs warnings/errors based on these thresholds:

| Metric | Warning Threshold | Error Threshold |
|--------|-------------------|-----------------|
| Request duration | > 1000ms | > 5000ms |
| Database query | > 500ms | - |
| External API call | > 2000ms | - |
| Response size | > 1MB | - |

These thresholds are defined in `app/utils/logging_config.py`:

```python
SLOW_REQUEST_THRESHOLD_MS = 1000
VERY_SLOW_REQUEST_THRESHOLD_MS = 5000
SLOW_QUERY_THRESHOLD_MS = 500
SLOW_EXTERNAL_CALL_THRESHOLD_MS = 2000
LARGE_RESPONSE_THRESHOLD_BYTES = 1024 * 1024  # 1MB
```

---

## Implementation Examples

### Setting Up Logger in a Module

```python
import logging

logger = logging.getLogger(__name__)
```

Always use `__name__` to create module-specific loggers. This enables:
- Hierarchical logger configuration
- Per-module log level control
- Clear identification of log source

### Complete Endpoint Example

```python
"""
User endpoints
"""

import logging
from typing import List, Optional

from app import repositories as repo
from app import schemas
from app.exceptions import WasNotFoundException, ForbiddenException
from fastapi import APIRouter, Depends

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get('/{user_id}', response_model=schemas.User)
async def get_user(
    user_id: schemas.MonetaID,
    user_repo: repo.User,
) -> schemas.User:
    """Get a user by ID."""
    logger.debug('[BUSINESS] Fetching user | user_id=%s', user_id)

    user = await user_repo.get_by_id(user_id)

    if not user:
        logger.warning('[BUSINESS] User not found | user_id=%s', user_id)
        raise WasNotFoundException

    logger.info('[BUSINESS] User retrieved | user_id=%s', user_id)
    return user


@router.post('/', response_model=schemas.User)
async def create_user(
    user_data: schemas.UserCreate,
    user_repo: repo.User,
) -> schemas.User:
    """Create a new user."""
    logger.debug('[BUSINESS] Creating user | email=%s', user_data.email)

    # Check for existing user
    existing = await user_repo.get_by_email_exact(user_data.email)
    if existing:
        logger.warning('[BUSINESS] User already exists | email=%s', user_data.email)
        raise EntityAlreadyExistsException

    try:
        user = await user_repo.create(user_data)
        logger.info('[BUSINESS] User created | user_id=%s | email=%s', user.id, user.email)
        return user
    except Exception as e:
        logger.error(
            '[BUSINESS] Failed to create user | email=%s | error_type=%s | error=%s',
            user_data.email,
            type(e).__name__,
            str(e),
        )
        raise
```

---

## Quick Reference

### Log Level Decision Tree

```
Is the operation successful?
├── Yes → INFO
│   └── Include: entity_id, key identifiers, counts
└── No → What went wrong?
    ├── Entity not found → WARNING
    ├── Permission denied → WARNING
    ├── Validation failed → WARNING
    ├── Conflict (already exists) → WARNING
    ├── Operation failed (exception) → ERROR
    └── System-wide failure → CRITICAL
```

### Checklist for New Endpoints

- [ ] Logger initialized with `logging.getLogger(__name__)`
- [ ] DEBUG log at function entry with key parameters
- [ ] INFO log on successful completion
- [ ] WARNING logs for client errors (4xx scenarios)
- [ ] ERROR logs for server errors (5xx scenarios)
- [ ] Sensitive data masked or excluded
- [ ] Log messages follow `[COMPONENT] Action | key=value` format
