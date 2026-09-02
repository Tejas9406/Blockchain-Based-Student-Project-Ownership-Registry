from fastapi import APIRouter
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from app.api.dependencies import Pagination
from app.core.exceptions import (
    AppException,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    NotImplementedAppError,
    UnauthorizedError,
)
from app.main import app
from app.schemas.common import ApiMeta, ApiResponse
from app.schemas.error import ApiErrorResponse
from app.schemas.pagination import ApiPaginatedResponse, PaginatedMeta


# ==============================================================================
# 1. Schemas & Envelopes Unit Tests
# ==============================================================================


def test_api_meta_and_success_envelope():
    """Test 1: Universal success response envelope structure and UTC timestamp format."""
    meta = ApiMeta(request_id="req-test-12345")
    assert meta.request_id == "req-test-12345"
    assert meta.timestamp.endswith("Z")

    response = ApiResponse[dict](
        success=True,
        data={"user_id": "USR-202609-00001", "name": "Alice"},
        meta=meta,
    )
    dumped = response.model_dump()
    assert dumped["success"] is True
    assert dumped["data"]["user_id"] == "USR-202609-00001"
    assert dumped["meta"]["request_id"] == "req-test-12345"
    assert "timestamp" in dumped["meta"]


def test_pagination_meta_calculation():
    """Test 2: PaginatedMeta factory calculations for pages, has_next, and has_prev."""
    # Case A: Middle page
    meta_mid = PaginatedMeta.create(page=2, page_size=20, total_items=55, request_id="req-1")
    assert meta_mid.page == 2
    assert meta_mid.page_size == 20
    assert meta_mid.total_items == 55
    assert meta_mid.total_pages == 3
    assert meta_mid.has_next is True
    assert meta_mid.has_prev is True

    # Case B: First page
    meta_first = PaginatedMeta.create(page=1, page_size=20, total_items=55)
    assert meta_first.has_next is True
    assert meta_first.has_prev is False

    # Case C: Last page
    meta_last = PaginatedMeta.create(page=3, page_size=20, total_items=55)
    assert meta_last.has_next is False
    assert meta_last.has_prev is True

    # Case D: Empty results
    meta_empty = PaginatedMeta.create(page=1, page_size=20, total_items=0)
    assert meta_empty.total_pages == 0
    assert meta_empty.has_next is False
    assert meta_empty.has_prev is False

    # Paginated envelope
    paginated_resp = ApiPaginatedResponse[str](
        success=True,
        data=["item1", "item2"],
        meta=meta_mid,
    )
    assert paginated_resp.success is True
    assert len(paginated_resp.data) == 2


def test_error_response_envelope():
    """Test 3: Universal error response envelope structure."""
    err_resp = ApiErrorResponse(
        success=False,
        error={
            "code": "PROJECT_NOT_FOUND",
            "message": "The requested project was not found.",
            "details": {"project_id": "PRJ-202609-00000"},
        },
        meta=ApiMeta(request_id="req-err-01"),
    )
    dumped = err_resp.model_dump()
    assert dumped["success"] is False
    assert dumped["error"]["code"] == "PROJECT_NOT_FOUND"
    assert dumped["error"]["details"]["project_id"] == "PRJ-202609-00000"
    assert dumped["meta"]["request_id"] == "req-err-01"


# ==============================================================================
# 2. Mock Endpoints Setup for Middleware & Exception Handlers
# ==============================================================================

mock_router = APIRouter(prefix="/mock-foundation", tags=["Mock Foundation"])


class SampleItem(BaseModel):
    name: str = Field(..., min_length=3)
    score: int = Field(..., ge=0, le=100)


@mock_router.get("/success")
def mock_success_endpoint():
    return ApiResponse(
        data={"message": "foundation working properly"},
        meta=ApiMeta(request_id="req-custom-success"),
    )


@mock_router.get("/paginated")
def mock_paginated_endpoint(pagination: Pagination):
    items = [f"item_{i}" for i in range(pagination.offset, pagination.offset + pagination.limit)]
    meta = PaginatedMeta.create(
        page=pagination.page,
        page_size=pagination.page_size,
        total_items=100,
    )
    return ApiPaginatedResponse(data=items, meta=meta)


@mock_router.get("/app-exception")
def mock_app_exception_endpoint(error_type: str = "not_found"):
    if error_type == "not_found":
        raise NotFoundError("Custom item not found.", code="ITEM_NOT_FOUND", details={"id": 42})
    elif error_type == "unauthorized":
        raise UnauthorizedError("Invalid credentials.")
    elif error_type == "forbidden":
        raise ForbiddenError("Access forbidden.")
    elif error_type == "conflict":
        raise ConflictError("Duplicate resource.", details={"key": "email"})
    elif error_type == "not_implemented":
        raise NotImplementedAppError("Feature in development.")
    raise AppException("Generic bad request.", code="CUSTOM_BAD_REQUEST", status_code=400)


@mock_router.post("/validation")
def mock_validation_endpoint(payload: SampleItem):
    return ApiResponse(data=payload.model_dump())


@mock_router.get("/unhandled-error")
def mock_unhandled_error_endpoint():
    # Intentionally trigger an unhandled runtime error
    raise RuntimeError("Simulated unhandled runtime error")


# Mount mock router on app
app.include_router(mock_router)


# ==============================================================================
# 3. HTTP Integration Tests via TestClient
# ==============================================================================


