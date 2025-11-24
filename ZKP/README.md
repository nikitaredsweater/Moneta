# ZKP NFT Service

A FastAPI backend microservice that bridges the ZKP Service and the NFT_Storage smart contract. This service handles all blockchain interactions for minting, transferring, burning, and verifying NFTs.

## Features

- **NFT Minting**: Mint new NFTs with unique hash identifiers
- **NFT Transfer**: Transfer NFTs between wallet addresses
- **NFT Burning**: Permanently destroy NFTs
- **NFT Verification**: Verify if an NFT exists by its hash
- **Event Listening**: Listen to smart contract events and forward them to ZKP Service
- **Full Web3 Integration**: Direct interaction with Ethereum-compatible blockchains

## Architecture

```
┌─────────────┐          ┌──────────────────┐          ┌─────────────────┐
│             │          │                  │          │                 │
│ ZKP Service │◄────────►│  ZKP NFT Service │◄────────►│  NFT_Storage    │
│             │   HTTP   │   (This Service) │   Web3   │  Smart Contract │
└─────────────┘          └──────────────────┘          └─────────────────┘
```

## Project Structure

```
ZKP/
├── app/
│   ├── __init__.py          # Package initialization
│   ├── main.py              # FastAPI application with endpoints
│   ├── blockchain.py        # Web3 integration and contract interaction
│   ├── config.py            # Configuration and contract ABI
│   └── schemas.py           # Pydantic request/response models
├── .env.example             # Environment variables template
└── README.md                # This file
```

## Setup

### Prerequisites

- Python 3.8+
- Access to an Ethereum-compatible blockchain (local or testnet)
- Deployed NFT_Storage smart contract
- Wallet with private key for transaction signing

### Installation

1. Install dependencies:
```bash
# From the project root
pip install -r requirements.txt

# Or compile from requirements.in
pip-compile requirements.in
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
cd ZKP
cp .env.example .env
# Edit .env with your configuration
```

3. Required environment variables:
```bash
# Blockchain
BLOCKCHAIN_RPC_URL=http://localhost:8545  # Your blockchain RPC endpoint
CHAIN_ID=1337                              # Network chain ID

# Contract
NFT_CONTRACT_ADDRESS=0x...                 # Deployed contract address

# Wallet (for signing transactions)
WALLET_PRIVATE_KEY=0x...                   # Private key (KEEP SECRET!)
WALLET_ADDRESS=0x...                       # Wallet address

# Optional
ZKP_SERVICE_URL=http://localhost:8000      # ZKP Service endpoint
API_PORT=8001                              # This service's port
```

## Running the Service

### Development Mode

```bash
cd ZKP
python -m app.main
```

Or with uvicorn directly:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --workers 4
```

## API Endpoints

### Health Check

**GET** `/health`

Check service health and blockchain connectivity.

```bash
curl http://localhost:8001/health
```

Response:
```json
{
  "status": "healthy",
  "blockchain_connected": true,
  "contract_loaded": true,
  "wallet_loaded": true
}
```

### Mint NFT

**POST** `/nft/mint`

Mint a new NFT to a specified address.

Request:
```json
{
  "to_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1",
  "token_hash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
}
```

Response:
```json
{
  "success": true,
  "token_id": 1,
  "transaction_hash": "0xabc...",
  "message": "NFT minted successfully with token ID 1"
}
```

### Transfer NFT

**POST** `/nft/transfer`

Transfer an NFT from one address to another.

Request:
```json
{
  "from_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1",
  "to_address": "0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed",
  "token_id": 1
}
```

Response:
```json
{
  "success": true,
  "transaction_hash": "0xdef...",
  "message": "NFT 1 transferred successfully"
}
```

### Burn NFT

**POST** `/nft/burn`

Burn (destroy) an NFT permanently.

Request:
```json
{
  "token_id": 1
}
```

Response:
```json
{
  "success": true,
  "transaction_hash": "0xghi...",
  "message": "NFT 1 burned successfully"
}
```

### Verify NFT

**POST** `/nft/verify`

Verify if an NFT with a given hash exists.

Request:
```json
{
  "token_hash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
}
```

Response:
```json
{
  "exists": true,
  "token_id": 1,
  "message": "NFT exists with token ID 1"
}
```

### Get Token Hash

**GET** `/nft/{token_id}/hash`

Get the hash associated with a token ID.

```bash
curl http://localhost:8001/nft/1/hash
```

Response:
```json
{
  "token_id": 1,
  "token_hash": "0x1234...",
  "message": "Token hash retrieved successfully"
}
```

## Interactive API Documentation

Once the service is running, visit:

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

## Event Listening

The service automatically listens to blockchain events from the NFT_Storage contract:

- `Transfer` - When NFTs are transferred
- `Minted` - When new NFTs are minted
- `Burned` - When NFTs are burned

Events are automatically forwarded to the ZKP Service (if configured) at the `/events/nft` endpoint.

## Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `BLOCKCHAIN_RPC_URL` | Blockchain RPC endpoint | `http://localhost:8545` |
| `CHAIN_ID` | Network chain ID | `1337` |
| `NFT_CONTRACT_ADDRESS` | Deployed contract address | Required |
| `WALLET_PRIVATE_KEY` | Private key for signing | Required |
| `GAS_LIMIT` | Transaction gas limit | `3000000` |
| `GAS_PRICE` | Gas price in Wei (auto if empty) | `None` |
| `API_PORT` | Service port | `8001` |
| `ZKP_SERVICE_URL` | ZKP Service URL | `http://localhost:8000` |
| `EVENT_POLL_INTERVAL` | Event polling interval (seconds) | `5` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Testing with cURL

### Mint an NFT
```bash
curl -X POST http://localhost:8001/nft/mint \
  -H "Content-Type: application/json" \
  -d '{
    "to_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1",
    "token_hash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
  }'
```

### Transfer an NFT
```bash
curl -X POST http://localhost:8001/nft/transfer \
  -H "Content-Type: application/json" \
  -d '{
    "from_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1",
    "to_address": "0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed",
    "token_id": 1
  }'
```

### Verify an NFT
```bash
curl -X POST http://localhost:8001/nft/verify \
  -H "Content-Type: application/json" \
  -d '{
    "token_hash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
  }'
```

## Security Considerations

1. **Private Keys**: Never commit `.env` files or expose private keys
2. **HTTPS**: Use HTTPS in production
3. **Authentication**: Add authentication middleware for production use
4. **Rate Limiting**: Implement rate limiting to prevent abuse
5. **Input Validation**: All inputs are validated via Pydantic models
6. **Gas Limits**: Configure appropriate gas limits for your network

## Troubleshooting

### Service won't start
- Check that all required environment variables are set
- Verify blockchain RPC endpoint is accessible
- Ensure contract address is valid

### Transactions failing
- Check wallet has sufficient funds for gas
- Verify private key has permission to execute operations
- Check gas limit and price settings

### Events not being received
- Verify contract address is correct
- Check that contract is deployed and accessible
- Review event listener logs for errors

## Development

### Adding New Endpoints

1. Add request/response schemas in `schemas.py`
2. Add blockchain interaction method in `blockchain.py`
3. Create FastAPI endpoint in `main.py`

### Modifying Contract ABI

Update the `NFT_STORAGE_ABI` in `config.py` with the new contract ABI.

## License

See LICENSE file in the project root.
