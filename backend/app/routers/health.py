from fastapi import APIRouter
from app.core.config import settings
from app.database.session import check_database_connection
from app.schemas.health import HealthCheckResponse, DatabaseStatus

router = APIRouter(tags=["Health & Diagnostics"])


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Service Health Check",
    description="Returns backend service operational status and diagnostic database connectivity state."
)
def get_health() -> HealthCheckResponse:
    is_db_connected, db_message = check_database_connection()
    return HealthCheckResponse(
        status="ok",
        service="backend",
        environment=settings.ENVIRONMENT,
        version=settings.VERSION,
        database=DatabaseStatus(
            connected=is_db_connected,
            details=db_message
        )
    )
