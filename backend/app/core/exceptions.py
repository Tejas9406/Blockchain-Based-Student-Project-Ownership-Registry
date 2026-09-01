from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class AppException(HTTPException):
    """
    Base application exception adhering to the universal error envelope specification.
    """
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(status_code=status_code, detail=message)
        self.code = code
        self.message = message
        self.details = details or {}


class ConflictException(AppException):
    """HTTP 409 Conflict Exception."""
    def __init__(
        self,
        message: str = "A resource with these details already exists.",
        code: str = "RESOURCE_CONFLICT",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code=code,
            message=message,
            details=details,
        )


class ValidationException(AppException):
    """HTTP 422 Unprocessable Entity Exception."""
    def __init__(
        self,
        message: str = "Request validation failed.",
        code: str = "VALIDATION_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code=code,
            message=message,
            details=details,
        )
