import os
import shutil
from pathlib import Path
from typing import AsyncIterator, Optional, Union

from app.core.config import settings
from app.storage.base import StorageAdapter


class LocalStorageAdapter(StorageAdapter):
    """
    Local filesystem storage adapter for development environment.
    Stores artifact bytes safely under a configurable root directory.
    Enforces strict path containment to prevent path traversal.
    """

    def __init__(self, root_dir: Optional[Union[str, Path]] = None) -> None:
        if root_dir is not None:
            self._root_dir = Path(root_dir).resolve()
        else:
            self._root_dir = Path(settings.ARTIFACT_STORAGE_DIR).resolve()
        self._root_dir.mkdir(parents=True, exist_ok=True)

    @property
    def root_dir(self) -> Path:
        return self._root_dir

    def _resolve_safe_path(self, storage_key: str) -> Path:
        """
        Resolves storage_key against root_dir while strictly preventing path traversal.
        """
        if not storage_key or "\x00" in storage_key:
            raise ValueError("Invalid storage key.")

        # Normalize slashes
        normalized_key = storage_key.replace("\\", "/").strip("/ ")
        resolved_path = (self._root_dir / normalized_key).resolve()

        # Strict containment check
        try:
            resolved_path.relative_to(self._root_dir)
        except ValueError:
            raise ValueError(
                f"Path traversal detected: storage key '{storage_key}' escapes storage root."
            )

        return resolved_path

    async def write_chunk(
        self, storage_key: str, chunk: bytes, is_first_chunk: bool = False
    ) -> None:
        target_path = self._resolve_safe_path(storage_key)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        mode = "wb" if is_first_chunk else "ab"
        with open(target_path, mode) as f:
            f.write(chunk)

    async def retrieve(self, storage_key: str) -> bytes:
        target_path = self._resolve_safe_path(storage_key)
        if not target_path.is_file():
            raise FileNotFoundError(f"Artifact content not found for key: '{storage_key}'")
        with open(target_path, "rb") as f:
            return f.read()

    async def retrieve_stream(
        self, storage_key: str, chunk_size: int = 65536
    ) -> AsyncIterator[bytes]:
        target_path = self._resolve_safe_path(storage_key)
        if not target_path.is_file():
            raise FileNotFoundError(f"Artifact content not found for key: '{storage_key}'")
        with open(target_path, "rb") as f:
            while chunk := f.read(chunk_size):
                yield chunk

    async def delete(self, storage_key: str) -> bool:
        target_path = self._resolve_safe_path(storage_key)
        deleted = False

        if target_path.is_file():
            target_path.unlink()
            deleted = True

        # Clean up empty parent directory if it's not the root_dir itself
        parent = target_path.parent
        if parent != self._root_dir and parent.is_dir():
            try:
                # Remove parent directory if empty
                if not any(parent.iterdir()):
                    parent.rmdir()
            except OSError:
                pass

        return deleted

    async def exists(self, storage_key: str) -> bool:
        target_path = self._resolve_safe_path(storage_key)
        return target_path.is_file()

    async def add_bytes(
        self, data: bytes, filename: Optional[str] = None, pin: bool = True
    ) -> str:
        """
        Stores artifact bytes under local CIDs directory and returns a deterministic CIDv1 string.
        """
        if not data:
            from app.core.exceptions import ValidationException
            raise ValidationException(
                code="EMPTY_CONTENT_NOT_ALLOWED",
                message="Cannot upload empty (0-byte) content to storage.",
                details={"bytes": 0},
            )
        import base64
        import hashlib
        raw_hash = hashlib.sha256(data).digest()
        raw_cid = b"\x01\x70\x12\x20" + raw_hash
        cid = "b" + base64.b32encode(raw_cid).decode("ascii").lower().rstrip("=")
        storage_key = f"cids/{cid}"
        await self.write_chunk(storage_key, data, is_first_chunk=True)
        return cid

    async def add_directory(
        self, files: dict[str, bytes], pin: bool = True
    ) -> dict[str, str]:
        """
        Stores directory files locally and returns a mapping of filename -> CID, and 'root' -> root CID.
        """
        if not files:
            from app.core.exceptions import ValidationException
            raise ValidationException(
                code="EMPTY_DIRECTORY_NOT_ALLOWED",
                message="Cannot create storage directory without files.",
            )
        import base64
        import hashlib
        mapping: dict[str, str] = {}
        combined = bytearray()
        for name in sorted(files.keys()):
            content = files[name]
            cid = await self.add_bytes(content, filename=name, pin=pin)
            mapping[name] = cid
            combined.extend(name.encode("utf-8") + b":" + content)
        raw_root = hashlib.sha256(bytes(combined)).digest()
        raw_root_cid = b"\x01\x70\x12\x20" + raw_root
        root_cid = "b" + base64.b32encode(raw_root_cid).decode("ascii").lower().rstrip("=")
        mapping["root"] = root_cid
        return mapping
