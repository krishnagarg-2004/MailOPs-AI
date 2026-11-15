"""
Unit tests for Phase 7: Multi-Tenancy Organization Workspaces, RBAC Roles, and Audit Logging.
"""

import uuid
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.db.base import Base
from backend.app.models.audit_log import AuditLog
from backend.app.models.organization import Organization, RoleEnum, TeamMembership
from backend.app.models.user import User
from backend.app.services.audit_service import AuditService


@pytest.fixture
def in_memory_db():
    """Provides an isolated SQLite in-memory database."""
    engine = create_engine("sqlite:///:memory:")
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_create_organization_and_assign_rbac_role(in_memory_db):
    """Verify Organization creation and TeamMembership RBAC assignment."""
    user = User(email="org.admin@enterprise.com", full_name="Org Admin", is_active=True)
    in_memory_db.add(user)
    in_memory_db.commit()

    org = Organization(name="FinTech Corp", slug="fintech-corp", domain="fintech.com")
    in_memory_db.add(org)
    in_memory_db.commit()

    membership = TeamMembership(
        organization_id=org.id,
        user_id=user.id,
        role=RoleEnum.ADMIN.value,
    )
    in_memory_db.add(membership)
    in_memory_db.commit()

    # Query back
    saved_org = in_memory_db.query(Organization).filter_by(slug="fintech-corp").first()
    assert saved_org is not None
    assert len(saved_org.memberships) == 1
    assert saved_org.memberships[0].role == RoleEnum.ADMIN.value
    assert saved_org.memberships[0].user.email == "org.admin@enterprise.com"


def test_audit_service_records_immutable_events(in_memory_db):
    """Verify AuditService records compliance audit events with actor metadata."""
    user = User(email="compliance.officer@audit.com", full_name="Compliance Officer")
    in_memory_db.add(user)
    in_memory_db.commit()

    event = AuditService.record_event(
        db=in_memory_db,
        action_type="AI_DRAFT_APPROVED",
        target_entity_type="REPLY_DRAFT",
        target_entity_id="draft_xyz_123",
        user_id=user.id,
        ip_address="192.168.1.100",
        details={"diff_lines_changed": 3, "human_reviewed": True},
    )

    assert event.id is not None
    assert event.action_type == "AI_DRAFT_APPROVED"
    assert event.ip_address == "192.168.1.100"
    assert event.details["human_reviewed"] is True

    # Check query from database
    logs = in_memory_db.query(AuditLog).filter_by(user_id=user.id).all()
    assert len(logs) == 1
    assert logs[0].target_entity_type == "REPLY_DRAFT"
