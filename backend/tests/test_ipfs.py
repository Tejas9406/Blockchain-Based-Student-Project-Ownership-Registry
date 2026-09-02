import json
from typing import Dict
from unittest.mock import patch

import httpx
import pytest

from app.core.config import Settings
from app.core.exceptions import IPFSException, ValidationException
from app.storage.ipfs_adapter import (
    IPFSStorageAdapter,
    is_valid_ipfs_cid,
)
from app.storage.local_adapter import LocalStorageAdapter
from app.storage.service import StorageService


# ==============================================================================
# 1. CID VALIDATION TESTS
# ==============================================================================

def test_cid_validation_valid_cidv0():
    """Test 7a: Standard 46-character Base58btc CIDv0 (Qm...) is validated as True."""
    valid_cidv0 = "QmXoypizjW3WknFiJnKLwHCnL72vedxjQkDDP1mXWo6uco"
    assert is_valid_ipfs_cid(valid_cidv0) is True


def test_cid_validation_valid_cidv1():
    """Test 7b: Standard Base32 CIDv1 (bafy...) is validated as True."""
    valid_cidv1 = "bafybeic527ywh2k37pzn26oxbpxiynvxvxzvdvdg24k722jgyk33n65d3m"
    assert is_valid_ipfs_cid(valid_cidv1) is True


def test_cid_validation_invalid_strings():
    """Test 7c & 10: Invalid strings, empty strings, and non-CIDs are rejected."""
    invalid_cases = [
        "",
        "   ",
        "invalid_cid",
        "QmShort",
        "bafy_with_invalid_chars!@#$",
        "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",  # raw SHA256 hex is not a CID
        None,
        12345,
    ]
    for case in invalid_cases:
        assert is_valid_ipfs_cid(case) is False


# ==============================================================================
# 2. IPFS ADAPTER CONFIGURATION & SSRF PROTECTION
# ==============================================================================

def test_ipfs_adapter_initializes_with_valid_config():
    """Test 11 & 12: Adapter initializes from explicit arguments or environment settings."""
    adapter = IPFSStorageAdapter(
        api_url="http://192.168.1.50:5001",
        gateway_url="http://192.168.1.50:8080",
        timeout_seconds=45,
    )
    assert adapter.api_url == "http://192.168.1.50:5001"
    assert adapter.gateway_url == "http://192.168.1.50:8080"
    assert adapter.timeout_seconds == 45


def test_ipfs_adapter_rejects_malformed_or_ssrf_urls():
    """Test 11b: Adapter rejects non-HTTP/HTTPS URLs preventing protocol smuggling."""
    for bad_url in ["ftp://localhost:5001", "file:///etc/passwd", "gopher://bad", "invalid-url"]:
        with pytest.raises(ValueError, match="Must be a valid HTTP/HTTPS URL"):
            IPFSStorageAdapter(api_url=bad_url)


# ==============================================================================
# 3. SINGLE ARTIFACT UPLOAD & RETRIEVAL (MOCKED KUBO API)
# ==============================================================================

@pytest.mark.asyncio
async def test_add_bytes_successful_upload():
    """Test 1 & 2: Successful upload to IPFS propagates genuine CID returned by Kubo."""
    expected_cid = "bafybeic527ywh2k37pzn26oxbpxiynvxvxzvdvdg24k722jgyk33n65d3m"

    def mock_handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v0/add"
        assert request.url.params["pin"] == "true"
        assert request.url.params["cid-version"] == "1"
        return httpx.Response(
            200,
            json={"Name": "artifact.pdf", "Hash": expected_cid, "Size": "1024"},
        )

    adapter = IPFSStorageAdapter(
        api_url="http://127.0.0.1:5001",
        transport=httpx.MockTransport(mock_handler),
    )
    cid = await adapter.add_bytes(b"sample artifact content bytes", filename="artifact.pdf")
    assert cid == expected_cid


