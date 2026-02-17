# Inter-Service Authentication Guide

This document explains how the ZKP service authenticates requests from the "on_chain" service.

## Overview

The ZKP service uses **HMAC-SHA256 signatures** to verify that requests come from trusted microservices. This ensures that only authorized services can send data to protected endpoints.

## Authentication Flow

1. **Service Identification**: The calling service includes its name in the `X-Service-Name` header
2. **Request Signing**: The calling service generates an HMAC-SHA256 signature of the request body using a shared secret
3. **Signature Verification**: The ZKP service verifies the signature matches the expected value
4. **Request Processing**: If authentication succeeds, the request is processed

## Configuration

### ZKP Service (This Service)

Add the shared secret to your `.env` file:

```bash
ON_CHAIN_SERVICE_SECRET=your-secret-key-here
```

Generate a secure secret key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### On Chain Service (Calling Service)

The on_chain service needs to:

1. **Store the same secret key** in its environment variables
2. **Include required headers** in each request:
   - `X-Service-Name: on_chain`
   - `X-Service-Signature: <hmac_signature>`
   - `X-Request-ID: <optional_tracking_id>`

3. **Generate the signature** for each request:

```python
import hmac
import hashlib
import json
import requests

# Configuration
ZKP_SERVICE_URL = "http://zkp-service:8000"
SERVICE_SECRET = "your-secret-key-here"

# Prepare request data
data = {
    "event_type": "NFTMinted",
    "transaction_hash": "0x1234...",
    "block_number": 12345678,
    "contract_address": "0xabcd...",
    "event_data": {
        "token_id": 1,
        "owner": "0x9876...",
        "uri": "ipfs://QmXyz..."
    }
}

# Convert to JSON bytes
body = json.dumps(data).encode('utf-8')

# Generate HMAC signature
signature = hmac.new(
    SERVICE_SECRET.encode(),
    body,
    hashlib.sha256
).hexdigest()

# Send request with authentication headers
response = requests.post(
    f"{ZKP_SERVICE_URL}/v1/service/onchain/event",
    json=data,
    headers={
        "X-Service-Name": "on_chain",
        "X-Service-Signature": signature,
        "X-Request-ID": "unique-request-id",
        "Content-Type": "application/json"
    }
)

print(response.json())
```

## Available Endpoints

### 1. Receive Blockchain Event
**POST** `/v1/service/onchain/event`

Receives blockchain event data (NFT minting, transfers, burns, etc.)

**Request Body:**
```json
{
  "event_type": "NFTMinted",
  "transaction_hash": "0x1234567890abcdef...",
  "block_number": 12345678,
  "contract_address": "0xabcdef1234567890...",
  "event_data": {
    "token_id": 1,
    "owner": "0x9876543210fedcba...",
    "uri": "ipfs://QmXyz..."
  },
  "timestamp": "2025-10-13T13:00:00Z",
  "chain_id": 1
}
```

**Response:**
```json
{
  "success": true,
  "message": "Event NFTMinted processed successfully",
  "data": {
    "processed": true,
    "token_id": 1,
    "owner": "0x9876543210fedcba...",
    "uri": "ipfs://QmXyz...",
    "action": "NFT minted event recorded"
  },
  "request_id": "unique-request-id"
}
```

### 2. Receive Transaction Data
**POST** `/v1/service/onchain/transaction`

Receives general transaction data for tracking or processing.

**Request Body:**
```json
{
  "transaction_hash": "0x1234567890abcdef...",
  "from_address": "0xabcdef1234567890...",
  "to_address": "0x9876543210fedcba...",
  "value": "1000000000000000000",
  "gas_used": 21000,
  "status": "success",
  "block_number": 12345678,
  "timestamp": "2025-10-13T13:00:00Z"
}
```

## Supported Event Types

- `NFTMinted` - When a new NFT is minted
- `NFTTransferred` - When an NFT is transferred between addresses
- `NFTBurned` - When an NFT is burned/destroyed

## Security Best Practices

1. **Never commit secrets** to version control
2. **Use environment variables** for all secrets
3. **Rotate secrets regularly** (update in both services simultaneously)
4. **Use HTTPS** in production to encrypt all traffic
5. **Monitor failed authentication attempts** for security incidents
6. **Use unique request IDs** for tracking and debugging

## Testing

Test the authentication locally:

```bash
# Start the ZKP service
uvicorn app.main:app --reload

# In another terminal, test with curl
curl -X POST http://localhost:8000/v1/service/onchain/event \
  -H "Content-Type: application/json" \
  -H "X-Service-Name: on_chain" \
  -H "X-Service-Signature: <generate_signature>" \
  -d '{
    "event_type": "NFTMinted",
    "transaction_hash": "0x123",
    "block_number": 123,
    "contract_address": "0xabc",
    "event_data": {"token_id": 1}
  }'
```

## Troubleshooting

### 401 Unauthorized - Missing Headers
- Ensure `X-Service-Name` and `X-Service-Signature` headers are included

### 403 Forbidden - Service Not Authorized
- Check that the service name matches exactly: `on_chain`
- Verify the service is configured in `TRUSTED_SERVICES`

### 401 Unauthorized - Invalid Signature
- Ensure both services use the **exact same secret key**
- Verify the signature is generated from the **request body** (not headers)
- Check that the body is encoded as UTF-8 bytes before signing
- Ensure JSON serialization is consistent (no extra whitespace)

## Adding More Trusted Services

To add additional trusted services, update `main.py`:

```python
TRUSTED_SERVICES = {
    "on_chain": os.getenv("ON_CHAIN_SERVICE_SECRET"),
    "another_service": os.getenv("ANOTHER_SERVICE_SECRET"),
}
```

And add the corresponding environment variable to your `.env` file.
