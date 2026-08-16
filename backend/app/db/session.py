from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import settings

# Engine configuration with connection pre-ping for pool health
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
    future=True,
)

# Session factory for producing request-scoped database sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, Any, None]:
    """FastAPI dependency for request-scoped database session management.
    
    Yields:
        Session: A fresh SQLAlchemy database session.
    Ensures:
        Session is closed cleanly after request processing.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
