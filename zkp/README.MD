# New Microservice

This is a new FastAPI-based microservice for the Moneta backend ecosystem.

## Table of Contents

- [API Endpoints](#api-endpoints)
- [Setup Instructions](#setup-instructions)
- [Development](#development)

## API Endpoints

### Base URL
All endpoints are prefixed with `/v1`

### Health Check

#### `GET /v1/health/`
Simple health check endpoint to verify service status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": 1234567890.123,
  "service": "new_microservice",
  "version": "1.0.0"
}
```

## Setup Instructions

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run development server:
```bash
./scripts/run_dev.sh
```

## Development

- API documentation: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc
