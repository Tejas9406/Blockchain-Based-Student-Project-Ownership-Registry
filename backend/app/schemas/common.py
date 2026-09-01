from datetime import datetime, timezone
from typing import Any, Dict, Generic, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


def get_utc_now_iso() -> str:
    """Returns current UTC timestamp formatted as ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class ApiMeta(BaseModel):
    """Universal API metadata envelope."""
    timestamp: str = Field(default_factory=get_utc_now_iso, description="UTC ISO 8601 timestamp")
    request_id: Optional[str] = Field(default=None, description="Unique correlation request identifier")


class ApiResponse(BaseModel, Generic[T]):
    """Universal success response envelope (API_CONTRACT.md Section 3.1)."""
    success: bool = Field(default=True, description="Indicates successful request completion")
    data: T = Field(..., description="Response payload")
    meta: ApiMeta = Field(default_factory=ApiMeta, description="Response metadata")


class ApiErrorDetail(BaseModel):
    """Error detail structure inside error envelope."""
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error explanation")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Field-level error details")


class ApiErrorResponse(BaseModel):
    """Universal error response envelope (API_CONTRACT.md Section 3.3)."""
    success: bool = Field(default=False, description="Always false for error responses")
    error: ApiErrorDetail = Field(..., description="Error detail object")
    meta: ApiMeta = Field(default_factory=ApiMeta, description="Response metadata")
