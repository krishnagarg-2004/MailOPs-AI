"""
Unit tests for the Demo Data Seeder and One-Click Login Endpoint.
"""

from unittest.mock import MagicMock, patch
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.db.base import Base
from backend.app.models.user import User
from backend.app.models.email_thread import EmailThread
from backend.app.models.ai_analysis import AIAnalysis
from backend.app.models.extracted_action import ExtractedAction
from backend.app.scripts.seed_demo_data import seed_demo_environment, DEMO_USER_EMAIL


@pytest.fixture
def in_memory_db():
    """Provides an isolated SQLite in-memory database for testing the seeder logic."""
    engine = create_engine("sqlite:///:memory:")
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Note: VectorEmbedding uses pgvector which SQLite doesn't have by default,
    # so we mock out VectorEmbedding creation for SQLite unit tests.
    Base.metadata.create_all(bind=engine)
    session = TestingSession()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_seed_demo_environment_creates_records(in_memory_db):
    """Verify that seed_demo_environment populates user, threads, analyses, and actions."""
    summary = seed_demo_environment(db=in_memory_db, include_embeddings=False)

    assert summary["demo_user"] == DEMO_USER_EMAIL
    assert summary["threads_created"] == 4
    assert summary["actions_created"] >= 3

    # Verify user exists in database
    user = in_memory_db.query(User).filter_by(email=DEMO_USER_EMAIL).first()
    assert user is not None
    assert user.is_active is True

    # Verify threads exist
    threads = in_memory_db.query(EmailThread).filter_by(user_id=user.id).all()
    assert len(threads) == 4

    # Verify AI analyses
    analyses = in_memory_db.query(AIAnalysis).filter_by(user_id=user.id).all()
    assert len(analyses) == 4

    # Verify Extracted actions
    actions = in_memory_db.query(ExtractedAction).filter_by(user_id=user.id).all()
    assert len(actions) >= 3


def test_seed_demo_environment_idempotent(in_memory_db):
    """Running seeder twice should not duplicate records."""
    seed_demo_environment(db=in_memory_db, include_embeddings=False)
    second_summary = seed_demo_environment(db=in_memory_db, include_embeddings=False)

    # On second run, newly created counts should be 0 because records already exist
    assert second_summary["threads_created"] == 0