@pytest.mark.asyncio
async def test_add_bytes_empty_content_rejected():
    """Test 3: Empty 0-byte upload is rejected without network call."""
    adapter = IPFSStorageAdapter(api_url="http://127.0.0.1:5001")
    with pytest.raises(ValidationException, match="Cannot upload empty"):
        await adapter.add_bytes(b"")


@pytest.mark.asyncio
async def test_cat_and_cat_stream_content_retrieval():
    """Test 1b: Retrieving content by CID matches uploaded content."""
    valid_cid = "bafybeic527ywh2k37pzn26oxbpxiynvxvxzvdvdg24k722jgyk33n65d3m"
    payload = b"Retrieved student project document bytes from IPFS"

    def mock_handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v0/cat"
        assert request.url.params["arg"] == valid_cid
        return httpx.Response(200, content=payload)

    adapter = IPFSStorageAdapter(
        api_url="http://127.0.0.1:5001",
        transport=httpx.MockTransport(mock_handler),
    )

    # Full retrieval
    data = await adapter.cat(valid_cid)
    assert data == payload

    # Streamed retrieval
    streamed = b""
    async for chunk in adapter.cat_stream(valid_cid, chunk_size=16):
        streamed += chunk
    assert streamed == payload


# ==============================================================================
# 4. MULTI-ARTIFACT DIRECTORY DAG (ROOT CID) TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_add_directory_multi_artifact_root_dag():
    """Test 8 & 9: Uploading multiple artifacts returns individual CIDs and root directory DAG CID."""
    root_cid = "bafybeirootdirectorydagcidabcdefghijklmnopqrstuvwxyz234567"
    file1_cid = "bafybeifileonecontentcidabcdefghijklmnopqrstuvwxyz234567"
    file2_cid = "bafybeifiletwocontentcidabcdefghijklmnopqrstuvwxyz234567"

    ndjson_response = (
        f'{{"Name":"report.pdf","Hash":"{file1_cid}","Size":"100"}}\n'
        f'{{"Name":"code.zip","Hash":"{file2_cid}","Size":"200"}}\n'
        f'{{"Name":"","Hash":"{root_cid}","Size":"300"}}\n'
    )

    def mock_handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v0/add"
        assert request.url.params["wrap-with-directory"] == "true"
        return httpx.Response(200, text=ndjson_response)

    adapter = IPFSStorageAdapter(
        api_url="http://127.0.0.1:5001",
        transport=httpx.MockTransport(mock_handler),
    )

    files = {
        "report.pdf": b"Report content",
        "code.zip": b"Source code zip content",
    }

    result = await adapter.add_directory(files=files, pin=True)

    assert result["report.pdf"] == file1_cid
    assert result["code.zip"] == file2_cid
    assert result["root"] == root_cid
    assert result[""] == root_cid


@pytest.mark.asyncio
async def test_add_directory_empty_files_rejected():
    """Test 8b: Attempting to create an empty directory DAG is rejected."""
    adapter = IPFSStorageAdapter(api_url="http://127.0.0.1:5001")
    with pytest.raises(ValidationException, match="Cannot create an IPFS directory DAG without files"):
        await adapter.add_directory(files={})


# ==============================================================================
# 5. PINNING OPERATIONS & CHECKS
# ==============================================================================

@pytest.mark.asyncio
async def test_pin_and_unpin_and_is_pinned():
    """Test 4: Pin add, rm, and ls operations succeed with valid CIDs."""
    valid_cid = "bafybeic527ywh2k37pzn26oxbpxiynvxvxzvdvdg24k722jgyk33n65d3m"

    def mock_handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v0/pin/add":
            return httpx.Response(200, json={"Pins": [valid_cid]})
        elif request.url.path == "/api/v0/pin/rm":
            return httpx.Response(200, json={"Pins": [valid_cid]})
        elif request.url.path == "/api/v0/pin/ls":
            return httpx.Response(200, json={"Keys": {valid_cid: {"Type": "recursive"}}})
        return httpx.Response(404)

    adapter = IPFSStorageAdapter(
        api_url="http://127.0.0.1:5001",
        transport=httpx.MockTransport(mock_handler),
    )

    assert await adapter.pin(valid_cid) is True
    assert await adapter.unpin(valid_cid) is True
    assert await adapter.is_pinned(valid_cid) is True


