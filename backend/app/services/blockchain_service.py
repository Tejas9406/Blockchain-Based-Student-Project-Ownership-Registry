import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

from eth_account import Account
from web3 import Web3
from web3.exceptions import ContractLogicError, TransactionNotFound

from app.abi import get_project_registry_abi
from app.core.config import settings
from app.core.exceptions import BlockchainException

logger = logging.getLogger(__name__)

# Precompiled regex patterns
SHA256_HEX_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")

# Lifecycle stage mappings to Solidity enum IProjectRegistry.LifecycleStage
LIFECYCLE_STAGE_TO_INT: Dict[str, int] = {
    "IDEA": 0,
    "DESIGN": 1,
    "PROTOTYPE": 2,
    "FINAL": 3,
}

INT_TO_LIFECYCLE_STAGE: Dict[int, str] = {v: k for k, v in LIFECYCLE_STAGE_TO_INT.items()}

# Dispute status mappings to Solidity enum IProjectRegistry.DisputeStatus
DISPUTE_STATUS_TO_INT: Dict[str, int] = {
    "NONE": 0,
    "OPEN": 1,
    "UNDER_REVIEW": 2,
    "RESOLVED": 3,
    "REJECTED": 4,
}

INT_TO_DISPUTE_STATUS: Dict[int, str] = {v: k for k, v in DISPUTE_STATUS_TO_INT.items()}


def sha256_to_bytes32(hex_digest: str) -> bytes:
    """
    Converts a 64-character SHA-256 hexadecimal string into a 32-byte binary digest.
    Validates formatting and ensures non-zero input.
    """
    if not hex_digest or not isinstance(hex_digest, str):
        raise BlockchainException(
            code="BLOCKCHAIN_INVALID_HASH",
            message="SHA-256 hash must be a non-empty string.",
            status_code=422,
        )

    clean_hex = hex_digest.strip().lower()
    if clean_hex.startswith("0x"):
        clean_hex = clean_hex[2:]

    if not SHA256_HEX_PATTERN.match(clean_hex):
        raise BlockchainException(
            code="BLOCKCHAIN_INVALID_HASH",
            message=f"Invalid SHA-256 hash format. Expected 64 hexadecimal characters, got {len(clean_hex)} chars.",
            status_code=422,
            details={"hash_length": len(clean_hex)},
        )

    if clean_hex == "0" * 64:
        raise BlockchainException(
            code="BLOCKCHAIN_INVALID_HASH",
            message="Zero composite hash (0x000...000) is prohibited for registration.",
            status_code=422,
        )

    return bytes.fromhex(clean_hex)


def lifecycle_stage_to_solidity(stage: Union[str, int, Any]) -> int:
    """
    Safely converts a lifecycle stage representation (Enum, str, or int)
    into the Solidity IProjectRegistry.LifecycleStage enum index (0-3).
    """
    if isinstance(stage, int):
        if 0 <= stage <= 3:
            return stage
        raise BlockchainException(
            code="BLOCKCHAIN_CONFIGURATION_ERROR",
            message=f"Invalid lifecycle stage integer {stage}. Must be between 0 (IDEA) and 3 (FINAL).",
            status_code=422,
        )

    stage_str = stage.value if hasattr(stage, "value") else str(stage)
    normalized = stage_str.strip().upper()
    if normalized in LIFECYCLE_STAGE_TO_INT:
        return LIFECYCLE_STAGE_TO_INT[normalized]

    raise BlockchainException(
        code="BLOCKCHAIN_CONFIGURATION_ERROR",
        message=f"Unknown lifecycle stage '{stage}'. Expected one of: IDEA, DESIGN, PROTOTYPE, FINAL.",
        status_code=422,
    )


def normalize_address(address: Optional[str]) -> str:
    """
    Validates and converts an Ethereum address to EIP-55 checksummed format.
    Accepts empty or None as the zero address (0x000...000).
    """
    if not address or address.strip() == "":
        return Web3.to_checksum_address("0x0000000000000000000000000000000000000000")

    clean = address.strip()
    if not Web3.is_address(clean):
        raise BlockchainException(
            code="BLOCKCHAIN_INVALID_ADDRESS",
            message=f"Invalid Ethereum address: '{address}'.",
            status_code=422,
            details={"address": address},
        )

    return Web3.to_checksum_address(clean)


