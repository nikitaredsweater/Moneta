"""
ZKP NFT Service - FastAPI Backend Microservice

This service acts as a bridge between the ZKP Service and the NFT_Storage smart contract.
It handles mint, transfer, burn, and verify operations for NFTs.
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import httpx

from .config import settings
from .blockchain import blockchain_service
from .schemas import (
    MintNFTRequest,
    MintNFTResponse,
    TransferNFTRequest,
    TransferNFTResponse,
    BurnNFTRequest,
    BurnNFTResponse,
    VerifyNFTRequest,
    VerifyNFTResponse,
    ContractEventResponse
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Background task flag
event_listener_running = False


async def event_listener_task():
    """Background task to listen to contract events and forward to ZKP Service"""
    global event_listener_running

    logger.info("Starting event listener task")
    event_listener_running = True

    while event_listener_running:
        try:
            # Listen for events
            for event_data in blockchain_service.listen_to_events(from_block=settings.START_BLOCK):
                logger.info(f"Received event: {event_data['event_type']}")

                # Forward event to ZKP Service if configured
                if settings.ZKP_SERVICE_URL:
                    try:
                        async with httpx.AsyncClient() as client:
                            response = await client.post(
                                f"{settings.ZKP_SERVICE_URL}/events/nft",
                                json=event_data,
                                timeout=10.0
                            )
                            if response.status_code == 200:
                                logger.info(f"Event forwarded to ZKP Service: {event_data['event_type']}")
                            else:
                                logger.warning(f"Failed to forward event: {response.status_code}")
                    except Exception as e:
                        logger.error(f"Error forwarding event to ZKP Service: {e}")

            # Sleep before next poll
            await asyncio.sleep(settings.EVENT_POLL_INTERVAL)

        except Exception as e:
            logger.error(f"Error in event listener: {e}")
            await asyncio.sleep(settings.EVENT_POLL_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI app"""
    # Startup
    logger.info("Starting ZKP NFT Service")

    # Initialize blockchain service
    if not blockchain_service.initialize():
        logger.error("Failed to initialize blockchain service")
    else:
        logger.info("Blockchain service initialized successfully")

    # Start event listener in background
    event_task = asyncio.create_task(event_listener_task())

    yield

    # Shutdown
    logger.info("Shutting down ZKP NFT Service")
    global event_listener_running
    event_listener_running = False

    # Cancel event listener task
    event_task.cancel()
    try:
        await event_task
    except asyncio.CancelledError:
        pass


# Create FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="Backend microservice for NFT operations via smart contracts",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.API_TITLE,
        "version": settings.API_VERSION,
        "status": "running",
        "blockchain_connected": blockchain_service.is_ready()
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    is_ready = blockchain_service.is_ready()

    return {
        "status": "healthy" if is_ready else "unhealthy",
        "blockchain_connected": blockchain_service.w3 is not None and blockchain_service.w3.is_connected() if blockchain_service.w3 else False,
        "contract_loaded": blockchain_service.contract is not None,
        "wallet_loaded": blockchain_service.account is not None
    }


@app.post("/nft/mint", response_model=MintNFTResponse)
async def mint_nft(request: MintNFTRequest):
    """
    Mint a new NFT

    This endpoint receives mint requests from the ZKP Service and sends them to the smart contract.

    Args:
        request: MintNFTRequest containing to_address and token_hash

    Returns:
        MintNFTResponse with success status, token_id, and transaction_hash
    """
    try:
        logger.info(f"Received mint request for address {request.to_address}")

        # Mint NFT via blockchain service
        success, token_id, tx_hash, message = blockchain_service.mint_nft(
            to_address=request.to_address,
            token_hash=request.token_hash
        )

        if success:
            logger.info(f"NFT minted successfully: token_id={token_id}, tx_hash={tx_hash}")
            return MintNFTResponse(
                success=True,
                token_id=token_id,
                transaction_hash=tx_hash,
                message=message
            )
        else:
            logger.error(f"Failed to mint NFT: {message}")
            raise HTTPException(status_code=400, detail=message)

    except Exception as e:
        logger.error(f"Error in mint endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/nft/transfer", response_model=TransferNFTResponse)
