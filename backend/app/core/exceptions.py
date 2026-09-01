from typing import Any, Optional


class AppException(Exception):
    """
    Base Application Exception.
    All business logic and operational exceptions should inherit from or instantiate this class.
    """

    def __init__(
        self,
        message: str,
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


class UnauthorizedError(AppException):
    """Authentication required or failed (HTTP 401)."""

    def __init__(
        self,
        message: str = "Authentication required.",
        code: str = "UNAUTHORIZED",
        details: Optional[Any] = None,
    ):
        super().__init__(message=message, code=code, status_code=401, details=details)


class ForbiddenError(AppException):
    """Permission denied for authenticated user (HTTP 403)."""

    def __init__(
        self,
        message: str = "You do not have permission to perform this action.",
        code: str = "FORBIDDEN",
        details: Optional[Any] = None,
    ):
        super().__init__(message=message, code=code, status_code=403, details=details)


class ConflictError(AppException):
    """Resource state conflict, e.g. duplicate key (HTTP 409)."""

    def __init__(
        self,
        message: str = "Resource state conflict.",
        code: str = "CONFLICT",
        details: Optional[Any] = None,
    ):
        super().__init__(message=message, code=code, status_code=409, details=details)


class ValidationAppError(AppException):
    """Custom validation failure (HTTP 422)."""

    def __init__(
        self,
        message: str = "Validation error.",
        code: str = "VALIDATION_ERROR",
        details: Optional[Any] = None,
    ):
        super().__init__(message=message, code=code, status_code=422, details=details)


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
