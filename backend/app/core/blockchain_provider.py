from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional
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
    Default provider for foundation when smart contract is unconfigured.
    Does not call external RPCs or fabricate on-chain transactions.
    Relies on authoritative database state or returns unanchored status.
    """

    async def verify_project_version(
        self, registration_id: str, expected_hash: Optional[str] = None
    ) -> Optional[OnChainVerificationResult]:
        return None


class Web3BlockchainVerificationProvider(BlockchainVerificationProvider):
    """
    Concrete Web3.py verification provider for ProjectRegistry.sol.
    Queries the deployed smart contract directly via BlockchainService.
    """

    def __init__(self, service: Optional[Any] = None) -> None:
        self._service = service

    def _get_service(self) -> Any:
        if self._service is not None:
            return self._service
        from app.services.blockchain_service import get_blockchain_service
        return get_blockchain_service()

    async def verify_project_version(
        self, registration_id: str, expected_hash: Optional[str] = None
    ) -> Optional[OnChainVerificationResult]:
        svc = self._get_service()
        if not svc.contract_address:
            return None

        # Verify on-chain using expected_hash or zero hash if none provided
        hash_to_check = expected_hash or ("0" * 64)
        try:
            res = svc.verify_project_version(registration_id, hash_to_check)
            if not res.get("anchored_timestamp") and not res.get("is_valid"):
                # No on-chain record found
                return None

            return OnChainVerificationResult(
                is_valid=res["is_valid"],
                registration_id=registration_id,
                anchored_timestamp=res["anchored_timestamp"],
                ipfs_root_cid=res["ipfs_root_cid"],
                author_wallet=res["author_wallet"],
                dispute_status=res["dispute_status"],
                smart_contract_address=res["smart_contract_address"],
                match_confirmed=res["match_confirmed"],
            )
        except Exception:
            return None


# Global provider instance management (enables mock injection in test suites)
_global_blockchain_provider: Optional[BlockchainVerificationProvider] = None


def get_blockchain_provider() -> BlockchainVerificationProvider:
    """Returns active BlockchainVerificationProvider instance."""
    global _global_blockchain_provider
    if _global_blockchain_provider is None:
        from app.core.config import settings

        if getattr(settings, "PROJECT_REGISTRY_CONTRACT_ADDRESS", ""):
            _global_blockchain_provider = Web3BlockchainVerificationProvider()
        else:
            _global_blockchain_provider = DefaultBlockchainVerificationProvider()
    return _global_blockchain_provider


def set_blockchain_provider(provider: Optional[BlockchainVerificationProvider]) -> None:
    """Sets or overrides active BlockchainVerificationProvider (used for tests)."""
    global _global_blockchain_provider
    _global_blockchain_provider = provider
