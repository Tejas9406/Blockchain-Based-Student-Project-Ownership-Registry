import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.logging import logger
from app.routers import auth_router, health_router
from app.schemas.common import (
    ApiErrorDetail,
    ApiErrorResponse,
    ApiMeta,
    get_utc_now_iso,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager handling startup and shutdown events.
    """
    logger.info(f"Starting {settings.PROJECT_NAME} in [{settings.ENVIRONMENT}] environment.")
    logger.info(f"Interactive Swagger docs available at /docs")
    yield
    logger.info(f"Shutting down {settings.PROJECT_NAME}.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="REST API foundation for Blockchain-Based Student Project Ownership Registry (SIH 2026 CYB05)",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Request ID correlation middleware
@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or f"req-{uuid.uuid4().hex[:12]}"
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception Handlers
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(
            ApiErrorResponse(
                success=False,
                error=ApiErrorDetail(
                    code=exc.code,
                    message=exc.message,
                    details=exc.details,
                ),
                meta=ApiMeta(
                    timestamp=get_utc_now_iso(),
                    request_id=request_id,
                ),
            )
        ),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", None)
    formatted_errors = []
    for err in exc.errors():
        field_loc = ".".join(str(loc) for loc in err.get("loc", []))
        formatted_errors.append({
            "field": field_loc,
            "message": err.get("msg", ""),
            "type": err.get("type", ""),
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder(
            ApiErrorResponse(
                success=False,
                error=ApiErrorDetail(
                    code="VALIDATION_ERROR",
                    message="The submitted request body failed validation constraints.",
                    details={"errors": formatted_errors},
                ),
                meta=ApiMeta(
                    timestamp=get_utc_now_iso(),
                    request_id=request_id,
                ),
            )
        ),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(
            ApiErrorResponse(
                success=False,
                error=ApiErrorDetail(
                    code="HTTP_ERROR",
                    message=str(exc.detail),
                ),
                meta=ApiMeta(
                    timestamp=get_utc_now_iso(),
                    request_id=request_id,
                ),
            )
        ),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", None)
    logger.error(f"Unhandled server error [request_id={request_id}]: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=jsonable_encoder(
            ApiErrorResponse(
                success=False,
                error=ApiErrorDetail(
                    code="INTERNAL_SERVER_ERROR",
                    message="An unexpected internal server error occurred. Please contact system support.",
                ),
                meta=ApiMeta(
                    timestamp=get_utc_now_iso(),
                    request_id=request_id,
                ),
            )
        ),
    )


# Root-level health endpoint (GET /health)
app.include_router(health_router, prefix="")

# Versioned API prefix health endpoint (GET /api/v1/health)
app.include_router(health_router, prefix=settings.API_PREFIX)

# Versioned Authentication Router (POST /api/v1/auth/register)
app.include_router(auth_router, prefix=settings.API_PREFIX)
