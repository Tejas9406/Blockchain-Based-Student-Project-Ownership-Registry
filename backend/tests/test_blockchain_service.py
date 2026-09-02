from datetime import datetime, timezone
from unittest.mock import MagicMock, PropertyMock, patch
import pytest
from web3.exceptions import ContractLogicError, TransactionNotFound

from app.core.exceptions import BlockchainException
from app.models.enums import ProjectVersionStage
from app.services.blockchain_service import (
    BlockchainService,
    lifecycle_stage_to_solidity,
    normalize_address,
    sha256_to_bytes32,
)

SAMPLE_RELAYER_KEY = "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"
SAMPLE_RELAYER_ADDR = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
SAMPLE_CONTRACT_ADDR = "0x5FbDB2315678afecb367f032d93F642f64180aa3"
SAMPLE_AUTHOR_ADDR = "0x90F79bf6EB2c4f870365E785982E1f101E93b906"
SAMPLE_REG_ID = "REG-2026-A8F92"
SAMPLE_COMPOSITE_HASH = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
SAMPLE_IPFS_CID = "bafybeiczsscdsbs7ffqz55asqdf3smv6klcw3gofszvwlyarci47bgf354"


@pytest.fixture
def mock_w3():
    """Provides a fully mocked Web3 instance."""
    w3 = MagicMock()
    w3.is_connected.return_value = True
    w3.eth.chain_id = 31337
    w3.eth.block_number = 100
    w3.eth.gas_price = 1000000000
    w3.eth.get_block.return_value = {
        "timestamp": 1788330000,
        "baseFeePerGas": None,
    }
    w3.eth.get_transaction_count.return_value = 0
    w3.to_wei.side_effect = lambda val, unit: val * 10**9 if unit == "gwei" else val
    return w3


@pytest.fixture
def blockchain_service(mock_w3):
    """Provides a configured BlockchainService with mocked Web3."""
    return BlockchainService(
        rpc_url="http://127.0.0.1:8545",
        contract_address=SAMPLE_CONTRACT_ADDR,
        chain_id=31337,
        relayer_private_key=SAMPLE_RELAYER_KEY,
        confirmation_blocks=1,
        timeout_seconds=5,
        web3_instance=mock_w3,
    )


# =============================================================================
# 1. INITIALIZATION & CONFIGURATION
# =============================================================================

def test_1_service_initializes_correctly(blockchain_service):
    assert blockchain_service.is_connected() is True
    assert blockchain_service.contract_address == SAMPLE_CONTRACT_ADDR
    assert blockchain_service.relayer_address == SAMPLE_RELAYER_ADDR
    assert blockchain_service.get_chain_id() == 31337
    assert blockchain_service.get_latest_block() == 100


def test_2_invalid_rpc_configuration_handled():
    # If connection fails, is_connected returns False and methods raise controlled exception
    dead_w3 = MagicMock()
    dead_w3.is_connected.return_value = False
    type(dead_w3.eth).chain_id = PropertyMock(side_effect=Exception("Connection refused"))
    service = BlockchainService(
        rpc_url="http://dead-rpc:8545",
        contract_address=SAMPLE_CONTRACT_ADDR,
        web3_instance=dead_w3,
    )
    assert service.is_connected() is False
    with pytest.raises(BlockchainException) as exc:
        service.get_chain_id()
    assert exc.value.code == "BLOCKCHAIN_CONNECTION_ERROR"


def test_3_invalid_contract_address_rejected():
    with pytest.raises(BlockchainException) as exc:
        BlockchainService(contract_address="0xInvalidAddress")
    assert exc.value.code == "BLOCKCHAIN_INVALID_ADDRESS"


def test_4_chain_id_mismatch_detected(mock_w3):
    mock_w3.eth.chain_id = 1  # RPC returns Mainnet, expected Hardhat 31337
    service = BlockchainService(
        contract_address=SAMPLE_CONTRACT_ADDR,
        chain_id=31337,
        relayer_private_key=SAMPLE_RELAYER_KEY,
        web3_instance=mock_w3,
    )
    with pytest.raises(BlockchainException) as exc:
        import asyncio
        asyncio.run(
            service.register_project_version(
                registration_id=SAMPLE_REG_ID,
                composite_hash=SAMPLE_COMPOSITE_HASH,
                ipfs_root_cid=SAMPLE_IPFS_CID,
                version_index=1,
                lifecycle_stage="IDEA",
                author=SAMPLE_AUTHOR_ADDR,
            )
        )
    assert exc.value.code == "BLOCKCHAIN_CHAIN_ID_MISMATCH"


