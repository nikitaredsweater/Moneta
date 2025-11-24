#!/usr/bin/env python3
"""
Test script to simulate requests from the on_chain service
This helps verify that the authentication and endpoint work correctly
"""
import hmac
import hashlib
import json
import requests
import sys
from datetime import datetime

# Configuration
ZKP_SERVICE_URL = "http://localhost:8000"
SERVICE_SECRET = "your-secret-key-here"  # Should match ON_CHAIN_SERVICE_SECRET in .env


def generate_signature(body_dict: dict, secret: str) -> str:
    """Generate HMAC-SHA256 signature for request body"""
    body_bytes = json.dumps(body_dict, separators=(',', ':')).encode('utf-8')
    signature = hmac.new(
        secret.encode(),
        body_bytes,
        hashlib.sha256
    ).hexdigest()
    return signature


def test_nft_minted_event():
    """Test sending an NFT minted event"""
    print("\n=== Testing NFT Minted Event ===")
    
    data = {
        "event_type": "NFTMinted",
        "transaction_hash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        "block_number": 12345678,
        "contract_address": "0xabcdef1234567890abcdef1234567890abcdef12",
        "event_data": {
            "token_id": 1,
            "owner": "0x9876543210fedcba9876543210fedcba98765432",
            "uri": "ipfs://QmXyz123456789"
        },
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "chain_id": 1
    }
    
    signature = generate_signature(data, SERVICE_SECRET)
    
    headers = {
        "X-Service-Name": "on_chain",
        "X-Service-Signature": signature,
        "X-Request-ID": "test-request-001",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{ZKP_SERVICE_URL}/v1/service/onchain/event",
            json=data,
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return False


def test_nft_transferred_event():
    """Test sending an NFT transferred event"""
    print("\n=== Testing NFT Transferred Event ===")
    
    data = {
        "event_type": "NFTTransferred",
        "transaction_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        "block_number": 12345679,
        "contract_address": "0xabcdef1234567890abcdef1234567890abcdef12",
        "event_data": {
            "token_id": 1,
            "from": "0x9876543210fedcba9876543210fedcba98765432",
            "to": "0x1111111111111111111111111111111111111111"
        },
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "chain_id": 1
    }
    
    signature = generate_signature(data, SERVICE_SECRET)
    
    headers = {
        "X-Service-Name": "on_chain",
        "X-Service-Signature": signature,
        "X-Request-ID": "test-request-002",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{ZKP_SERVICE_URL}/v1/service/onchain/event",
            json=data,
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return False


def test_transaction():
    """Test sending transaction data"""
    print("\n=== Testing Transaction Data ===")
    
    data = {
        "transaction_hash": "0xfedcba0987654321fedcba0987654321fedcba0987654321fedcba0987654321",
        "from_address": "0x9876543210fedcba9876543210fedcba98765432",
        "to_address": "0xabcdef1234567890abcdef1234567890abcdef12",
        "value": "1000000000000000000",
        "gas_used": 21000,
        "status": "success",
        "block_number": 12345680,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    signature = generate_signature(data, SERVICE_SECRET)
    
    headers = {
        "X-Service-Name": "on_chain",
        "X-Service-Signature": signature,
        "X-Request-ID": "test-request-003",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{ZKP_SERVICE_URL}/v1/service/onchain/transaction",
            json=data,
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return False


def test_invalid_signature():
    """Test that invalid signatures are rejected"""
    print("\n=== Testing Invalid Signature (Should Fail) ===")
    
    data = {
        "event_type": "NFTMinted",
        "transaction_hash": "0x123",
        "block_number": 123,
        "contract_address": "0xabc",
        "event_data": {"token_id": 1}
    }
    
    headers = {
        "X-Service-Name": "on_chain",
        "X-Service-Signature": "invalid_signature_12345",
        "X-Request-ID": "test-request-004",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{ZKP_SERVICE_URL}/v1/service/onchain/event",
            json=data,
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # Should return 401 Unauthorized
        return response.status_code == 401
    except Exception as e:
        print(f"Error: {str(e)}")
        return False


def main():
    print("=" * 60)
    print("Testing On-Chain Service Integration")
    print("=" * 60)
    print(f"\nTarget URL: {ZKP_SERVICE_URL}")
    print(f"Service Secret: {SERVICE_SECRET[:10]}...")
    print("\nMake sure the ZKP service is running:")
    print("  uvicorn app.main:app --reload")
    print("\nAnd that ON_CHAIN_SERVICE_SECRET is set in your .env file")
    
    results = []
    
    # Run tests
    results.append(("NFT Minted Event", test_nft_minted_event()))
    results.append(("NFT Transferred Event", test_nft_transferred_event()))
    results.append(("Transaction Data", test_transaction()))
    results.append(("Invalid Signature", test_invalid_signature()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