class BlockchainService:
    """
    Web3.py Blockchain Service encapsulating all communication with the ProjectRegistry smart contract.
    Responsible for:
    - Provider initialization & RPC health checks
    - Relayer wallet initialization & transaction signing
    - Registering project version proofs on-chain
    - Public trustless verification view queries
    - Querying version proofs & dispute lifecycle actions
    - Event log decoding and receipt confirmation tracking
    """

    def __init__(
        self,
        rpc_url: Optional[str] = None,
        contract_address: Optional[str] = None,
        chain_id: Optional[int] = None,
        relayer_private_key: Optional[str] = None,
        confirmation_blocks: Optional[int] = None,
        timeout_seconds: Optional[int] = None,
        web3_instance: Optional[Web3] = None,
    ) -> None:
        self._rpc_url = (rpc_url or getattr(settings, "BLOCKCHAIN_RPC_URL", "http://127.0.0.1:8545")).rstrip("/")
        self._expected_chain_id = chain_id or getattr(settings, "BLOCKCHAIN_CHAIN_ID", 31337)
        self._confirmation_blocks = confirmation_blocks or getattr(settings, "BLOCKCHAIN_CONFIRMATION_BLOCKS", 1)
        self._timeout = timeout_seconds or getattr(settings, "BLOCKCHAIN_TIMEOUT_SECONDS", 30)

        # 1. Initialize Web3 Provider
        if web3_instance is not None:
            self._w3 = web3_instance
        else:
            provider = Web3.HTTPProvider(
                self._rpc_url,
                request_kwargs={"timeout": self._timeout},
            )
            self._w3 = Web3(provider)

        # 2. Configure Relayer Account (Never store or log private keys)
        raw_key = relayer_private_key or getattr(settings, "RELAYER_PRIVATE_KEY", "")
        self._relayer_account: Optional[Any] = None
        self._relayer_address: Optional[str] = None

        if raw_key and raw_key.strip():
            clean_key = raw_key.strip()
            if not clean_key.startswith("0x") and len(clean_key) == 64:
                clean_key = "0x" + clean_key
            try:
                self._relayer_account = Account.from_key(clean_key)
                self._relayer_address = Web3.to_checksum_address(self._relayer_account.address)
            except Exception as e:
                raise BlockchainException(
                    code="BLOCKCHAIN_CONFIGURATION_ERROR",
                    message="Failed to initialize relayer account from configured private key.",
                    details={"error": str(e)},
                )

        # 3. Configure Smart Contract
        raw_contract_address = contract_address or getattr(settings, "PROJECT_REGISTRY_CONTRACT_ADDRESS", "")
        self._contract_address: Optional[str] = None
        self._contract: Optional[Any] = None

        if raw_contract_address and raw_contract_address.strip():
            clean_addr = raw_contract_address.strip()
            if not Web3.is_address(clean_addr):
                raise BlockchainException(
                    code="BLOCKCHAIN_INVALID_ADDRESS",
                    message=f"Configured smart contract address '{clean_addr}' is invalid.",
                )
            self._contract_address = Web3.to_checksum_address(clean_addr)
            try:
                abi = get_project_registry_abi()
                self._contract = self._w3.eth.contract(
                    address=self._contract_address,
                    abi=abi,
                )
            except Exception as e:
                raise BlockchainException(
                    code="BLOCKCHAIN_CONTRACT_ERROR",
                    message="Failed to load ProjectRegistry contract ABI or bind address.",
                    details={"error": str(e)},
                )

    # =========================================================================
    # DIAGNOSTICS & STATUS
    # =========================================================================

    def is_connected(self) -> bool:
        """Returns True if the Web3 RPC provider is responsive."""
        try:
            return bool(self._w3.is_connected())
        except Exception:
            return False

    def get_chain_id(self) -> int:
        """Retrieves the active EVM network chain ID."""
        try:
            return self._w3.eth.chain_id
        except Exception as e:
            raise BlockchainException(
                code="BLOCKCHAIN_CONNECTION_ERROR",
                message=f"Unable to retrieve chain ID from RPC node at {self._rpc_url}.",
                details={"error": str(e)},
            )

    def get_latest_block(self) -> int:
        """Retrieves the latest mined block number."""
        try:
            return self._w3.eth.block_number
        except Exception as e:
            raise BlockchainException(
                code="BLOCKCHAIN_CONNECTION_ERROR",
                message=f"Unable to retrieve latest block from RPC node at {self._rpc_url}.",
                details={"error": str(e)},
            )

    @property
    def relayer_address(self) -> Optional[str]:
        return self._relayer_address

    @property
    def contract_address(self) -> Optional[str]:
        return self._contract_address

    def _ensure_contract_ready(self) -> Any:
        """Ensures that contract and provider are properly configured before execution."""
        if self._contract is None:
            raise BlockchainException(
                code="BLOCKCHAIN_NOT_CONFIGURED",
                message="ProjectRegistry contract is not configured. Specify PROJECT_REGISTRY_CONTRACT_ADDRESS.",
            )
        return self._contract

    def _ensure_relayer_ready(self) -> Tuple[Any, str]:
        """Ensures that relayer account is initialized before state-changing transactions."""
        if self._relayer_account is None or self._relayer_address is None:
            raise BlockchainException(
                code="BLOCKCHAIN_CONFIGURATION_ERROR",
                message="Platform Gas Relayer is not configured. Provide RELAYER_PRIVATE_KEY.",
            )
        return self._relayer_account, self._relayer_address

    # =========================================================================
    # 1. REGISTER PROJECT VERSION (STATE CHANGING)
    # =========================================================================

    async def register_project_version(
        self,
        registration_id: str,
        composite_hash: str,
        ipfs_root_cid: str,
        version_index: int,
        lifecycle_stage: Union[str, int, Any],
        author: Optional[str] = None,
        co_authors: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Signs and broadcasts a registerProjectVersion transaction via the platform gas relayer.
        Awaits receipt confirmation depth, extracts block timestamp, and decodes the canonical event.
        """
        contract = self._ensure_contract_ready()
        relayer_account, relayer_address = self._ensure_relayer_ready()

        # Input Validations
        if not registration_id or not registration_id.strip():
            raise BlockchainException(
                code="BLOCKCHAIN_CONTRACT_ERROR",
                message="Registration ID cannot be empty.",
                status_code=422,
            )

        hash_bytes32 = sha256_to_bytes32(composite_hash)

        if not ipfs_root_cid or not ipfs_root_cid.strip():
            raise BlockchainException(
                code="BLOCKCHAIN_CONTRACT_ERROR",
                message="IPFS root CID cannot be empty.",
                status_code=422,
            )

        if version_index < 1:
            raise BlockchainException(
                code="BLOCKCHAIN_CONTRACT_ERROR",
                message="Version index must be >= 1.",
                status_code=422,
            )

        stage_int = lifecycle_stage_to_solidity(lifecycle_stage)
        norm_author = normalize_address(author)
        norm_co_authors = [normalize_address(a) for a in (co_authors or [])]

        # Chain ID check
        active_chain_id = self.get_chain_id()
        if active_chain_id != self._expected_chain_id:
            raise BlockchainException(
                code="BLOCKCHAIN_CHAIN_ID_MISMATCH",
                message=f"RPC chain ID {active_chain_id} does not match expected chain ID {self._expected_chain_id}.",
                details={"active_chain_id": active_chain_id, "expected_chain_id": self._expected_chain_id},
            )

        try:
            # Nonce and Gas Estimation
            nonce = self._w3.eth.get_transaction_count(relayer_address, "pending")
            function_call = contract.functions.registerProjectVersion(
                registration_id,
                hash_bytes32,
                ipfs_root_cid,
                version_index,
                stage_int,
                norm_author,
                norm_co_authors,
            )

            # Build transaction dictionary
            tx_params: Dict[str, Any] = {
                "from": relayer_address,
                "nonce": nonce,
                "chainId": active_chain_id,
            }

            try:
                gas_estimate = function_call.estimate_gas(tx_params)
                tx_params["gas"] = int(gas_estimate * 1.2)  # 20% safety margin
            except ContractLogicError as cle:
                raise BlockchainException(
                    code="BLOCKCHAIN_TRANSACTION_FAILED",
                    message=f"Smart contract simulation reverted: {str(cle)}",
                    details={"error": str(cle)},
                )
            except Exception as ge:
                # If estimation fails due to gas or node constraints, fallback to safe default
                tx_params["gas"] = 600000

            # Gas price strategy
            latest_block = self._w3.eth.get_block("latest")
            if "baseFeePerGas" in latest_block and latest_block["baseFeePerGas"] is not None:
                # EIP-1559 transaction
                base_fee = latest_block["baseFeePerGas"]
                max_priority_fee = self._w3.to_wei(2, "gwei")
                max_fee = int(base_fee * 1.5) + max_priority_fee
                tx_params["maxFeePerGas"] = max_fee
                tx_params["maxPriorityFeePerGas"] = max_priority_fee
            else:
                tx_params["gasPrice"] = self._w3.eth.gas_price

            built_tx = function_call.build_transaction(tx_params)

            # Sign transaction
            signed_tx = self._w3.eth.account.sign_transaction(built_tx, relayer_account.key)

            # Broadcast raw transaction
            tx_hash_bytes = self._w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_hash = tx_hash_bytes.hex()
            if not tx_hash.startswith("0x"):
                tx_hash = "0x" + tx_hash

            # Wait for receipt and confirmations
            receipt = self._w3.eth.wait_for_transaction_receipt(
                tx_hash_bytes,
                timeout=self._timeout,
            )

        except BlockchainException:
            raise
        except ContractLogicError as cle:
            raise BlockchainException(
                code="BLOCKCHAIN_TRANSACTION_FAILED",
                message=f"Smart contract transaction reverted: {str(cle)}",
                details={"error": str(cle)},
            )
        except TransactionNotFound:
            raise BlockchainException(
                code="BLOCKCHAIN_TRANSACTION_TIMEOUT",
                message=f"Transaction timed out awaiting confirmation after {self._timeout}s.",
            )
        except Exception as e:
            err_msg = str(e).lower()
            if "insufficient funds" in err_msg or "balance" in err_msg:
                raise BlockchainException(
                    code="BLOCKCHAIN_INSUFFICIENT_FUNDS",
                    message="Relayer wallet has insufficient funds to pay gas fees.",
                )
            raise BlockchainException(
                code="BLOCKCHAIN_TRANSACTION_FAILED",
                message=f"Blockchain transaction failed: {str(e)}",
                details={"error": str(e)},
            )

        status = receipt.get("status") if isinstance(receipt, dict) else getattr(receipt, "status", None)
        block_num = receipt.get("blockNumber") if isinstance(receipt, dict) else getattr(receipt, "blockNumber", None)
        gas_used = receipt.get("gasUsed") if isinstance(receipt, dict) else getattr(receipt, "gasUsed", None)

        if status != 1:
            raise BlockchainException(
                code="BLOCKCHAIN_TRANSACTION_FAILED",
                message=f"Transaction mined but reverted with status {status}.",
                details={"transaction_hash": tx_hash, "receipt": str(receipt)},
            )

        # Check confirmation depth if requested
        if self._confirmation_blocks > 1 and block_num is not None:
            current_height = self._w3.eth.block_number
            confirmations = current_height - block_num + 1
            if confirmations < self._confirmation_blocks:
                logger.info(
                    f"Transaction {tx_hash} has {confirmations} confirmations; configured for {self._confirmation_blocks}"
                )

        # Retrieve block timestamp
        mined_block = self._w3.eth.get_block(block_num)
        anchored_dt = datetime.fromtimestamp(mined_block["timestamp"], tz=timezone.utc)

        # Decode event log
        event_data = self.decode_project_version_registered(receipt)

        return {
            "transaction_hash": tx_hash,
            "block_number": block_num,
            "gas_used": gas_used,
            "anchored_timestamp": anchored_dt,
            "record_id": event_data.get("recordId") if event_data else None,
            "event_data": event_data,
        }

    # =========================================================================
    # 2. TRUSTLESS VERIFICATION (VIEW ONLY)
    # =========================================================================

    def verify_project_version(
        self,
        registration_id: str,
        expected_hash: str,
    ) -> Dict[str, Any]:
        """
        Public trustless verification calling ProjectRegistry.verifyProjectVersion(regId, hash).
        Does NOT revert on non-existent registration or hash mismatch.
        """
        contract = self._ensure_contract_ready()
        hash_bytes32 = sha256_to_bytes32(expected_hash)

        try:
            is_valid, timestamp, ipfs_cid, author, dispute_state_int = (
                contract.functions.verifyProjectVersion(registration_id, hash_bytes32).call()
            )
        except Exception as e:
            if isinstance(e, BlockchainException):
                raise
            err_str = str(e).lower()
            if "timeout" in err_str or "timed out" in err_str:
                raise BlockchainException(
                    code="BLOCKCHAIN_TIMEOUT",
                    message=f"Blockchain call verifyProjectVersion timed out: {str(e)}",
                    status_code=504,
                    details={"registration_id": registration_id, "error": str(e)},
                )
            if (
                "connection" in err_str
                or "connect" in err_str
                or "refused" in err_str
                or "network" in err_str
            ):
                raise BlockchainException(
                    code="BLOCKCHAIN_CONNECTION_ERROR",
                    message=f"RPC connection failed for verifyProjectVersion: {str(e)}",
                    status_code=502,
                    details={"registration_id": registration_id, "error": str(e)},
                )
            raise BlockchainException(
                code="BLOCKCHAIN_CONTRACT_ERROR",
                message=f"Contract call verifyProjectVersion failed: {str(e)}",
                details={"registration_id": registration_id, "error": str(e)},
            )

        anchored_dt = None
        if timestamp > 0:
            anchored_dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)

        dispute_status_str = INT_TO_DISPUTE_STATUS.get(dispute_state_int, "NONE")

        return {
            "is_valid": bool(is_valid),
            "anchored_timestamp": anchored_dt,
            "ipfs_root_cid": ipfs_cid or None,
            "author_wallet": author if author != ethers_zero_address() else None,
            "dispute_status": dispute_status_str,
            "match_confirmed": bool(is_valid),
            "registration_id": registration_id,
            "smart_contract_address": self._contract_address,
        }

    # =========================================================================
    # 3. GET PROJECT VERSION STRUCT (VIEW ONLY)
    # =========================================================================

    def get_project_version(self, registration_id: str) -> Dict[str, Any]:
        """
        Retrieves the complete on-chain VersionProof struct for a registration ID.
        Reverts with VersionNotFound if not found.
        """
        contract = self._ensure_contract_ready()

        try:
            proof = contract.functions.getProjectVersion(registration_id).call()
        except ContractLogicError as cle:
            if "VersionNotFound" in str(cle):
                raise BlockchainException(
                    code="VERSION_NOT_FOUND",
                    message=f"No on-chain proof found for registration ID '{registration_id}'.",
                    status_code=404,
                )
            raise BlockchainException(
                code="BLOCKCHAIN_CONTRACT_ERROR",
                message=f"Contract error retrieving version proof: {str(cle)}",
            )
        except Exception as e:
            if isinstance(e, BlockchainException):
                raise
            err_str = str(e).lower()
            if "versionnotfound" in err_str:
                raise BlockchainException(
                    code="VERSION_NOT_FOUND",
                    message=f"No on-chain proof found for registration ID '{registration_id}'.",
                    status_code=404,
                )
            if "timeout" in err_str or "timed out" in err_str:
                raise BlockchainException(
                    code="BLOCKCHAIN_TIMEOUT",
                    message=f"Blockchain call getProjectVersion timed out: {str(e)}",
                    status_code=504,
                    details={"registration_id": registration_id, "error": str(e)},
                )
            if (
                "connection" in err_str
                or "connect" in err_str
                or "refused" in err_str
                or "network" in err_str
            ):
                raise BlockchainException(
                    code="BLOCKCHAIN_CONNECTION_ERROR",
                    message=f"RPC connection failed for getProjectVersion: {str(e)}",
                    status_code=502,
                    details={"registration_id": registration_id, "error": str(e)},
                )
            raise BlockchainException(
                code="BLOCKCHAIN_CONTRACT_ERROR",
                message=f"Failed to query getProjectVersion: {str(e)}",
            )

        # Decode tuple fields corresponding to VersionProof struct
        (
            record_id,
            reg_id,
            comp_hash,
            ipfs_cid,
            ver_index,
            stage_int,
            author,
            co_authors,
            timestamp,
            block_num,
            dispute_state_int,
            exists,
        ) = proof

        if not exists:
            raise BlockchainException(
                code="VERSION_NOT_FOUND",
                message=f"No on-chain proof found for registration ID '{registration_id}'.",
                status_code=404,
            )

        hash_hex = comp_hash.hex() if hasattr(comp_hash, "hex") else bytes(comp_hash).hex()
        if not hash_hex.startswith("0x"):
            hash_hex = "0x" + hash_hex

        anchored_dt = datetime.fromtimestamp(timestamp, tz=timezone.utc) if timestamp > 0 else None

        return {
            "record_id": record_id,
            "registration_id": reg_id,
            "composite_hash": hash_hex,
            "ipfs_root_cid": ipfs_cid,
            "version_index": ver_index,
            "lifecycle_stage": INT_TO_LIFECYCLE_STAGE.get(stage_int, "IDEA"),
            "author": author,
            "co_authors": list(co_authors),
            "anchored_timestamp": anchored_dt,
            "block_number": block_num,
            "dispute_state": INT_TO_DISPUTE_STATUS.get(dispute_state_int, "NONE"),
            "exists": exists,
        }

    # =========================================================================
    # 4. DISPUTE MANAGEMENT (STATE CHANGING)
    # =========================================================================

    async def raise_dispute(
        self,
        registration_id: str,
        evidence_cid: str,
    ) -> Dict[str, Any]:
        """
        Submits an on-chain dispute notice against an anchored version.
        """
        contract = self._ensure_contract_ready()
        relayer_account, relayer_address = self._ensure_relayer_ready()

        if not registration_id:
            raise BlockchainException(
                code="BLOCKCHAIN_CONTRACT_ERROR",
                message="Registration ID cannot be empty.",
                status_code=422,
            )
        if not evidence_cid:
            raise BlockchainException(
                code="BLOCKCHAIN_CONTRACT_ERROR",
                message="Dispute evidence CID cannot be empty.",
                status_code=422,
            )

        try:
            nonce = self._w3.eth.get_transaction_count(relayer_address, "pending")
            function_call = contract.functions.raiseDispute(registration_id, evidence_cid)

            tx_params = {
                "from": relayer_address,
                "nonce": nonce,
                "chainId": self.get_chain_id(),
                "gas": 300000,
                "gasPrice": self._w3.eth.gas_price,
            }

            built_tx = function_call.build_transaction(tx_params)
            signed_tx = self._w3.eth.account.sign_transaction(built_tx, relayer_account.key)
            tx_hash = self._w3.eth.send_raw_transaction(signed_tx.raw_transaction)

            receipt = self._w3.eth.wait_for_transaction_receipt(tx_hash, timeout=self._timeout)

        except ContractLogicError as cle:
            err_str = str(cle).lower()
            if "activedisputeexists" in err_str:
                raise BlockchainException(
                    code="ACTIVE_DISPUTE_EXISTS",
                    message=f"An active dispute already exists for registration '{registration_id}'.",
                    status_code=409,
                    details={"registration_id": registration_id, "error": str(cle)},
                )
            if "versionnotfound" in err_str:
                raise BlockchainException(
                    code="VERSION_NOT_FOUND",
                    message=f"Registration ID '{registration_id}' not found on-chain.",
                    status_code=404,
                    details={"registration_id": registration_id, "error": str(cle)},
                )
            raise BlockchainException(
                code="BLOCKCHAIN_TRANSACTION_FAILED",
                message=f"raiseDispute transaction reverted: {str(cle)}",
                status_code=502,
                details={"registration_id": registration_id, "error": str(cle)},
            )
        except Exception as e:
            if isinstance(e, BlockchainException):
                raise
            err_str = str(e).lower()
            if "activedisputeexists" in err_str:
                raise BlockchainException(
                    code="ACTIVE_DISPUTE_EXISTS",
                    message=f"An active dispute already exists for registration '{registration_id}'.",
                    status_code=409,
                    details={"registration_id": registration_id, "error": str(e)},
                )
            if "timeout" in err_str or "timed out" in err_str:
                raise BlockchainException(
                    code="BLOCKCHAIN_TIMEOUT",
                    message=f"raiseDispute transaction timed out: {str(e)}",
                    status_code=504,
                    details={"registration_id": registration_id, "error": str(e)},
                )
            if (
                "connection" in err_str
                or "connect" in err_str
                or "refused" in err_str
                or "network" in err_str
            ):
                raise BlockchainException(
                    code="BLOCKCHAIN_CONNECTION_ERROR",
                    message=f"RPC connection failed for raiseDispute: {str(e)}",
                    status_code=502,
                    details={"registration_id": registration_id, "error": str(e)},
                )
            raise BlockchainException(
                code="BLOCKCHAIN_TRANSACTION_FAILED",
                message=f"raiseDispute failed: {str(e)}",
                status_code=502,
                details={"registration_id": registration_id, "error": str(e)},
            )

        status = receipt.get("status") if isinstance(receipt, dict) else getattr(receipt, "status", None)
        block_num = receipt.get("blockNumber") if isinstance(receipt, dict) else getattr(receipt, "blockNumber", None)
        tx_hash_val = receipt.get("transactionHash") if isinstance(receipt, dict) else getattr(receipt, "transactionHash", None)
        tx_hash_str = tx_hash_val.hex() if hasattr(tx_hash_val, "hex") else str(tx_hash_val)

        if status != 1:
            raise BlockchainException(
                code="BLOCKCHAIN_TRANSACTION_FAILED",
                message="raiseDispute reverted on-chain.",
            )

        event_data = self.decode_dispute_logged(receipt)
        return {
            "transaction_hash": tx_hash_str,
            "block_number": block_num,
            "event_data": event_data,
        }

    async def resolve_dispute(
        self,
        registration_id: str,
        status: Union[str, int, Any],
    ) -> Dict[str, Any]:
        """
        Adjudicates an on-chain dispute (restricted to contract owner).
        Permitted resolution statuses: RESOLVED (3) or REJECTED (4).
        """
        contract = self._ensure_contract_ready()
        relayer_account, relayer_address = self._ensure_relayer_ready()

        # Translate status
        if isinstance(status, int):
            status_int = status
        else:
            status_str = status.value if hasattr(status, "value") else str(status)
            status_int = DISPUTE_STATUS_TO_INT.get(status_str.strip().upper(), -1)

        if status_int not in (3, 4):  # RESOLVED or REJECTED
            raise BlockchainException(
                code="BLOCKCHAIN_CONTRACT_ERROR",
                message=f"Invalid dispute resolution status {status}. Must be RESOLVED (3) or REJECTED (4).",
                status_code=422,
            )

        try:
            nonce = self._w3.eth.get_transaction_count(relayer_address, "pending")
            function_call = contract.functions.resolveDispute(registration_id, status_int)

            tx_params = {
                "from": relayer_address,
                "nonce": nonce,
                "chainId": self.get_chain_id(),
                "gas": 300000,
                "gasPrice": self._w3.eth.gas_price,
            }

            built_tx = function_call.build_transaction(tx_params)
            signed_tx = self._w3.eth.account.sign_transaction(built_tx, relayer_account.key)
            tx_hash = self._w3.eth.send_raw_transaction(signed_tx.raw_transaction)

            receipt = self._w3.eth.wait_for_transaction_receipt(tx_hash, timeout=self._timeout)

        except ContractLogicError as cle:
            err_str = str(cle).lower()
            if "versionnotfound" in err_str:
                raise BlockchainException(
                    code="VERSION_NOT_FOUND",
                    message=f"Registration ID '{registration_id}' not found on-chain.",
                    status_code=404,
                    details={"registration_id": registration_id, "error": str(cle)},
                )
            raise BlockchainException(
                code="BLOCKCHAIN_TRANSACTION_FAILED",
                message=f"resolveDispute transaction reverted: {str(cle)}",
                status_code=502,
                details={"registration_id": registration_id, "error": str(cle)},
            )
        except Exception as e:
            if isinstance(e, BlockchainException):
                raise
            err_str = str(e).lower()
            if "timeout" in err_str or "timed out" in err_str:
                raise BlockchainException(
                    code="BLOCKCHAIN_TIMEOUT",
                    message=f"resolveDispute transaction timed out: {str(e)}",
                    status_code=504,
                    details={"registration_id": registration_id, "error": str(e)},
                )
            if (
                "connection" in err_str
                or "connect" in err_str
                or "refused" in err_str
                or "network" in err_str
            ):
                raise BlockchainException(
                    code="BLOCKCHAIN_CONNECTION_ERROR",
                    message=f"RPC connection failed for resolveDispute: {str(e)}",
                    status_code=502,
                    details={"registration_id": registration_id, "error": str(e)},
                )
            raise BlockchainException(
                code="BLOCKCHAIN_TRANSACTION_FAILED",
                message=f"resolveDispute failed: {str(e)}",
                status_code=502,
                details={"registration_id": registration_id, "error": str(e)},
            )

        res_status = receipt.get("status") if isinstance(receipt, dict) else getattr(receipt, "status", None)
        block_num = receipt.get("blockNumber") if isinstance(receipt, dict) else getattr(receipt, "blockNumber", None)
        tx_hash_val = receipt.get("transactionHash") if isinstance(receipt, dict) else getattr(receipt, "transactionHash", None)
        tx_hash_str = tx_hash_val.hex() if hasattr(tx_hash_val, "hex") else str(tx_hash_val)

        if res_status != 1:
            raise BlockchainException(
                code="BLOCKCHAIN_TRANSACTION_FAILED",
                message="resolveDispute reverted on-chain.",
            )

        event_data = self.decode_dispute_resolved(receipt)
        return {
            "transaction_hash": tx_hash_str,
            "block_number": block_num,
            "event_data": event_data,
        }

    # =========================================================================
    # 5. EVENT DECODERS
    # =========================================================================

    def decode_project_version_registered(self, receipt: Any) -> Optional[Dict[str, Any]]:
        """Extracts and parses the ProjectVersionRegistered event from a transaction receipt."""
        if not self._contract:
            return None
        try:
            logs = self._contract.events.ProjectVersionRegistered().process_receipt(receipt)
            if logs:
                return dict(logs[0]["args"])
        except Exception as e:
            logger.warning(f"Failed to decode ProjectVersionRegistered event: {e}")
        return None

    def decode_dispute_logged(self, receipt: Any) -> Optional[Dict[str, Any]]:
        """Extracts and parses the DisputeLogged event from a transaction receipt."""
        if not self._contract:
            return None
        try:
            logs = self._contract.events.DisputeLogged().process_receipt(receipt)
            if logs:
                return dict(logs[0]["args"])
        except Exception as e:
            logger.warning(f"Failed to decode DisputeLogged event: {e}")
        return None

    def decode_dispute_resolved(self, receipt: Any) -> Optional[Dict[str, Any]]:
        """Extracts and parses the DisputeResolved event from a transaction receipt."""
        if not self._contract:
            return None
        try:
            logs = self._contract.events.DisputeResolved().process_receipt(receipt)
            if logs:
                return dict(logs[0]["args"])
        except Exception as e:
            logger.warning(f"Failed to decode DisputeResolved event: {e}")
        return None


def ethers_zero_address() -> str:
    return "0x0000000000000000000000000000000000000000"


# Global singleton instance management
_global_blockchain_service: Optional[BlockchainService] = None


def get_blockchain_service() -> BlockchainService:
    """Returns the active global BlockchainService singleton."""
    global _global_blockchain_service
    if _global_blockchain_service is None:
        _global_blockchain_service = BlockchainService()
    return _global_blockchain_service


def set_blockchain_service(service: Optional[BlockchainService]) -> None:
    """Overrides the active global BlockchainService (primarily for testing)."""
    global _global_blockchain_service
    _global_blockchain_service = service
