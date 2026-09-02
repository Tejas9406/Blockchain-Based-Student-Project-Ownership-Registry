import json
from pathlib import Path
from typing import Any, List

ABI_DIR = Path(__file__).parent


def get_project_registry_abi() -> List[Any]:
    """
    Returns the authoritative ABI for ProjectRegistry.
    Reads from the local backend ABI directory, with fallback to blockchain/artifacts.
    """
    local_abi_path = ABI_DIR / "ProjectRegistry.json"
    if local_abi_path.exists():
        with open(local_abi_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict) and "abi" in data:
                return data["abi"]
            elif isinstance(data, list):
                return data

    # Fallback to blockchain/artifacts if local copy is somehow missing
    fallback_path = (
        ABI_DIR.parents[2]
        / "blockchain"
        / "artifacts"
        / "contracts"
        / "ProjectRegistry.sol"
        / "ProjectRegistry.json"
    )
    if fallback_path.exists():
        with open(fallback_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict) and "abi" in data:
                return data["abi"]
            elif isinstance(data, list):
                return data

    raise FileNotFoundError("ProjectRegistry ABI artifact not found.")