async def transfer_nft(request: TransferNFTRequest):
    """
    Transfer an NFT

    This endpoint receives transfer requests from the ZKP Service and sends them to the smart contract.

    Args:
        request: TransferNFTRequest containing from_address, to_address, and token_id

    Returns:
        TransferNFTResponse with success status and transaction_hash
    """
    try:
        logger.info(f"Received transfer request for token {request.token_id} from {request.from_address} to {request.to_address}")

        # Transfer NFT via blockchain service
        success, tx_hash, message = blockchain_service.transfer_nft(
            from_address=request.from_address,
            to_address=request.to_address,
            token_id=request.token_id
        )

        if success:
            logger.info(f"NFT transferred successfully: tx_hash={tx_hash}")
            return TransferNFTResponse(
                success=True,
                transaction_hash=tx_hash,
                message=message
            )
        else:
            logger.error(f"Failed to transfer NFT: {message}")
            raise HTTPException(status_code=400, detail=message)

    except Exception as e:
        logger.error(f"Error in transfer endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/nft/burn", response_model=BurnNFTResponse)
async def burn_nft(request: BurnNFTRequest):
    """
    Burn an NFT

    This endpoint receives burn requests from the ZKP Service and sends them to the smart contract.

    Args:
        request: BurnNFTRequest containing token_id

    Returns:
        BurnNFTResponse with success status and transaction_hash
    """
    try:
        logger.info(f"Received burn request for token {request.token_id}")

        # Burn NFT via blockchain service
        success, tx_hash, message = blockchain_service.burn_nft(
            token_id=request.token_id
        )

        if success:
            logger.info(f"NFT burned successfully: tx_hash={tx_hash}")
            return BurnNFTResponse(
                success=True,
                transaction_hash=tx_hash,
                message=message
            )
        else:
            logger.error(f"Failed to burn NFT: {message}")
            raise HTTPException(status_code=400, detail=message)

    except Exception as e:
        logger.error(f"Error in burn endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/nft/verify", response_model=VerifyNFTResponse)
async def verify_nft(request: VerifyNFTRequest):
    """
    Verify if an NFT exists

    This endpoint receives verify requests from the ZKP Service, checks the smart contract,
    and returns the verification result.

    Args:
        request: VerifyNFTRequest containing token_hash

    Returns:
        VerifyNFTResponse with exists status, optional token_id, and message
    """
    try:
        logger.info(f"Received verify request for hash {request.token_hash}")

        # Verify NFT via blockchain service
        exists, token_id, message = blockchain_service.verify_nft(
            token_hash=request.token_hash
        )

        logger.info(f"NFT verification result: exists={exists}, token_id={token_id}")

        return VerifyNFTResponse(
            exists=exists,
            token_id=token_id,
            message=message
        )

    except Exception as e:
        logger.error(f"Error in verify endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/nft/{token_id}/hash")
async def get_token_hash(token_id: int):
    """
    Get the hash associated with a token ID

    Args:
        token_id: Token ID to query

    Returns:
        Token hash information
    """
    try:
        token_hash = blockchain_service.get_token_hash(token_id)

        if token_hash:
            return {
                "token_id": token_id,
                "token_hash": token_hash,
                "message": "Token hash retrieved successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="Token not found or does not exist")

    except Exception as e:
        logger.error(f"Error getting token hash: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/events/zkp")
async def receive_zkp_event(event_data: dict):
    """
    Receive events from ZKP Service

    This endpoint allows the ZKP Service to send events or notifications to this service.

    Args:
        event_data: Event data from ZKP Service

    Returns:
        Acknowledgment
    """
    try:
        logger.info(f"Received event from ZKP Service: {event_data}")

        # Process the event as needed
        # You can add custom logic here based on your requirements

        return {
            "success": True,
            "message": "Event received and processed"
        }

    except Exception as e:
        logger.error(f"Error processing ZKP event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )
