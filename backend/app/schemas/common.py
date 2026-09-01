from typing import Generic, Optional, TypeVar
from pydantic import BaseModel, Field

from app.utils.time import format_iso_utc

DataT = TypeVar("DataT")


class ApiMeta(BaseModel):
    """
    Standard API metadata envelope attached to all responses.
    """
    timestamp: str = Field(
        default_factory=format_iso_utc,
        description="ISO 8601 UTC timestamp of response generation",
        examples=["2026-08-31T18:50:00.000Z"],
    )
    request_id: Optional[str] = Field(
        default=None,
        description="Unique request correlation ID",
        examples=["req-8f29a-11e2"],
    )


class ApiResponse(BaseModel, Generic[DataT]):
    """
    Universal Success Response Envelope conforming to frozen contract.
    """
    success: bool = Field(
        default=True,
        description="Indicates successful request completion",
    )
    data: DataT = Field(
        ...,
        description="Response payload data",
    )
    meta: ApiMeta = Field(
        default_factory=ApiMeta,
        description="Response metadata",
    )
