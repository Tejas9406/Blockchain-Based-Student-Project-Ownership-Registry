from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import logger
from app.routers import health_router


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

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root-level health endpoint (GET /health)
app.include_router(health_router, prefix="")

# Versioned API prefix health endpoint (GET /api/v1/health)
app.include_router(health_router, prefix=settings.API_PREFIX)