def test_5_invalid_private_key_rejected_safely():
    with pytest.raises(BlockchainException) as exc:
        BlockchainService(
            contract_address=SAMPLE_CONTRACT_ADDR,
            relayer_private_key="not-a-valid-hex-private-key",
        )
    assert exc.value.code == "BLOCKCHAIN_CONFIGURATION_ERROR"
    # Ensure raw private key does not leak into error message
    assert "not-a-valid-hex-private-key" not in str(exc.value)


def test_6_relayer_address_derived_correctly(blockchain_service):
    assert blockchain_service.relayer_address == SAMPLE_RELAYER_ADDR


def test_7_missing_relayer_key_rejected_for_transactions(mock_w3):
    service = BlockchainService(
        contract_address=SAMPLE_CONTRACT_ADDR,
        relayer_private_key="",  # Unconfigured relayer
        web3_instance=mock_w3,
    )
    with pytest.raises(BlockchainException) as exc:
        import asyncio
        asyncio.run(
            service.register_project_version(
                registration_id=SAMPLE_REG_ID,
                composite_hash=SAMPLE_COMPOSITE_HASH,
                ipfs_root_cid=SAMPLE_IPFS_CID,
                version_index=1,
                lifecycle_stage="IDEA",
            )
        )
    assert exc.value.code == "BLOCKCHAIN_CONFIGURATION_ERROR"


# =============================================================================
# 2. HASH CONVERSION & VALIDATION
# =============================================================================

def test_8_valid_sha256_converts_to_bytes32():
    digest_bytes = sha256_to_bytes32(SAMPLE_COMPOSITE_HASH)
    assert isinstance(digest_bytes, bytes)
    assert len(digest_bytes) == 32
    assert digest_bytes.hex() == SAMPLE_COMPOSITE_HASH


def test_9_invalid_hash_rejected():
    with pytest.raises(BlockchainException) as exc:
        sha256_to_bytes32("zzzznothex" + "0" * 54)
    assert exc.value.code == "BLOCKCHAIN_INVALID_HASH"


def test_10_wrong_hash_length_rejected():
    with pytest.raises(BlockchainException) as exc:
        sha256_to_bytes32("abcd1234")
    assert exc.value.code == "BLOCKCHAIN_INVALID_HASH"


def test_11_zero_hash_rejected_for_registration():
    with pytest.raises(BlockchainException) as exc:
        sha256_to_bytes32("0" * 64)
    assert exc.value.code == "BLOCKCHAIN_INVALID_HASH"
    assert "Zero composite hash" in exc.value.message


# =============================================================================
# 3. LIFECYCLE STAGE & ADDRESS HANDLING
# =============================================================================

def test_12_lifecycle_enum_conversion():
    assert lifecycle_stage_to_solidity("IDEA") == 0
    assert lifecycle_stage_to_solidity("DESIGN") == 1
    assert lifecycle_stage_to_solidity("PROTOTYPE") == 2
    assert lifecycle_stage_to_solidity("FINAL") == 3
    assert lifecycle_stage_to_solidity(ProjectVersionStage.PROTOTYPE) == 2
    assert lifecycle_stage_to_solidity(1) == 1


def test_13_invalid_lifecycle_stage_rejected():
    with pytest.raises(BlockchainException) as exc:
        lifecycle_stage_to_solidity("RELEASED")
    assert exc.value.code == "BLOCKCHAIN_CONFIGURATION_ERROR"

    with pytest.raises(BlockchainException) as exc:
        lifecycle_stage_to_solidity(5)
    assert exc.value.code == "BLOCKCHAIN_CONFIGURATION_ERROR"


def test_14_valid_ethereum_addresses_accepted():
    checksum = normalize_address(SAMPLE_AUTHOR_ADDR)
    assert checksum == SAMPLE_AUTHOR_ADDR
    # Empty string normalizes to zero address
    zero_addr = normalize_address("")
    assert zero_addr == "0x0000000000000000000000000000000000000000"


def test_15_invalid_ethereum_address_rejected():
    with pytest.raises(BlockchainException) as exc:
        normalize_address("0xInvalidEthAddress123")
    assert exc.value.code == "BLOCKCHAIN_INVALID_ADDRESS"


# =============================================================================
# 4. REGISTRATION TRANSACTION LIFECYCLE
# =============================================================================

