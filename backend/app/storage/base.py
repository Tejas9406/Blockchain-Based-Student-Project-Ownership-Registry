from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional


class StorageAdapter(ABC):
    """
    Abstract storage adapter defining the interface for artifact content storage.
    Supports streaming writes, full/streamed retrieval, deletion, and existence checks.
    Allows substituting LocalStorageAdapter with IPFSStorageAdapter in future phases.
    """

    @abstractmethod
    async def write_chunk(
        self, storage_key: str, chunk: bytes, is_first_chunk: bool = False
    ) -> None:
        """
        Appends or initializes a chunk of data for the given storage_key.
        """
        pass

    @abstractmethod
    async def retrieve(self, storage_key: str) -> bytes:
        """
        Retrieves the complete content of the stored artifact as bytes.
        """
        pass

    @abstractmethod
    async def retrieve_stream(
        self, storage_key: str, chunk_size: int = 65536
    ) -> AsyncIterator[bytes]:
        """
        Yields the stored artifact content in streaming chunks.
        """
        pass

    @abstractmethod
    async def delete(self, storage_key: str) -> bool:
        """
        Deletes the stored artifact content for storage_key if present.
        Returns True if deleted, False if not found.
        """
        pass

    @abstractmethod
    async def exists(self, storage_key: str) -> bool:
        """
        Checks whether the artifact content exists in storage.
        """
        pass

    async def add_bytes(
        self, data: bytes, filename: Optional[str] = None, pin: bool = True
    ) -> str:
        """
        Uploads raw bytes to storage and returns a content identifier (CID).
        """
        raise NotImplementedError("Storage adapter does not support add_bytes.")

    async def add_directory(
        self, files: dict[str, bytes], pin: bool = True
    ) -> dict[str, str]:
        """
        Uploads multiple named files wrapped in a directory structure and returns
        a mapping of filename -> CID, and 'root' -> root directory CID.
        """
        raise NotImplementedError("Storage adapter does not support add_directory.")
