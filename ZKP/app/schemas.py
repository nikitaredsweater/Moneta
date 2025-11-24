"""Pydantic schemas for request and response models"""
from pydantic import BaseModel, Field
from typing import Optional


class MintNFTRequest(BaseModel):
    """Request schema for minting an NFT"""
    to_address: str = Field(..., description="Ethereum address to mint NFT to")
    token_hash: str = Field(..., description="Unique hash for the NFT (32 bytes hex)")

    class Config:
        json_schema_extra = {
            "example": {
                "to_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1",
                "token_hash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
            }
        }


class MintNFTResponse(BaseModel):
    """Response schema for minting an NFT"""
    success: bool
    token_id: Optional[int] = None
    transaction_hash: Optional[str] = None
    message: str


class TransferNFTRequest(BaseModel):
    """Request schema for transferring an NFT"""
    from_address: str = Field(..., description="Source Ethereum address")
    to_address: str = Field(..., description="Destination Ethereum address")
    token_id: int = Field(..., description="Token ID to transfer")

    class Config:
        json_schema_extra = {
            "example": {
                "from_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1",
                "to_address": "0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed",
                "token_id": 1
            }
        }


class TransferNFTResponse(BaseModel):
    """Response schema for transferring an NFT"""
    success: bool
    transaction_hash: Optional[str] = None
    message: str


class BurnNFTRequest(BaseModel):
    """Request schema for burning an NFT"""
    token_id: int = Field(..., description="Token ID to burn")

    class Config:
        json_schema_extra = {
            "example": {
                "token_id": 1
            }
        }


class BurnNFTResponse(BaseModel):
    """Response schema for burning an NFT"""
    success: bool
    transaction_hash: Optional[str] = None
    message: str


class VerifyNFTRequest(BaseModel):
    """Request schema for verifying an NFT hash"""
    token_hash: str = Field(..., description="Hash to verify (32 bytes hex)")

    class Config:
        json_schema_extra = {
            "example": {
                "token_hash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
            }
        }


class VerifyNFTResponse(BaseModel):
    """Response schema for verifying an NFT"""
    exists: bool
    token_id: Optional[int] = None
    message: str


class ContractEventResponse(BaseModel):
    """Response schema for contract events"""
    event_type: str
    block_number: int
    transaction_hash: str
    data: dict