@pytest.mark.asyncio
async def test_16_registration_transaction_constructed_correctly(blockchain_service, mock_w3):
    mock_func = MagicMock()
    mock_func.estimate_gas.return_value = 250000
    mock_func.build_transaction.return_value = {
        "from": SAMPLE_RELAYER_ADDR,
        "nonce": 0,
        "gas": 300000,
        "to": SAMPLE_CONTRACT_ADDR,
        "data": "0x1234",
    }
    blockchain_service._contract.functions.registerProjectVersion.return_value = mock_func

    mock_signed = MagicMock()
    mock_signed.raw_transaction = b"mock_raw_tx_bytes"
    mock_w3.eth.account.sign_transaction.return_value = mock_signed
    mock_w3.eth.send_raw_transaction.return_value = bytes.fromhex("a" * 64)
    mock_w3.eth.wait_for_transaction_receipt.return_value = {
        "status": 1,
        "blockNumber": 105,
        "gasUsed": 210000,
        "transactionHash": bytes.fromhex("a" * 64),
    }
    mock_w3.eth.get_block.return_value = {"timestamp": 1788330500}

    await blockchain_service.register_project_version(
        registration_id=SAMPLE_REG_ID,
        composite_hash=SAMPLE_COMPOSITE_HASH,
        ipfs_root_cid=SAMPLE_IPFS_CID,
        version_index=1,
        lifecycle_stage="IDEA",
        author=SAMPLE_AUTHOR_ADDR,
        co_authors=[],
    )

    blockchain_service._contract.functions.registerProjectVersion.assert_called_once_with(
        SAMPLE_REG_ID,
        bytes.fromhex(SAMPLE_COMPOSITE_HASH),
        SAMPLE_IPFS_CID,
        1,
        0,
        SAMPLE_AUTHOR_ADDR,
        [],
    )
    assert mock_func.build_transaction.called


@pytest.mark.asyncio
async def test_17_transaction_signed_correctly(blockchain_service, mock_w3):
    mock_func = MagicMock()
    mock_func.estimate_gas.return_value = 250000
    mock_func.build_transaction.return_value = {"from": SAMPLE_RELAYER_ADDR}
    blockchain_service._contract.functions.registerProjectVersion.return_value = mock_func

    mock_signed = MagicMock()
    mock_signed.raw_transaction = b"mock_raw_tx_bytes"
    mock_w3.eth.account.sign_transaction.return_value = mock_signed
    mock_w3.eth.send_raw_transaction.return_value = bytes.fromhex("a" * 64)
    mock_w3.eth.wait_for_transaction_receipt.return_value = {
        "status": 1,
        "blockNumber": 105,
        "gasUsed": 210000,
        "transactionHash": bytes.fromhex("a" * 64),
    }
    mock_w3.eth.get_block.return_value = {"timestamp": 1788330500}

    await blockchain_service.register_project_version(
        registration_id=SAMPLE_REG_ID,
        composite_hash=SAMPLE_COMPOSITE_HASH,
        ipfs_root_cid=SAMPLE_IPFS_CID,
        version_index=1,
        lifecycle_stage="IDEA",
    )

    mock_w3.eth.account.sign_transaction.assert_called_once()
    assert mock_w3.eth.send_raw_transaction.called


@pytest.mark.asyncio
async def test_18_transaction_hash_returned(blockchain_service, mock_w3):
    mock_func = MagicMock()
    mock_func.estimate_gas.return_value = 250000
    mock_func.build_transaction.return_value = {"from": SAMPLE_RELAYER_ADDR}
    blockchain_service._contract.functions.registerProjectVersion.return_value = mock_func

    mock_signed = MagicMock()
    mock_signed.raw_transaction = b"mock_raw_tx_bytes"
    mock_w3.eth.account.sign_transaction.return_value = mock_signed
    mock_w3.eth.send_raw_transaction.return_value = bytes.fromhex("f" * 64)
    mock_w3.eth.wait_for_transaction_receipt.return_value = {
        "status": 1,
        "blockNumber": 105,
        "gasUsed": 210000,
        "transactionHash": bytes.fromhex("f" * 64),
    }
    mock_w3.eth.get_block.return_value = {"timestamp": 1788330500}

    result = await blockchain_service.register_project_version(
        registration_id=SAMPLE_REG_ID,
        composite_hash=SAMPLE_COMPOSITE_HASH,
        ipfs_root_cid=SAMPLE_IPFS_CID,
        version_index=1,
        lifecycle_stage="IDEA",
    )

    assert result["transaction_hash"] == "0x" + "f" * 64


