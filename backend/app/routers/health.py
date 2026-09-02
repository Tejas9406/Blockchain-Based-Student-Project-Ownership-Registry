from fastapi import APIRouter
from app.core.config import settings
from app.database.session import check_database_connection
from app.schemas.health import BlockchainStatus, DatabaseStatus, HealthCheckResponse

router = APIRouter(tags=["Health & Diagnostics"])


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Service Health Check",
    description="Returns backend service operational status and diagnostic database connectivity state."
)
def get_health() -> HealthCheckResponse:
    is_db_connected, db_message = check_database_connection()

    blockchain_status = None
    try:
        from app.services.blockchain_service import get_blockchain_service
        service = get_blockchain_service()
        is_bc_connected = service.is_connected()
        chain_id = service.get_chain_id() if is_bc_connected else None
        latest_block = service.get_latest_block() if is_bc_connected else None
        blockchain_status = BlockchainStatus(
            connected=is_bc_connected,
            chain_id=chain_id,
            latest_block=latest_block,
            contract_address=service.contract_address,
            relayer_address=service.relayer_address,
        )
    except Exception:
        blockchain_status = BlockchainStatus(connected=False)

    return HealthCheckResponse(
        status="ok",
        service="backend",
        environment=settings.ENVIRONMENT,
        version=settings.VERSION,
        database=DatabaseStatus(
            connected=is_db_connected,
            details=db_message
        ),
        blockchain=blockchain_status,
    )
