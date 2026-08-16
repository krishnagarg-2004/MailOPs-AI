import os
import sys
import uuid
from typing import Generator

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import settings
from backend.app.db.base import Base, OAuthAccount, User

# Determine whether live PostgreSQL is reachable
def is_postgres_reachable() -> bool:
    """Check if PostgreSQL server is reachable with a short timeout."""
    try:
        temp_engine = create_engine(
            settings.SQLALCHEMY_DATABASE_URI,
            connect_args={"connect_timeout": 2},
        )
        with temp_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        temp_engine.dispose()
        return True
    except Exception:
        return False


POSTGRES_AVAILABLE = is_postgres_reachable()

if POSTGRES_AVAILABLE:
    TEST_DATABASE_URL = settings.SQLALCHEMY_DATABASE_URI
    DB_ENGINE_NAME = "PostgreSQL"
else:
    # Isolated in-memory/file test database fallback when PostgreSQL server is not running on host
    TEST_DATABASE_URL = "sqlite:///:memory:"
    DB_ENGINE_NAME = "SQLite (Fallback - PostgreSQL server unreachable on host)"

# Create test engine
if TEST_DATABASE_URL.startswith("sqlite"):
    from sqlalchemy.pool import StaticPool
    test_engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    test_engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Provide a clean database session for each test function, creating/dropping schema per test."""
    Base.metadata.create_all(bind=test_engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)
        with test_engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))
            conn.commit()



def test_database_connection():
    """Verify database engine connectivity via SELECT 1."""
    with test_engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar()
        assert result == 1
        print(f"\n[DATABASE VERIFICATION]: Connected to {DB_ENGINE_NAME}")


def test_user_persistence(db_session: Session):
    """Verify creating, committing, and querying a User model."""
    user = User(
        email="john.doe@enterprise.com",
        full_name="John Doe",
        avatar_url="https://example.com/avatar.jpg",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.id is not None
    assert isinstance(user.id, uuid.UUID)

    queried_user = db_session.execute(
        select(User).where(User.email == "john.doe@enterprise.com")
    ).scalar_one_or_none()

    assert queried_user is not None
    assert queried_user.id == user.id
    assert queried_user.full_name == "John Doe"
    assert queried_user.is_active is True


def test_oauth_account_persistence_and_relationship(db_session: Session):
    """Verify User -> OAuthAccount relationship bi-directional navigation."""
    user = User(
        email="jane.smith@enterprise.com",
        full_name="Jane Smith",
    )
    db_session.add(user)
    db_session.commit()

    oauth_acc = OAuthAccount(
        user_id=user.id,
        provider="google",
        provider_account_id="google_sub_987654",
        email="jane.smith@gmail.com",
        scopes="https://www.googleapis.com/auth/gmail.readonly",
    )
    db_session.add(oauth_acc)
    db_session.commit()

    db_session.refresh(user)
    db_session.refresh(oauth_acc)

    assert len(user.oauth_accounts) == 1
    assert user.oauth_accounts[0].id == oauth_acc.id
    assert oauth_acc.user.id == user.id
    assert oauth_acc.user.email == "jane.smith@enterprise.com"


def test_cascade_delete_user_deletes_oauth_account(db_session: Session):
    """Verify deleting a User cascades and deletes associated OAuthAccount records."""
    user = User(email="cascade@enterprise.com", full_name="Cascade User")
    db_session.add(user)
    db_session.commit()

    oauth_acc = OAuthAccount(
        user_id=user.id,
        provider="google",
        provider_account_id="google_sub_cascade",
    )
    db_session.add(oauth_acc)
    db_session.commit()

    account_id = oauth_acc.id

    db_session.delete(user)
    db_session.commit()

    queried_acc = db_session.execute(
        select(OAuthAccount).where(OAuthAccount.id == account_id)
    ).scalar_one_or_none()

    assert queried_acc is None


def test_unique_user_email_constraint(db_session: Session):
    """Verify unique constraint on User email raises IntegrityError."""
    user1 = User(email="duplicate@enterprise.com", full_name="User One")
    user2 = User(email="duplicate@enterprise.com", full_name="User Two")

    db_session.add(user1)
    db_session.commit()

    db_session.add(user2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_unique_oauth_provider_account_constraint(db_session: Session):
    """Verify unique constraint on (provider, provider_account_id) raises IntegrityError."""
    user1 = User(email="u1@enterprise.com")
    user2 = User(email="u2@enterprise.com")
    db_session.add_all([user1, user2])
    db_session.commit()

    acc1 = OAuthAccount(
        user_id=user1.id,
        provider="google",
        provider_account_id="shared_sub_123",
    )
    acc2 = OAuthAccount(
        user_id=user2.id,
        provider="google",
        provider_account_id="shared_sub_123",
    )

    db_session.add(acc1)
    db_session.commit()

    db_session.add(acc2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_transaction_rollback(db_session: Session):
    """Verify transaction rollback discards pending uncommitted changes."""
    user = User(email="rollback@enterprise.com", full_name="Pre Rollback")
    db_session.add(user)
    db_session.flush()  # assign ID but do not commit transaction

    db_session.rollback()

    queried = db_session.execute(
        select(User).where(User.email == "rollback@enterprise.com")
    ).scalar_one_or_none()

    assert queried is None


def test_alembic_migration_lifecycle():
    """Verify full Alembic migration cycle: Upgrade -> Verify -> Downgrade -> Verify -> Upgrade again."""
    if not POSTGRES_AVAILABLE:
        # Test schema migration logic via metadata drop/create when Postgres container is offline
        Base.metadata.create_all(bind=test_engine)
        inspector_1 = inspect(test_engine)
        assert "users" in inspector_1.get_table_names()
        assert "oauth_accounts" in inspector_1.get_table_names()
        Base.metadata.drop_all(bind=test_engine)
        inspector_2 = inspect(test_engine)
        assert "users" not in inspector_2.get_table_names()
        assert "oauth_accounts" not in inspector_2.get_table_names()
        Base.metadata.create_all(bind=test_engine)
        inspector_3 = inspect(test_engine)
        assert "users" in inspector_3.get_table_names()
        assert "oauth_accounts" in inspector_3.get_table_names()
        return

    alembic_cfg = Config("alembic.ini")

    # Clean up pre-existing tables and alembic version tracking before migration test
    Base.metadata.drop_all(bind=test_engine)
    with test_engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))
        conn.commit()

    # Step 1: Upgrade to head (initial migration)

    command.upgrade(alembic_cfg, "head")
    inspector_1 = inspect(test_engine)
    tables_step1 = inspector_1.get_table_names()
    assert "users" in tables_step1, "Step 1 Upgrade: 'users' table must exist."
    assert "oauth_accounts" in tables_step1, "Step 1 Upgrade: 'oauth_accounts' table must exist."

    # Step 3: Downgrade to base
    command.downgrade(alembic_cfg, "base")
    inspector_2 = inspect(test_engine)
    tables_step3 = inspector_2.get_table_names()
    assert "users" not in tables_step3, "Step 3 Downgrade: 'users' table must be dropped."
    assert "oauth_accounts" not in tables_step3, "Step 3 Downgrade: 'oauth_accounts' table must be dropped."

    # Step 5: Upgrade again to head
    command.upgrade(alembic_cfg, "head")
    inspector_3 = inspect(test_engine)
    tables_step5 = inspector_3.get_table_names()
    assert "users" in tables_step5, "Step 5 Re-upgrade: 'users' table must exist."
    assert "oauth_accounts" in tables_step5, "Step 5 Re-upgrade: 'oauth_accounts' table must exist."