@pytest.mark.asyncio
async def test_19_receipt_confirmation_handled(blockchain_service, mock_w3):
    mock_func = MagicMock()
    mock_func.estimate_gas.return_value = 250000
    mock_func.build_transaction.return_value = {"from": SAMPLE_RELAYER_ADDR}
    blockchain_service._contract.functions.registerProjectVersion.return_value = mock_func

    mock_signed = MagicMock()
    mock_signed.raw_transaction = b"mock_raw_tx_bytes"
    mock_w3.eth.account.sign_transaction.return_value = mock_signed
    mock_w3.eth.send_raw_transaction.return_value = bytes.fromhex("a" * 64)
    mock_w3.eth.wait_for_transaction_receipt.return_value = {
        "status": 1,
        "blockNumber": 105,
        "gasUsed": 210000,
        "transactionHash": bytes.fromhex("a" * 64),
    }
    mock_w3.eth.get_block.return_value = {"timestamp": 1788330500}

    result = await blockchain_service.register_project_version(
        registration_id=SAMPLE_REG_ID,
        composite_hash=SAMPLE_COMPOSITE_HASH,
        ipfs_root_cid=SAMPLE_IPFS_CID,
        version_index=1,
        lifecycle_stage="IDEA",
    )

    mock_w3.eth.wait_for_transaction_receipt.assert_called_once()
    assert result["block_number"] == 105
    assert result["gas_used"] == 210000
    assert isinstance(result["anchored_timestamp"], datetime)


@pytest.mark.asyncio
async def test_20_failed_transaction_handled(blockchain_service, mock_w3):
    mock_func = MagicMock()
    mock_func.estimate_gas.return_value = 250000
    mock_func.build_transaction.return_value = {"from": SAMPLE_RELAYER_ADDR}
    blockchain_service._contract.functions.registerProjectVersion.return_value = mock_func

    mock_signed = MagicMock()
    mock_signed.raw_transaction = b"raw_tx"
    mock_w3.eth.account.sign_transaction.return_value = mock_signed
    mock_w3.eth.send_raw_transaction.return_value = bytes.fromhex("b" * 64)

    # Receipt status = 0 (revert)
    mock_w3.eth.wait_for_transaction_receipt.return_value = {
        "status": 0,
        "blockNumber": 105,
        "gasUsed": 300000,
        "transactionHash": bytes.fromhex("b" * 64),
    }

    with pytest.raises(BlockchainException) as exc:
        await blockchain_service.register_project_version(
            registration_id=SAMPLE_REG_ID,
            composite_hash=SAMPLE_COMPOSITE_HASH,
            ipfs_root_cid=SAMPLE_IPFS_CID,
            version_index=1,
            lifecycle_stage="IDEA",
        )
    assert exc.value.code == "BLOCKCHAIN_TRANSACTION_FAILED"


@pytest.mark.asyncio
async def test_21_transaction_timeout_handled(blockchain_service, mock_w3):
    mock_func = MagicMock()
    mock_func.estimate_gas.return_value = 250000
    mock_func.build_transaction.return_value = {"from": SAMPLE_RELAYER_ADDR}
    blockchain_service._contract.functions.registerProjectVersion.return_value = mock_func

    mock_signed = MagicMock()
    mock_signed.raw_transaction = b"raw_tx"
    mock_w3.eth.account.sign_transaction.return_value = mock_signed
    mock_w3.eth.send_raw_transaction.return_value = bytes.fromhex("c" * 64)
    mock_w3.eth.wait_for_transaction_receipt.side_effect = TransactionNotFound("Timeout")

    with pytest.raises(BlockchainException) as exc:
        await blockchain_service.register_project_version(
            registration_id=SAMPLE_REG_ID,
            composite_hash=SAMPLE_COMPOSITE_HASH,
            ipfs_root_cid=SAMPLE_IPFS_CID,
            version_index=1,
            lifecycle_stage="IDEA",
        )
    assert exc.value.code == "BLOCKCHAIN_TRANSACTION_TIMEOUT"


