import re
import uuid
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# Valid request ID pattern: alphanumeric, hyphen, underscore, 1 to 128 characters
REQUEST_ID_REGEX = re.compile(r"^[a-zA-Z0-9\-_]{1,128}$")


def generate_request_id() -> str:
    """Generates a human-readable unique request ID."""
    return f"req-{uuid.uuid4().hex[:12]}"


def is_valid_request_id(req_id: Optional[str]) -> bool:
    """Validates incoming client request ID format to prevent header injection."""
    if not req_id:
        return False
    return bool(REQUEST_ID_REGEX.match(req_id.strip()))


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that ensures every incoming request has an associated Request ID.
    - Preserves client-supplied 'X-Request-ID' or 'Request-ID' header if valid.
    - Generates a new unique Request ID if absent or invalid.
    - Attaches the Request ID to request.state and response headers.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Check for client-supplied header
        client_req_id = request.headers.get("X-Request-ID") or request.headers.get("Request-ID")

        if client_req_id and is_valid_request_id(client_req_id):
            request_id = client_req_id.strip()
        else:
            request_id = generate_request_id()

        # Attach to request state for dependency access & exception handlers
        request.state.request_id = request_id

        # Proceed with request pipeline
        response = await call_next(request)

        # Inject into response headers
        response.headers["X-Request-ID"] = request_id

        return response
