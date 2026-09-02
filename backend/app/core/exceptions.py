from typing import Any, Optional


class AppException(Exception):
    """
    Base Application Exception adhering to the universal error envelope specification.
    All business logic and operational exceptions should inherit from or instantiate this class.
    """

    def __init__(
        self,
        message: str = "An application error occurred.",
        code: str = "BAD_REQUEST",
        status_code: int = 400,
        details: Optional[Any] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details

    def __repr__(self) -> str:
        return f"<AppException code={self.code} status_code={self.status_code} message={self.message}>"


class NotFoundError(AppException):
    """Resource not found (HTTP 404)."""

    def __init__(
        self,
        message: str = "Requested resource not found.",
        code: str = "RESOURCE_NOT_FOUND",
        details: Optional[Any] = None,
    ):
        super().__init__(message=message, code=code, status_code=404, details=details)


NotFoundException = NotFoundError


class UnauthorizedError(AppException):
    """Authentication required or failed (HTTP 401)."""

    def __init__(
        self,
        message: str = "Authentication required.",
        code: str = "UNAUTHORIZED",
        details: Optional[Any] = None,
    ):
        super().__init__(message=message, code=code, status_code=401, details=details)


class UnauthorizedException(UnauthorizedError):
    """HTTP 401 Unauthorized Exception (Authentication subsystem)."""

    def __init__(
        self,
        message: str = "Invalid email or password.",
        code: str = "INVALID_CREDENTIALS",
        details: Optional[Any] = None,
    ):
        super().__init__(message=message, code=code, details=details)


class ForbiddenError(AppException):
    """Permission denied for authenticated user (HTTP 403)."""

    def __init__(
        self,
        message: str = "You do not have permission to perform this action.",
        code: str = "FORBIDDEN",
        details: Optional[Any] = None,
    ):
        super().__init__(message=message, code=code, status_code=403, details=details)


class ForbiddenException(ForbiddenError):
    """HTTP 403 Forbidden Exception."""
    pass


class ConflictError(AppException):
    """Resource state conflict, e.g. duplicate key (HTTP 409)."""

    def __init__(
        self,
        message: str = "Resource state conflict.",
        code: str = "CONFLICT",
        details: Optional[Any] = None,
    ):
        super().__init__(message=message, code=code, status_code=409, details=details)


class ConflictException(ConflictError):
    """HTTP 409 Conflict Exception."""

    def __init__(
        self,
        message: str = "A resource with these details already exists.",
        code: str = "RESOURCE_CONFLICT",
        details: Optional[Any] = None,
    ):
        super().__init__(message=message, code=code, details=details)


class ValidationAppError(AppException):
    """Custom validation failure (HTTP 422)."""

    def __init__(
        self,
        message: str = "Validation error.",
        code: str = "VALIDATION_ERROR",
        details: Optional[Any] = None,
    ):
        super().__init__(message=message, code=code, status_code=422, details=details)


class ValidationException(ValidationAppError):
    """HTTP 422 Unprocessable Entity Exception."""

    def __init__(
        self,
        message: str = "Request validation failed.",
        code: str = "VALIDATION_ERROR",
        details: Optional[Any] = None,
    ):
        super().__init__(message=message, code=code, details=details)


class NotImplementedAppError(AppException):
    """Endpoint or operation not yet implemented (HTTP 501)."""

    def __init__(
        self,
        message: str = "This operation is not yet implemented.",
        code: str = "NOT_IMPLEMENTED",
        details: Optional[Any] = None,
    ):
        super().__init__(message=message, code=code, status_code=501, details=details)


class InternalServerError(AppException):
    """Internal server error (HTTP 500)."""

    def __init__(
        self,
        message: str = "An internal server error occurred.",
        code: str = "INTERNAL_SERVER_ERROR",
        details: Optional[Any] = None,
    ):
        super().__init__(message=message, code=code, status_code=500, details=details)


class IPFSException(AppException):
    """Raised when IPFS communication fails, times out, or returns a daemon error (HTTP 502)."""

    def __init__(
        self,
        message: str = "IPFS service operation failed.",
        code: str = "IPFS_ERROR",
        status_code: int = 502,
        details: Optional[Any] = None,
    ):
        super().__init__(message=message, code=code, status_code=status_code, details=details)


class BlockchainException(AppException):
    """Raised when blockchain communication, contract execution, or relayer operations fail (HTTP 502)."""

    def __init__(
        self,
        message: str = "Blockchain service operation failed.",
        code: str = "BLOCKCHAIN_ERROR",
        status_code: int = 502,
        details: Optional[Any] = None,
    ):
        super().__init__(message=message, code=code, status_code=status_code, details=details)


__all__ = [
    "AppException",
    "NotFoundError",
    "NotFoundException",
    "UnauthorizedError",
    "UnauthorizedException",
    "ForbiddenError",
    "ForbiddenException",
    "ConflictError",
    "ConflictException",
    "ValidationAppError",
    "ValidationException",
    "NotImplementedAppError",
    "InternalServerError",
    "IPFSException",
    "BlockchainException",
]