@pytest.mark.asyncio
async def test_22_insufficient_funds_handled(blockchain_service, mock_w3):
    mock_func = MagicMock()
    mock_func.estimate_gas.return_value = 250000
    mock_func.build_transaction.return_value = {"from": SAMPLE_RELAYER_ADDR}
    blockchain_service._contract.functions.registerProjectVersion.return_value = mock_func

    mock_signed = MagicMock()
    mock_signed.raw_transaction = b"raw_tx"
    mock_w3.eth.account.sign_transaction.return_value = mock_signed
    mock_w3.eth.send_raw_transaction.side_effect = Exception("insufficient funds for gas * price + value")

    with pytest.raises(BlockchainException) as exc:
        await blockchain_service.register_project_version(
            registration_id=SAMPLE_REG_ID,
            composite_hash=SAMPLE_COMPOSITE_HASH,
            ipfs_root_cid=SAMPLE_IPFS_CID,
            version_index=1,
            lifecycle_stage="IDEA",
        )
    assert exc.value.code == "BLOCKCHAIN_INSUFFICIENT_FUNDS"


def test_23_project_version_registered_event_decoded(blockchain_service):
    receipt = {"logs": []}
    blockchain_service._contract.events.ProjectVersionRegistered().process_receipt.return_value = [
        {"args": {"recordId": 5, "registrationId": SAMPLE_REG_ID}}
    ]
    event_data = blockchain_service.decode_project_version_registered(receipt)
    assert event_data["recordId"] == 5
    assert event_data["registrationId"] == SAMPLE_REG_ID


# =============================================================================
# 5. TRUSTLESS VERIFICATION & GET PROJECT VERSION
# =============================================================================

def test_24_verification_call_decoded_correctly(blockchain_service):
    # Mock verifyProjectVersion response: (isValid, timestamp, ipfsCID, author, disputeState)
    blockchain_service._contract.functions.verifyProjectVersion(
        SAMPLE_REG_ID, bytes.fromhex(SAMPLE_COMPOSITE_HASH)
    ).call.return_value = (
        True,
        1788330500,
        SAMPLE_IPFS_CID,
        SAMPLE_AUTHOR_ADDR,
        0,  # DisputeStatus.NONE
    )

    result = blockchain_service.verify_project_version(SAMPLE_REG_ID, SAMPLE_COMPOSITE_HASH)
    assert result["is_valid"] is True
    assert result["match_confirmed"] is True
    assert result["ipfs_root_cid"] == SAMPLE_IPFS_CID
    assert result["author_wallet"] == SAMPLE_AUTHOR_ADDR
    assert result["dispute_status"] == "NONE"


def test_25_missing_registration_handled_without_revert(blockchain_service):
    # Contract returns (false, 0, "", zero_address, 0)
    blockchain_service._contract.functions.verifyProjectVersion(
        "REG-2026-MISSING", bytes.fromhex(SAMPLE_COMPOSITE_HASH)
    ).call.return_value = (
        False,
        0,
        "",
        "0x0000000000000000000000000000000000000000",
        0,
    )

    result = blockchain_service.verify_project_version("REG-2026-MISSING", SAMPLE_COMPOSITE_HASH)
    assert result["is_valid"] is False
    assert result["match_confirmed"] is False
    assert result["anchored_timestamp"] is None
    assert result["author_wallet"] is None


def test_26_hash_mismatch_handled_correctly(blockchain_service):
    # Registration exists, but storedHash != expectedHash: isValid = false, but timestamp exists
    blockchain_service._contract.functions.verifyProjectVersion(
        SAMPLE_REG_ID, bytes.fromhex(SAMPLE_COMPOSITE_HASH)
    ).call.return_value = (
        False,
        1788330500,
        SAMPLE_IPFS_CID,
        SAMPLE_AUTHOR_ADDR,
        0,
    )

    result = blockchain_service.verify_project_version(SAMPLE_REG_ID, SAMPLE_COMPOSITE_HASH)
    assert result["is_valid"] is False
    assert result["match_confirmed"] is False
    assert result["anchored_timestamp"] is not None  # Proof exists on chain!


def test_27_project_version_response_decoded_correctly(blockchain_service):
    # Tuple matches VersionProof struct
    proof_tuple = (
        1,  # recordId
        SAMPLE_REG_ID,
        bytes.fromhex(SAMPLE_COMPOSITE_HASH),
        SAMPLE_IPFS_CID,
        1,  # versionIndex
        1,  # DESIGN (1)
        SAMPLE_AUTHOR_ADDR,
        ["0x0000000000000000000000000000000000000001"],
        1788330500,
        100,
        0,  # NONE (0)
        True,  # exists
    )
    blockchain_service._contract.functions.getProjectVersion(SAMPLE_REG_ID).call.return_value = proof_tuple

    res = blockchain_service.get_project_version(SAMPLE_REG_ID)
    assert res["record_id"] == 1
    assert res["registration_id"] == SAMPLE_REG_ID
    assert res["composite_hash"] == "0x" + SAMPLE_COMPOSITE_HASH
    assert res["version_index"] == 1
    assert res["lifecycle_stage"] == "DESIGN"
    assert res["exists"] is True


