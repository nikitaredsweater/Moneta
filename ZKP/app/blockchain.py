"""Blockchain interaction module for NFT_Storage contract"""
import logging
from typing import Optional, Tuple
from web3 import Web3
from web3.contract import Contract
from web3.exceptions import ContractLogicError
from eth_account import Account
from .config import settings, NFT_STORAGE_ABI

logger = logging.getLogger(__name__)


class BlockchainService:
    """Service for interacting with the NFT_Storage smart contract"""

    def __init__(self):
        """Initialize blockchain service"""
        self.w3: Optional[Web3] = None
        self.contract: Optional[Contract] = None
        self.account: Optional[Account] = None
        self._initialized = False

    def initialize(self) -> bool:
        """
        Initialize Web3 connection and contract instance

        Returns:
            bool: True if initialization successful
        """
        try:
            # Connect to blockchain
            logger.info(f"Connecting to blockchain at {settings.BLOCKCHAIN_RPC_URL}")
            self.w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_RPC_URL))

            if not self.w3.is_connected():
                logger.error("Failed to connect to blockchain")
                return False

            logger.info(f"Connected to blockchain. Chain ID: {self.w3.eth.chain_id}")

            # Load account from private key
            if settings.WALLET_PRIVATE_KEY:
                self.account = Account.from_key(settings.WALLET_PRIVATE_KEY)
                logger.info(f"Loaded wallet address: {self.account.address}")
            else:
                logger.warning("No wallet private key provided. Transaction signing will fail.")

            # Load contract
            if settings.NFT_CONTRACT_ADDRESS:
                contract_address = Web3.to_checksum_address(settings.NFT_CONTRACT_ADDRESS)
                self.contract = self.w3.eth.contract(
                    address=contract_address,
                    abi=NFT_STORAGE_ABI
                )
                logger.info(f"Loaded NFT_Storage contract at {contract_address}")
            else:
                logger.warning("No contract address provided. Contract interactions will fail.")

            self._initialized = True
            return True

        except Exception as e:
            logger.error(f"Failed to initialize blockchain service: {e}")
            return False

    def is_ready(self) -> bool:
        """Check if service is ready for operations"""
        return (
            self._initialized
            and self.w3 is not None
            and self.w3.is_connected()
            and self.contract is not None
            and self.account is not None
        )

    def _build_and_send_transaction(self, transaction) -> Tuple[bool, Optional[str], str]:
        """
        Build, sign and send a transaction

        Args:
            transaction: Transaction function to execute

        Returns:
            Tuple of (success, transaction_hash, message)
        """
        try:
            if not self.is_ready():
                return False, None, "Blockchain service not ready"

            # Build transaction
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            gas_price = settings.GAS_PRICE or self.w3.eth.gas_price

            tx_dict = transaction.build_transaction({
                'from': self.account.address,
                'nonce': nonce,
                'gas': settings.GAS_LIMIT,
                'gasPrice': gas_price,
                'chainId': self.w3.eth.chain_id
            })

            # Sign transaction
            signed_tx = self.w3.eth.account.sign_transaction(tx_dict, self.account.key)

            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_hash_hex = tx_hash.hex()

            logger.info(f"Transaction sent: {tx_hash_hex}")

            # Wait for transaction receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            if receipt.status == 1:
                logger.info(f"Transaction successful: {tx_hash_hex}")
                return True, tx_hash_hex, "Transaction successful"
            else:
                logger.error(f"Transaction failed: {tx_hash_hex}")
                return False, tx_hash_hex, "Transaction failed"

        except ContractLogicError as e:
            logger.error(f"Contract logic error: {e}")
            return False, None, f"Contract error: {str(e)}"
        except Exception as e:
            logger.error(f"Transaction error: {e}")
            return False, None, f"Transaction error: {str(e)}"

    def mint_nft(self, to_address: str, token_hash: str) -> Tuple[bool, Optional[int], Optional[str], str]:
        """
        Mint a new NFT

        Args:
            to_address: Address to mint NFT to
            token_hash: Unique hash for the NFT (must be 32 bytes hex)

        Returns:
            Tuple of (success, token_id, transaction_hash, message)
        """
        try:
            if not self.is_ready():
                return False, None, None, "Blockchain service not ready"

            # Convert addresses and hash
            to_address = Web3.to_checksum_address(to_address)

            # Ensure token_hash is bytes32
            if isinstance(token_hash, str):
                if token_hash.startswith('0x'):
                    token_hash = token_hash[2:]
                token_hash_bytes = bytes.fromhex(token_hash)
            else:
                token_hash_bytes = token_hash

            if len(token_hash_bytes) != 32:
                return False, None, None, "Token hash must be 32 bytes"

            # Build transaction
            transaction = self.contract.functions.mintNFT(to_address, token_hash_bytes)

            # Send transaction
            success, tx_hash, message = self._build_and_send_transaction(transaction)

            if success:
                # Get token ID from transaction receipt
                receipt = self.w3.eth.get_transaction_receipt(tx_hash)
                # Parse Minted event to get token ID
                minted_event = self.contract.events.Minted().process_receipt(receipt)
                if minted_event:
                    token_id = minted_event[0]['args']['tokenId']
                    return True, token_id, tx_hash, f"NFT minted successfully with token ID {token_id}"
                else:
                    return True, None, tx_hash, "NFT minted but could not retrieve token ID"

            return False, None, tx_hash, message

        except Exception as e:
            logger.error(f"Error minting NFT: {e}")
            return False, None, None, f"Error: {str(e)}"

    def transfer_nft(self, from_address: str, to_address: str, token_id: int) -> Tuple[bool, Optional[str], str]:
        """
        Transfer an NFT

        Args:
            from_address: Source address
            to_address: Destination address
            token_id: Token ID to transfer

        Returns:
            Tuple of (success, transaction_hash, message)
        """
        try:
            if not self.is_ready():
                return False, None, "Blockchain service not ready"

            # Convert addresses
            from_address = Web3.to_checksum_address(from_address)
            to_address = Web3.to_checksum_address(to_address)

            # Build transaction
            transaction = self.contract.functions.transferNFT(from_address, to_address, token_id)

            # Send transaction
            success, tx_hash, message = self._build_and_send_transaction(transaction)

            if success:
                return True, tx_hash, f"NFT {token_id} transferred successfully"

            return False, tx_hash, message

        except Exception as e:
            logger.error(f"Error transferring NFT: {e}")
            return False, None, f"Error: {str(e)}"

    def burn_nft(self, token_id: int) -> Tuple[bool, Optional[str], str]:
        """
        Burn an NFT

        Args:
            token_id: Token ID to burn

        Returns:
            Tuple of (success, transaction_hash, message)
        """
        try:
            if not self.is_ready():
                return False, None, "Blockchain service not ready"

            # Build transaction
            transaction = self.contract.functions.burnNFT(token_id)

            # Send transaction
            success, tx_hash, message = self._build_and_send_transaction(transaction)

            if success:
                return True, tx_hash, f"NFT {token_id} burned successfully"

            return False, tx_hash, message

        except Exception as e:
            logger.error(f"Error burning NFT: {e}")
            return False, None, f"Error: {str(e)}"

    def verify_nft(self, token_hash: str) -> Tuple[bool, Optional[int], str]:
        """
        Verify if an NFT with the given hash exists

        Args:
            token_hash: Hash to verify (32 bytes hex)

        Returns:
            Tuple of (exists, token_id, message)
        """
        try:
            if not self.is_ready():
                return False, None, "Blockchain service not ready"

            # Ensure token_hash is bytes32
            if isinstance(token_hash, str):
                if token_hash.startswith('0x'):
                    token_hash = token_hash[2:]
                token_hash_bytes = bytes.fromhex(token_hash)
            else:
                token_hash_bytes = token_hash

            if len(token_hash_bytes) != 32:
                return False, None, "Token hash must be 32 bytes"

            # Call view function
            exists = self.contract.functions.verifyNFT(token_hash_bytes).call()

            if exists:
                # Get token ID
                token_id = self.contract.functions.getTokenIdByHash(token_hash_bytes).call()
                return True, token_id, f"NFT exists with token ID {token_id}"
            else:
                return False, None, "NFT does not exist"

        except Exception as e:
            logger.error(f"Error verifying NFT: {e}")
            return False, None, f"Error: {str(e)}"

    def get_token_hash(self, token_id: int) -> Optional[str]:
        """
        Get the hash associated with a token ID

        Args:
            token_id: Token ID

        Returns:
            Token hash as hex string or None
        """
        try:
            if not self.is_ready():
                return None

            token_hash = self.contract.functions.getTokenHash(token_id).call()
            return '0x' + token_hash.hex()

        except Exception as e:
            logger.error(f"Error getting token hash: {e}")
            return None

    def listen_to_events(self, from_block: int = 'latest'):
        """
        Listen to contract events

        Args:
            from_block: Block number to start listening from

        Yields:
            Event data
        """
        if not self.is_ready():
            logger.error("Blockchain service not ready for event listening")
            return

        # Create filters for each event type
        transfer_filter = self.contract.events.Transfer.create_filter(fromBlock=from_block)
        minted_filter = self.contract.events.Minted.create_filter(fromBlock=from_block)
        burned_filter = self.contract.events.Burned.create_filter(fromBlock=from_block)

        while True:
            try:
                # Check for Transfer events
                for event in transfer_filter.get_new_entries():
                    yield {
                        'event_type': 'Transfer',
                        'block_number': event['blockNumber'],
                        'transaction_hash': event['transactionHash'].hex(),
                        'data': {
                            'from': event['args']['from'],
                            'to': event['args']['to'],
                            'tokenId': event['args']['tokenId']
                        }
                    }

                # Check for Minted events
                for event in minted_filter.get_new_entries():
                    yield {
                        'event_type': 'Minted',
                        'block_number': event['blockNumber'],
                        'transaction_hash': event['transactionHash'].hex(),
                        'data': {
                            'to': event['args']['to'],
                            'tokenId': event['args']['tokenId'],
                            'tokenHash': '0x' + event['args']['tokenHash'].hex()
                        }
                    }

                # Check for Burned events
                for event in burned_filter.get_new_entries():
                    yield {
                        'event_type': 'Burned',
                        'block_number': event['blockNumber'],
                        'transaction_hash': event['transactionHash'].hex(),
                        'data': {
                            'tokenId': event['args']['tokenId'],
                            'tokenHash': '0x' + event['args']['tokenHash'].hex()
                        }
                    }

            except Exception as e:
                logger.error(f"Error listening to events: {e}")


# Global blockchain service instance
blockchain_service = BlockchainService()
