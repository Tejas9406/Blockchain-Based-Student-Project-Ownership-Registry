import asyncio
import os
import sys
from datetime import datetime

from web3 import Web3

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.abi import get_project_registry_abi
from app.services.blockchain_service import BlockchainService

# Default Hardhat local network parameters
DEFAULT_RPC_URL = "http://127.0.0.1:8545"
# Standard Hardhat account #0 (Owner) and #1 (Relayer)
HARDHAT_ACCOUNT_0_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
HARDHAT_ACCOUNT_1_KEY = "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"
HARDHAT_ACCOUNT_2_KEY = "0x5de4111afa1a4b94908f83103eb2f95402bbf249883017900de5160d4ff50506"


async def run_live_integration_verification():
    """
    Executes live verification against an active EVM node (e.g. npx hardhat node).
    1. Checks connection
    2. Deploys a test ProjectRegistry contract
    3. Initializes BlockchainService
    4. Registers a project version
    5. Queries version proof
    6. Verifies composite hash
    7. Raises a dispute
    8. Resolves the dispute
    """
    print("=" * 64)
    print("Web3.py Live Blockchain Integration Verification")
    print("=" * 64)

    w3 = Web3(Web3.HTTPProvider(DEFAULT_RPC_URL))
    if not w3.is_connected():
        print(f"[SKIP] No active EVM node running at {DEFAULT_RPC_URL}.")
        print("To run this verification against a live node, start:")
        print("   cd blockchain && npx hardhat node")
        print("then in another terminal:")
        print("   python backend/scripts/verify_web3_live.py")
        return 0

    chain_id = w3.eth.chain_id
    latest_block = w3.eth.block_number
    print(f"[1/8] Connected to RPC at {DEFAULT_RPC_URL} (Chain ID: {chain_id}, Height: {latest_block})")

    deployer_account = w3.eth.account.from_key(HARDHAT_ACCOUNT_0_KEY)
    relayer_account = w3.eth.account.from_key(HARDHAT_ACCOUNT_1_KEY)
    claimant_account = w3.eth.account.from_key(HARDHAT_ACCOUNT_2_KEY)

    print(f"[2/8] Accounts: Deployer={deployer_account.address}, Relayer={relayer_account.address}")

    # Load ABI & deploy contract
    abi = get_project_registry_abi()
    
    # We need bytecode for deployment
    import json
    from pathlib import Path
    artifact_path = Path(__file__).resolve().parents[2] / "blockchain" / "artifacts" / "contracts" / "ProjectRegistry.sol" / "ProjectRegistry.json"
    if not artifact_path.exists():
        print(f"[FAIL] Hardhat artifact not found at {artifact_path}")
        return 1

    with open(artifact_path, "r", encoding="utf-8") as f:
        artifact_data = json.load(f)
    bytecode = artifact_data["bytecode"]

    contract_factory = w3.eth.contract(abi=abi, bytecode=bytecode)
    nonce = w3.eth.get_transaction_count(deployer_account.address, "pending")

    deploy_tx = contract_factory.constructor(
        deployer_account.address,
        relayer_account.address,
    ).build_transaction({
        "from": deployer_account.address,
        "nonce": nonce,
        "chainId": chain_id,
        "gasPrice": w3.eth.gas_price,
    })

    signed_deploy = w3.eth.account.sign_transaction(deploy_tx, deployer_account.key)
    tx_hash = w3.eth.send_raw_transaction(signed_deploy.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=15)
    contract_addr = receipt.contractAddress

    print(f"[3/8] ProjectRegistry deployed at: {contract_addr}")

    # Initialize BlockchainService
    service = BlockchainService(
        rpc_url=DEFAULT_RPC_URL,
        contract_address=contract_addr,
        chain_id=chain_id,
        relayer_private_key=HARDHAT_ACCOUNT_1_KEY,
        confirmation_blocks=1,
        web3_instance=w3,
    )

    # Register project version
    sample_reg_id = f"REG-2026-LIVE{int(datetime.now().timestamp()) % 10000:04d}"
    sample_hash = "a" * 64
    sample_cid = "bafybeiliveintegrationchecktestcid1234567890abcdefghijklmn"

    print(f"[4/8] Registering version {sample_reg_id} via Relayer...")
    reg_result = await service.register_project_version(
        registration_id=sample_reg_id,
        composite_hash=sample_hash,
        ipfs_root_cid=sample_cid,
        version_index=1,
        lifecycle_stage="IDEA",
        author=claimant_account.address,
        co_authors=[],
    )
    print(f"      Anchored! Tx: {reg_result['transaction_hash']}, Block: {reg_result['block_number']}")

    # Verification call
    print("[5/8] Performing trustless verification view call...")
    ver_result = service.verify_project_version(sample_reg_id, sample_hash)
    assert ver_result["is_valid"] is True
    assert ver_result["match_confirmed"] is True
    print(f"      Verification confirmed valid: {ver_result['is_valid']}")

    # Mismatch check
    ver_mismatch = service.verify_project_version(sample_reg_id, "b" * 64)
    assert ver_mismatch["is_valid"] is False
    print("      Verification correctly rejected mismatched hash.")

    # Get project version
    print("[6/8] Retrieving complete version proof struct...")
    proof = service.get_project_version(sample_reg_id)
    assert proof["registration_id"] == sample_reg_id
    assert proof["lifecycle_stage"] == "IDEA"
    print(f"      Proof retrieved: {proof['registration_id']}, Author: {proof['author']}")

    # Raise dispute
    print("[7/8] Submitting dispute against anchored version...")
    evidence_cid = "bafybeidisputeevidence1234567890abcdef"
    disp_res = await service.raise_dispute(sample_reg_id, evidence_cid)
    print(f"      Dispute raised on-chain: Tx {disp_res['transaction_hash']}")

    # Resolve dispute (using owner account)
    print("[8/8] Resolving dispute as RESOLVED (3)...")
    owner_service = BlockchainService(
        rpc_url=DEFAULT_RPC_URL,
        contract_address=contract_addr,
        chain_id=chain_id,
        relayer_private_key=HARDHAT_ACCOUNT_0_KEY,  # Contract Owner
        confirmation_blocks=1,
        web3_instance=w3,
    )
    res_dispute = await owner_service.resolve_dispute(sample_reg_id, 3)
    print(f"      Dispute resolved on-chain: Tx {res_dispute['transaction_hash']}")

    updated_proof = service.get_project_version(sample_reg_id)
    assert updated_proof["dispute_state"] == "RESOLVED"
    print(f"      Verified updated dispute state: {updated_proof['dispute_state']}")

    print("=" * 64)
    print("SUCCESS: Live Web3.py integration verification completed!")
    print("=" * 64)
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(run_live_integration_verification())
    sys.exit(exit_code)