def test_request_id_generation(client: TestClient):
    """Test 4: Request ID is automatically generated and returned in header."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    req_id = response.headers["X-Request-ID"]
    assert req_id.startswith("req-")


def test_request_id_preservation(client: TestClient):
    """Test 5: Client-supplied X-Request-ID is validated and preserved."""
    client_id = "client-trace-98765-xyz"
    response = client.get("/health", headers={"X-Request-ID": client_id})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == client_id


def test_app_exception_handling(client: TestClient):
    """Test 6: AppException subclasses formatted as standard ApiErrorResponse."""
    # 404 Not Found
    res_404 = client.get("/mock-foundation/app-exception?error_type=not_found")
    assert res_404.status_code == 404
    data_404 = res_404.json()
    assert data_404["success"] is False
    assert data_404["error"]["code"] == "ITEM_NOT_FOUND"
    assert data_404["error"]["details"] == {"id": 42}
    assert "timestamp" in data_404["meta"]
    assert "request_id" in data_404["meta"]

    # 401 Unauthorized
    res_401 = client.get("/mock-foundation/app-exception?error_type=unauthorized")
    assert res_401.status_code == 401
    assert res_401.json()["error"]["code"] == "UNAUTHORIZED"

    # 403 Forbidden
    res_403 = client.get("/mock-foundation/app-exception?error_type=forbidden")
    assert res_403.status_code == 403
    assert res_403.json()["error"]["code"] == "FORBIDDEN"

    # 409 Conflict
    res_409 = client.get("/mock-foundation/app-exception?error_type=conflict")
    assert res_409.status_code == 409
    assert res_409.json()["error"]["code"] == "CONFLICT"

    # 501 Not Implemented
    res_501 = client.get("/mock-foundation/app-exception?error_type=not_implemented")
    assert res_501.status_code == 501
    assert res_501.json()["error"]["code"] == "NOT_IMPLEMENTED"


def test_validation_error_handling(client: TestClient):
    """Test 7: RequestValidationError (422) formatted into ApiErrorResponse."""
    response = client.post(
        "/mock-foundation/validation",
        json={"name": "a", "score": 200},
    )
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert isinstance(data["error"]["details"], list)
    assert len(data["error"]["details"]) >= 2
    fields = [d["field"] for d in data["error"]["details"]]
    assert "name" in fields
    assert "score" in fields


def test_http_404_error_handling(client: TestClient):
    """Test 8: Standard HTTP 404 on nonexistent route is formatted in envelope."""
    response = client.get("/api/v1/nonexistent-route-999")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "NOT_FOUND"
    assert "meta" in data


def test_unhandled_exception_handling():
    """Test 9: Unhandled 500 exceptions masked safely without exposing stack traces."""
    with TestClient(app, raise_server_exceptions=False) as safe_client:
        response = safe_client.get("/mock-foundation/unhandled-error")
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
        assert "Simulated unhandled runtime error" not in str(data)
        assert "meta" in data


def test_pagination_endpoint_validation(client: TestClient):
    """Test 10: Pagination query parameters validation."""
    # Valid pagination
    res_valid = client.get("/mock-foundation/paginated?page=2&page_size=10")
    assert res_valid.status_code == 200
    d = res_valid.json()
    assert d["success"] is True
    assert d["meta"]["page"] == 2
    assert d["meta"]["page_size"] == 10
    assert len(d["data"]) == 10

    # Invalid page < 1
    res_invalid_page = client.get("/mock-foundation/paginated?page=0")
    assert res_invalid_page.status_code == 422
    assert res_invalid_page.json()["error"]["code"] == "VALIDATION_ERROR"

    # Invalid page_size > 100
    res_invalid_size = client.get("/mock-foundation/paginated?page_size=101")
    assert res_invalid_size.status_code == 422


def test_backward_compatibility_health_endpoints(client: TestClient):
    """Test 11: GET /health and GET /api/v1/health continue working."""
    res_root = client.get("/health")
    assert res_root.status_code == 200
    assert res_root.json()["status"] == "ok"
    assert res_root.json()["service"] == "backend"

    res_v1 = client.get("/api/v1/health")
    assert res_v1.status_code == 200
    assert res_v1.json()["status"] == "ok"


def test_openapi_and_docs_endpoints(client: TestClient):
    """Test 12: OpenAPI docs endpoints are available."""
    res_docs = client.get("/docs")
    assert res_docs.status_code == 200

    res_openapi = client.get("/openapi.json")
    assert res_openapi.status_code == 200
    spec = res_openapi.json()
    assert spec["info"]["title"] == "Student Project Ownership Registry API"
    assert "/health" in spec["paths"]
    assert "/api/v1/health" in spec["paths"]


def test_router_placeholders(client: TestClient):
    """Test 13: Domain router placeholders return 501 Not Implemented (implemented modules return auth or success)."""
    res_art = client.post("/api/v1/artifacts/upload")
    assert res_art.status_code == 401  # Implemented in Step 4.4, requires JWT auth

    res_ver = client.get("/api/v1/verification/verify-registration/REG-2026-00001")
    assert res_ver.status_code == 404  # Implemented in Step 4.5: public verification endpoint (404 when not found)

    res_cert = client.get("/api/v1/certificates/REG-2026-001")
    assert res_cert.status_code == 501

    res_disp = client.post("/api/v1/disputes")
    assert res_disp.status_code == 401  # Implemented in Step 8, requires JWT auth

    res_adm = client.get("/api/v1/admin/audit-logs")
    assert res_adm.status_code == 501

