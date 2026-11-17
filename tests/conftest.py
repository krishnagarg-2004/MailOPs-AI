"""
EnterpriseAIMailOPs_MIPRO Global Test Configuration and Fixtures.
Provides isolated in-memory SQLite database sessions, dependency-injected FastAPI test clients,
authenticated test users, and mock providers.
"""

from collections.abc import Generator
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.config import settings
from backend.app.db.base import Base
from backend.app.db.session import get_db
import backend.app.models
from backend.app.main import app
from tests.test_helpers import create_test_auth_session, create_test_email


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Ensure test environment variables and offline AI provider are set."""
    settings.AI_PROVIDER_TYPE = "mock"
    settings.APP_ENV = "test"
    with patch("backend.app.main._ensure_migrations_applied"), patch(
        "backend.app.main._reset_stale_syncing_states"
    ):
        yield


@pytest.fixture(scope="function")
def test_engine():
    """Create an isolated, in-memory SQLite engine with StaticPool."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def session_factory(test_engine):
    """Provide a thread-safe session factory bound to the in-memory SQLite database."""
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session(session_factory) -> Generator[Session, None, None]:
    """Provide a clean, isolated database session per test function for test setup/assertions."""
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def test_app(session_factory):
    """Provide FastAPI application with database dependency overridden to test session factory."""
    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield app
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client(test_app) -> Generator[TestClient, None, None]:
    """Provide a TestClient bound to the FastAPI application."""
    yield TestClient(test_app)


@pytest.fixture(scope="function")
def auth_user(db_session: Session):
    """Provide a standard authenticated user with active session cookies."""
    user, cookies, raw_token = create_test_auth_session(db_session)
    return {
        "user": user,
        "cookies": cookies,
        "raw_token": raw_token,
    }


@pytest.fixture(scope="function")
def test_email(db_session: Session, auth_user):
    """Provide an EmailThread and EmailMessage for the authenticated user."""
    user = auth_user["user"]
    thread, message = create_test_email(db_session, user.id)
    return {
        "thread": thread,
        "message": message,
    }
