from typing import Any, Optional
from pydantic import BaseModel, Field

from app.schemas.common import ApiMeta


class ApiErrorDetail(BaseModel):
    """
    Standard error detail block.
    """
    code: str = Field(
        ...,
        description="Machine-readable error code",
        examples=["PROJECT_NOT_FOUND", "VALIDATION_ERROR"],
    )
    message: str = Field(
        ...,
        description="Human-readable description of error",
        examples=["The requested project identifier does not exist."],
    )
    details: Optional[Any] = Field(
        default=None,
        description="Additional context, field errors, or parameter details",
    )


class ApiErrorResponse(BaseModel):
    """
    Universal Error Response Envelope conforming to frozen contract.
    """
    success: bool = Field(
        default=False,
        description="Always false for error responses",
    )
    error: ApiErrorDetail = Field(
        ...,
        description="Error details payload",
    )
    meta: ApiMeta = Field(
        default_factory=ApiMeta,
        description="Response metadata",
    )
