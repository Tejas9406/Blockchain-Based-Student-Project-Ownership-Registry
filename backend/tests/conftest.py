from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database.session import SessionLocal, engine
from app.database.base import Base


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    """
    TestClient fixture for executing synchronous API requests against the FastAPI app.
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """
    Provides an isolated database session per test by executing within a rolled-back transaction.
    Ensures zero state leakage between test executions.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)

    yield session

    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()
