from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class OnChainVerificationResult(BaseModel):
    """
    Represents on-chain proof returned by a blockchain verification provider.
    Conforms to the frozen ProjectRegistry.sol verifyProjectVersion contract.
    """
    model_config = ConfigDict(from_attributes=True)

    is_valid: bool
    registration_id: str
    anchored_timestamp: Optional[datetime] = None
    ipfs_root_cid: Optional[str] = None
    author_wallet: Optional[str] = None
    dispute_status: str = "NONE"
    transaction_hash: Optional[str] = None
    block_number: Optional[int] = None
    smart_contract_address: Optional[str] = None
    match_confirmed: bool = False


class BlockchainVerificationProvider(ABC):
    """
    Abstract interface for verifying project version registrations on-chain.
    In Step 4.5, this cleanly abstracts on-chain query logic.
    Developer 3 will implement the concrete Web3.py provider in Phase 5.
    """

    @abstractmethod
    async def verify_project_version(
        self, registration_id: str, expected_hash: Optional[str] = None
    ) -> Optional[OnChainVerificationResult]:
        """
        Queries blockchain state for the specified registration_id and compares
        it against expected_hash if provided.
        Returns None if no on-chain record exists.
        """
        pass


class DefaultBlockchainVerificationProvider(BlockchainVerificationProvider):
    """
    Default provider for Phase 4 foundation.
    Does not call external RPCs or fabricate on-chain transactions.
    Relies on authoritative database state or returns unanchored status.
    """

    async def verify_project_version(
        self, registration_id: str, expected_hash: Optional[str] = None
    ) -> Optional[OnChainVerificationResult]:
        # In Phase 4, the service layer queries PostgreSQL for the persisted BlockchainRecord.
        # Developer 3 will inject Web3.py RPC calls into a Web3BlockchainVerificationProvider in Phase 5.
        return None


# Global provider instance management (enables mock injection in test suites)
_global_blockchain_provider: Optional[BlockchainVerificationProvider] = None


def get_blockchain_provider() -> BlockchainVerificationProvider:
    """Returns active BlockchainVerificationProvider instance."""
    global _global_blockchain_provider
    if _global_blockchain_provider is None:
        _global_blockchain_provider = DefaultBlockchainVerificationProvider()
    return _global_blockchain_provider


def set_blockchain_provider(provider: Optional[BlockchainVerificationProvider]) -> None:
    """Sets or overrides active BlockchainVerificationProvider (used for tests)."""
    global _global_blockchain_provider
    _global_blockchain_provider = provider