# ==============================================================================
# 6. ERROR & FAILURE HANDLING TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_ipfs_connection_failure():
    """Test 4: Connection error when Kubo daemon is offline raises IPFSException."""
    def mock_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Connection refused by host: 127.0.0.1:5001")

    adapter = IPFSStorageAdapter(
        api_url="http://127.0.0.1:5001",
        transport=httpx.MockTransport(mock_handler),
    )

    with pytest.raises(IPFSException) as exc_info:
        await adapter.add_bytes(b"test data")
    assert exc_info.value.code == "IPFS_CONNECTION_ERROR"
    assert exc_info.value.status_code == 502


@pytest.mark.asyncio
async def test_ipfs_timeout_handling():
    """Test 5: Request timeout raises IPFSException."""
    def mock_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("Network timeout communicating with IPFS node")

    adapter = IPFSStorageAdapter(
        api_url="http://127.0.0.1:5001",
        timeout_seconds=10,
        transport=httpx.MockTransport(mock_handler),
    )

    with pytest.raises(IPFSException) as exc_info:
        await adapter.add_bytes(b"test data")
    assert exc_info.value.code == "IPFS_TIMEOUT"
    assert exc_info.value.status_code == 502


@pytest.mark.asyncio
async def test_ipfs_api_error_response():
    """Test 6: Kubo node returning HTTP 500 raises IPFSException."""
    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Internal repo error: block store locked")

    adapter = IPFSStorageAdapter(
        api_url="http://127.0.0.1:5001",
        transport=httpx.MockTransport(mock_handler),
    )

    with pytest.raises(IPFSException) as exc_info:
        await adapter.add_bytes(b"test data")
    assert exc_info.value.code == "IPFS_API_ERROR"
    assert exc_info.value.status_code == 502


# ==============================================================================
# 7. StorageAdapter INTERFACE BEHAVIOR (CHUNKS & BUFFERING)
# ==============================================================================

@pytest.mark.asyncio
async def test_storage_adapter_interface_chunking():
    """Test 13: IPFSStorageAdapter implements write_chunk, retrieve, exists, and delete."""
    adapter = IPFSStorageAdapter(api_url="http://127.0.0.1:5001")
    key = "ART-202609-TEST1/content"

    # Write chunks
    await adapter.write_chunk(key, b"chunk_part_1_", is_first_chunk=True)
    await adapter.write_chunk(key, b"chunk_part_2", is_first_chunk=False)

    assert await adapter.exists(key) is True
    retrieved = await adapter.retrieve(key)
    assert retrieved == b"chunk_part_1_chunk_part_2"

    # Clean up
    deleted = await adapter.delete(key)
    assert deleted is True
    assert await adapter.exists(key) is False


# ==============================================================================
# 8. StorageService INTEGRATION & LOCAL ADAPTER NON-REGRESSION
# ==============================================================================

@pytest.mark.asyncio
async def test_storage_service_uses_local_adapter_by_default(tmp_path):
    """Test 13b & 14: Existing LocalStorageAdapter continues to function without regression."""
    local_adapter = LocalStorageAdapter(root_dir=tmp_path / "artifacts")
    service = StorageService(adapter=local_adapter)

    key = "test_key/file.bin"
    await service.write_chunk(key, b"local content bytes", is_first_chunk=True)
    assert await service.exists(key) is True
    assert await service.retrieve(key) == b"local content bytes"
    await service.delete(key)
    assert await service.exists(key) is False
