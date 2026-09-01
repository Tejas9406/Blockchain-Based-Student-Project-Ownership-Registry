from typing import Any, List
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppException
from app.core.logging import logger
from app.core.middleware import generate_request_id
from app.schemas.common import ApiMeta
from app.schemas.error import ApiErrorDetail, ApiErrorResponse
from app.utils.time import format_iso_utc


def _extract_request_id(request: Request) -> str:
    """Helper to extract request ID from request state or generate fallback."""
    return getattr(request.state, "request_id", None) or generate_request_id()


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    Handles all domain AppException instances and returns standard ApiErrorResponse envelope.
    """
    request_id = _extract_request_id(request)
    error_payload = ApiErrorResponse(
        success=False,
        error=ApiErrorDetail(
            code=exc.code,
            message=exc.message,
            details=exc.details,
        ),
        meta=ApiMeta(
            timestamp=format_iso_utc(),
            request_id=request_id,
        ),
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload.model_dump(),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Handles FastAPI RequestValidationError (HTTP 422) and formats it into the standard error envelope.
    """
    request_id = _extract_request_id(request)

    formatted_errors: List[dict[str, Any]] = []
    for err in exc.errors():
        # Exclude 'body' from loc for cleaner field paths
        loc_parts = [str(part) for part in err.get("loc", ()) if part != "body"]
        field_path = ".".join(loc_parts) if loc_parts else "request"
        formatted_errors.append(
            {
                "field": field_path,
                "message": err.get("msg", "Invalid value"),
                "type": err.get("type", "value_error"),
            }
        )

    error_payload = ApiErrorResponse(
        success=False,
        error=ApiErrorDetail(
            code="VALIDATION_ERROR",
            message="Request validation failed. Please check your inputs.",
            details=formatted_errors,
        ),
        meta=ApiMeta(
            timestamp=format_iso_utc(),
            request_id=request_id,
        ),
    )
    return JSONResponse(
        status_code=422,
        content=error_payload.model_dump(),
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """
    Handles standard HTTPExceptions (e.g. 404 Not Found, 405 Method Not Allowed).
    """
    request_id = _extract_request_id(request)

    # Map common status codes to human-readable error codes
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        429: "TOO_MANY_REQUESTS",
        500: "INTERNAL_SERVER_ERROR",
        501: "NOT_IMPLEMENTED",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
    }
    error_code = code_map.get(exc.status_code, f"HTTP_{exc.status_code}")
    message = str(exc.detail) if exc.detail else "An HTTP error occurred."

    error_payload = ApiErrorResponse(
        success=False,
        error=ApiErrorDetail(
            code=error_code,
            message=message,
            details=None,
        ),
        meta=ApiMeta(
            timestamp=format_iso_utc(),
            request_id=request_id,
        ),
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload.model_dump(),
    )


async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """
    Catch-all handler for unexpected internal server errors (HTTP 500).
    Logs the full stack trace internally but masks details from the client.
    """
    request_id = _extract_request_id(request)
    logger.exception(
        f"Unhandled exception on [{request.method} {request.url.path}] Request ID: {request_id}"
    )

    error_payload = ApiErrorResponse(
        success=False,
        error=ApiErrorDetail(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected internal server error occurred. Please try again later.",
            details=None,
        ),
        meta=ApiMeta(
            timestamp=format_iso_utc(),
            request_id=request_id,
        ),
    )
    return JSONResponse(
        status_code=500,
        content=error_payload.model_dump(),
    )
