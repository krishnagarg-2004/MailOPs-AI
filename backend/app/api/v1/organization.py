"""
Multi-Tenancy, Team Management and RBAC API Router for MailOps AI.
"""

from datetime import datetime
from typing import Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.db.session import get_db
from backend.app.models.audit_log import AuditLog
from backend.app.models.organization import Organization, RoleEnum, TeamMembership
from backend.app.models.user import User
from backend.app.services.audit_service import AuditService

router = APIRouter(prefix="/organization", tags=["Organization & RBAC"])


# Pydantic Schemas
class CreateOrganizationRequest(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    slug: str = Field(min_length=2, max_length=100)
    domain: Optional[str] = None


class MemberResponse(BaseModel):
    user_id: str
    email: str
    full_name: Optional[str]
    role: str
    joined_at: str


class OrganizationResponse(BaseModel):
    id: str
    name: str
    slug: str
    domain: Optional[str]
    my_role: str
    members_count: int


class InviteMemberRequest(BaseModel):
    email: str
    role: RoleEnum = RoleEnum.ANALYST


class AuditLogResponse(BaseModel):
    id: str
    action_type: str
    target_entity_type: str
    target_entity_id: Optional[str]
    ip_address: Optional[str]
    timestamp: str
    details: dict


@router.post("", response_model=OrganizationResponse)
async def create_organization(
    req: CreateOrganizationRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Creates a new Organization workspace and grants creator ADMIN role."""
    existing = db.execute(select(Organization).where(Organization.slug == req.slug)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization slug already taken.")

    org = Organization(name=req.name, slug=req.slug, domain=req.domain)
    db.add(org)
    db.flush()

    membership = TeamMembership(
        organization_id=org.id,
        user_id=current_user.id,
        role=RoleEnum.ADMIN.value,
    )
    db.add(membership)
    db.commit()

    # Record Audit Event
    AuditService.record_event(
        db=db,
        action_type="ORGANIZATION_CREATED",
        target_entity_type="ORGANIZATION",
        target_entity_id=str(org.id),
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
        details={"name": org.name, "slug": org.slug},
    )

    return OrganizationResponse(
        id=str(org.id),
        name=org.name,
        slug=org.slug,
        domain=org.domain,
        my_role=RoleEnum.ADMIN.value,
        members_count=1,
    )


@router.get("/my", response_model=list[OrganizationResponse])
async def get_my_organizations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lists all organizations where the current user is a member."""
    memberships = db.execute(
        select(TeamMembership).where(TeamMembership.user_id == current_user.id)
    ).scalars().all()

    results = []
    for m in memberships:
        org = m.organization
        count = db.execute(
            select(TeamMembership).where(TeamMembership.organization_id == org.id)
        ).scalars().all()
        results.append(
            OrganizationResponse(
                id=str(org.id),
                name=org.name,
                slug=org.slug,
                domain=org.domain,
                my_role=m.role,
                members_count=len(count),
            )
        )
    return results


@router.get("/audit-logs", response_model=list[AuditLogResponse])
async def get_audit_logs(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves immutable compliance audit logs for the current user's workspace."""
    logs = db.execute(
        select(AuditLog)
        .where(AuditLog.user_id == current_user.id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    ).scalars().all()

    return [
        AuditLogResponse(
            id=str(log.id),
            action_type=log.action_type,
            target_entity_type=log.target_entity_type,
            target_entity_id=log.target_entity_id,
            ip_address=log.ip_address,
            timestamp=log.created_at.isoformat(),
            details=log.details,
        )
        for log in logs
    ]
