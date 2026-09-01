import math
from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

from app.schemas.common import ApiMeta
from app.utils.time import format_iso_utc

ItemT = TypeVar("ItemT")


class PaginatedMeta(ApiMeta):
    """
    Pagination metadata conforming to frozen API contract.
    """
    page: int = Field(
        ...,
        ge=1,
        description="Current page index (1-indexed)",
        examples=[1],
    )
    page_size: int = Field(
        ...,
        ge=1,
        le=100,
        description="Number of items per page",
        examples=[20],
    )
    total_items: int = Field(
        ...,
        ge=0,
        description="Total matching items count",
        examples=[142],
    )
    total_pages: int = Field(
        ...,
        ge=0,
        description="Total available pages count",
        examples=[8],
    )
    has_next: bool = Field(
        ...,
        description="True if subsequent page exists",
        examples=[True],
    )
    has_prev: bool = Field(
        ...,
        description="True if preceding page exists",
        examples=[False],
    )

    @classmethod
    def create(
        cls,
        page: int,
        page_size: int,
        total_items: int,
        request_id: Optional[str] = None,
    ) -> "PaginatedMeta":
        """
        Factory helper to compute total_pages, has_next, and has_prev deterministically.
        """
        total_pages = math.ceil(total_items / page_size) if total_items > 0 else 0
        has_next = page < total_pages
        has_prev = page > 1 and total_pages > 0
        return cls(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev,
            request_id=request_id,
            timestamp=format_iso_utc(),
        )


class ApiPaginatedResponse(BaseModel, Generic[ItemT]):
    """
    Universal Paginated Response Envelope conforming to frozen contract.
    """
    success: bool = Field(
        default=True,
        description="Indicates successful request completion",
    )
    data: List[ItemT] = Field(
        default_factory=list,
        description="List of paginated items",
    )
    meta: PaginatedMeta = Field(
        ...,
        description="Pagination metadata",
    )


class PaginationParams(BaseModel):
    """
    Query parameter dependency for paginated endpoints.
    """
    page: int = Field(
        default=1,
        ge=1,
        description="Page number (1-based index)",
    )
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Number of records per page (max 100)",
    )

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size
