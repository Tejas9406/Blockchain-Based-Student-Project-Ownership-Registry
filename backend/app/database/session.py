from typing import Generator, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from app.core.logging import logger

# Create SQLAlchemy synchronous engine
# Uses pool_pre_ping to automatically recover from dropped connections
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for yielding database session per request.
    Ensures session closure after request lifecycle.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_connection() -> Tuple[bool, str]:
    """
    Diagnostic helper to test PostgreSQL database reachability.
    Returns: (is_connected: bool, message: str)
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            scalar_val = result.scalar()
            if scalar_val == 1:
                return True, "Database connection healthy (PostgreSQL)."
            return False, "Database responded with unexpected result."
    except Exception as exc:
        logger.warning(f"Database connectivity check failed: {str(exc)}")
        return False, f"Database unavailable: {str(exc)}"