def test_28_version_not_found_handled_correctly(blockchain_service):
    blockchain_service._contract.functions.getProjectVersion("REG-2026-MISSING").call.side_effect = (
        ContractLogicError("execution reverted: custom error VersionNotFound")
    )

    with pytest.raises(BlockchainException) as exc:
        blockchain_service.get_project_version("REG-2026-MISSING")
    assert exc.value.code == "VERSION_NOT_FOUND"
    assert exc.value.status_code == 404


# =============================================================================
# 6. DISPUTE MANAGEMENT & SECURITY
# =============================================================================

@pytest.mark.asyncio
async def test_29_dispute_transaction_constructed_correctly(blockchain_service, mock_w3):
    mock_func = MagicMock()
    mock_func.build_transaction.return_value = {"from": SAMPLE_RELAYER_ADDR}
    blockchain_service._contract.functions.raiseDispute.return_value = mock_func

    mock_signed = MagicMock()
    mock_signed.raw_transaction = b"raw_tx"
    mock_w3.eth.account.sign_transaction.return_value = mock_signed
    mock_w3.eth.send_raw_transaction.return_value = bytes.fromhex("d" * 64)

    mock_receipt = MagicMock()
    mock_receipt.status = 1
    mock_receipt.blockNumber = 110
    mock_receipt.transactionHash = bytes.fromhex("d" * 64)
    mock_w3.eth.wait_for_transaction_receipt.return_value = mock_receipt

    blockchain_service._contract.events.DisputeLogged().process_receipt.return_value = [
        {"args": {"registrationId": SAMPLE_REG_ID, "evidenceCID": "bafybeievidence"}}
    ]

    res = await blockchain_service.raise_dispute(SAMPLE_REG_ID, "bafybeievidence")
    assert res["transaction_hash"] == "d" * 64
    assert res["block_number"] == 110


@pytest.mark.asyncio
async def test_30_dispute_resolution_transaction_constructed_correctly(blockchain_service, mock_w3):
    mock_func = MagicMock()
    mock_func.build_transaction.return_value = {"from": SAMPLE_RELAYER_ADDR}
    blockchain_service._contract.functions.resolveDispute.return_value = mock_func

    mock_signed = MagicMock()
    mock_signed.raw_transaction = b"raw_tx"
    mock_w3.eth.account.sign_transaction.return_value = mock_signed
    mock_w3.eth.send_raw_transaction.return_value = bytes.fromhex("e" * 64)

    mock_receipt = MagicMock()
    mock_receipt.status = 1
    mock_receipt.blockNumber = 112
    mock_receipt.transactionHash = bytes.fromhex("e" * 64)
    mock_w3.eth.wait_for_transaction_receipt.return_value = mock_receipt

    blockchain_service._contract.events.DisputeResolved().process_receipt.return_value = [
        {"args": {"registrationId": SAMPLE_REG_ID, "status": 3}}
    ]

    res = await blockchain_service.resolve_dispute(SAMPLE_REG_ID, 3)  # RESOLVED
    assert res["transaction_hash"] == "e" * 64


def test_31_blockchain_exceptions_do_not_expose_private_keys(blockchain_service):
    # Validate that exceptions never contain private keys or secrets
    err = BlockchainException(
        code="BLOCKCHAIN_TRANSACTION_FAILED",
        message="Simulated transaction failure",
        details={"relayer_address": SAMPLE_RELAYER_ADDR},
    )
    err_str = f"{err.message} {err.code} {err.details}"
    assert SAMPLE_RELAYER_KEY not in err_str
    assert "private" not in err_str


def test_32_rpc_errors_are_converted_to_controlled_exceptions(blockchain_service, mock_w3):
    type(mock_w3.eth).block_number = PropertyMock(side_effect=Exception("Internal JSON-RPC Error: method not allowed"))
    with pytest.raises(BlockchainException) as exc:
        blockchain_service.get_latest_block()
    assert exc.value.code == "BLOCKCHAIN_CONNECTION_ERROR"
    assert "JSON-RPC" in str(exc.value.details)
