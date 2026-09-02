from typing import AsyncIterator, Optional

from app.storage.base import StorageAdapter
from app.storage.local_adapter import LocalStorageAdapter


class StorageService:
    """
    Core storage service providing a unified interface for artifact persistence.
    Delegates concrete storage operations to a pluggable StorageAdapter.
    Currently uses LocalStorageAdapter; easily swappable with IPFSStorageAdapter in Phase 5.
    """

    def __init__(self, adapter: Optional[StorageAdapter] = None) -> None:
        self._adapter: StorageAdapter = adapter or LocalStorageAdapter()

    @property
    def adapter(self) -> StorageAdapter:
        return self._adapter

    async def write_chunk(
        self, storage_key: str, chunk: bytes, is_first_chunk: bool = False
    ) -> None:
        await self._adapter.write_chunk(
            storage_key=storage_key, chunk=chunk, is_first_chunk=is_first_chunk
        )

    async def retrieve(self, storage_key: str) -> bytes:
        return await self._adapter.retrieve(storage_key=storage_key)

    async def retrieve_stream(
        self, storage_key: str, chunk_size: int = 65536
    ) -> AsyncIterator[bytes]:
        async for chunk in self._adapter.retrieve_stream(
            storage_key=storage_key, chunk_size=chunk_size
        ):
            yield chunk

    async def delete(self, storage_key: str) -> bool:
        return await self._adapter.delete(storage_key=storage_key)

    async def exists(self, storage_key: str) -> bool:
        return await self._adapter.exists(storage_key=storage_key)


# Global storage service instance
_global_storage_service: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    """
    Returns the active StorageService instance.
    Defaults to LocalStorageAdapter if not overridden.
    """
    global _global_storage_service
    if _global_storage_service is None:
        _global_storage_service = StorageService()
    return _global_storage_service


def set_storage_service(service: Optional[StorageService]) -> None:
    """
    Allows overriding the storage service (used extensively in test suites to point to temporary directories).
    """
    global _global_storage_service
    _global_storage_service = service
