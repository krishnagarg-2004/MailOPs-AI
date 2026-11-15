"""
Executive Intelligence Digest and Multi-Format Export API for MailOps AI.
Provides aggregated KPIs, risk registers, action trackers, and downloadable CSV/Markdown reports.
"""

import csv
import io
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Response, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.db.session import get_db
from backend.app.models.ai_analysis import AIAnalysis
from backend.app.models.business_document_extraction import BusinessDocumentExtraction
from backend.app.models.extracted_action import ExtractedAction
from backend.app.models.user import User

router = APIRouter(prefix="/digest", tags=["Executive Digest & Reporting"])


class DigestItem(BaseModel):
    id: str
    item_type: str
    description: str
    assignee: Optional[str] = None
    due_date: Optional[str] = None
    severity_or_priority: str
    status: str
    evidence_snippet: Optional[str] = None


class ExecutiveDigestSummary(BaseModel):
    generated_at: str
    user_email: str
    total_emails_analyzed: int
    total_actions: int
    pending_actions: int
    confirmed_actions: int
    completed_actions: int
    total_risks: int
    high_severity_risks: int
    total_decisions: int
    total_financial_value: float
    top_actions: List[DigestItem]
    active_risks: List[DigestItem]
    recent_decisions: List[DigestItem]


def _build_digest_data(user: User, db: Session):
    # Total analyzed emails
    total_emails_analyzed = (
        db.execute(select(func.count(AIAnalysis.id)).where(AIAnalysis.user_id == user.id)).scalar() or 0
    )

    # Actions, Risks, Decisions
    all_items = (
        db.execute(
            select(ExtractedAction)
            .where(ExtractedAction.user_id == user.id)
            .order_by(ExtractedAction.created_at.desc())
        )
        .scalars()
        .all()
    )

    actions = [it for it in all_items if it.item_type == "ACTION"]
    risks = [it for it in all_items if it.item_type == "RISK"]
    decisions = [it for it in all_items if it.item_type == "DECISION"]

    pending_actions = sum(1 for a in actions if a.status == "PENDING")
    confirmed_actions = sum(1 for a in actions if a.status == "CONFIRMED")
    completed_actions = sum(1 for a in actions if a.status == "COMPLETED")
    high_severity_risks = sum(1 for r in risks if r.severity_or_priority.upper() == "HIGH")

    # Financial Total
    total_financial_val = (
        db.execute(
            select(func.sum(BusinessDocumentExtraction.financial_total)).where(
                BusinessDocumentExtraction.user_id == user.id
            )
        ).scalar()
        or 0.0
    )

    # Convert to schema items
    def to_digest_item(it: ExtractedAction) -> DigestItem:
        return DigestItem(
            id=str(it.id),
            item_type=it.item_type,
            description=it.description,
            assignee=it.assignee,
            due_date=it.due_date.isoformat() if it.due_date else None,
            severity_or_priority=it.severity_or_priority,
            status=it.status,
            evidence_snippet=it.evidence_snippet,
        )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "user_email": user.email,
        "total_emails_analyzed": total_emails_analyzed,
        "total_actions": len(actions),
        "pending_actions": pending_actions,
        "confirmed_actions": confirmed_actions,
        "completed_actions": completed_actions,
        "total_risks": len(risks),
        "high_severity_risks": high_severity_risks,
        "total_decisions": len(decisions),
        "total_financial_value": float(total_financial_val),
        "top_actions": [to_digest_item(a) for a in actions[:15]],
        "active_risks": [to_digest_item(r) for r in risks[:10]],
        "recent_decisions": [to_digest_item(d) for d in decisions[:10]],
        "all_items": all_items,
    }


@router.get("/summary", response_model=ExecutiveDigestSummary)
async def get_digest_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns aggregated executive KPIs, actions, risks, and financial summaries."""
    data = _build_digest_data(current_user, db)
    return ExecutiveDigestSummary(
        generated_at=data["generated_at"],
        user_email=data["user_email"],
        total_emails_analyzed=data["total_emails_analyzed"],
        total_actions=data["total_actions"],
        pending_actions=data["pending_actions"],
        confirmed_actions=data["confirmed_actions"],
        completed_actions=data["completed_actions"],
        total_risks=data["total_risks"],
        high_severity_risks=data["high_severity_risks"],
        total_decisions=data["total_decisions"],
        total_financial_value=data["total_financial_value"],
        top_actions=data["top_actions"],
        active_risks=data["active_risks"],
        recent_decisions=data["recent_decisions"],
    )


@router.get("/export")
async def export_digest(
    format: str = Query(default="csv", pattern="^(csv|markdown|json)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Exports a downloadable executive intelligence digest in CSV, Markdown, or JSON.
    """
    data = _build_digest_data(current_user, db)

    if format == "json":
        summary = ExecutiveDigestSummary(
            generated_at=data["generated_at"],
            user_email=data["user_email"],
            total_emails_analyzed=data["total_emails_analyzed"],
            total_actions=data["total_actions"],
            pending_actions=data["pending_actions"],
            confirmed_actions=data["confirmed_actions"],
            completed_actions=data["completed_actions"],
            total_risks=data["total_risks"],
            high_severity_risks=data["high_severity_risks"],
            total_decisions=data["total_decisions"],
            total_financial_value=data["total_financial_value"],
            top_actions=data["top_actions"],
            active_risks=data["active_risks"],
            recent_decisions=data["recent_decisions"],
        )
        return summary.model_dump()

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        # Header
        writer.writerow(
            [
                "Item Type",
                "ID",
                "Description",
                "Assignee",
                "Priority/Severity",
                "Status",
                "Due Date",
                "Evidence Snippet",
            ]
        )

        for item in data["all_items"]:
            writer.writerow(
                [
                    item.item_type,
                    str(item.id),
                    item.description,
                    item.assignee or "Unassigned",
                    item.severity_or_priority,
                    item.status,
                    item.due_date.strftime("%Y-%m-%d %H:%M UTC") if item.due_date else "None",
                    item.evidence_snippet or "",
                ]
            )

        csv_bytes = output.getvalue()
        return Response(
            content=csv_bytes,
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="mailops-executive-digest.csv"'},
        )

    # Markdown format
    md_lines = [
        "# MailOps AI — Executive Intelligence Digest",
        f"**Generated:** {data['generated_at']} | **Account:** {data['user_email']}",
        "",
        "## Executive KPI Summary",
        "| Metric | Value |",
        "| :--- | :--- |",
        f"| Emails Analyzed | {data['total_emails_analyzed']} |",
        f"| Total Action Items | {data['total_actions']} (Pending: {data['pending_actions']}, Confirmed: {data['confirmed_actions']}, Completed: {data['completed_actions']}) |",
        f"| Identified Business Risks | {data['total_risks']} ({data['high_severity_risks']} High Severity) |",
        f"| Key Strategic Decisions | {data['total_decisions']} |",
        f"| Tracked Financial Exposure | ${data['total_financial_value']:,.2f} |",
        "",
        "## Priority Action Items",
    ]

    if data["top_actions"]:
        for idx, a in enumerate(data["top_actions"], 1):
            due = f" (Due: {a.due_date})" if a.due_date else ""
            assignee = f" [@{a.assignee}]" if a.assignee else ""
            md_lines.append(f"{idx}. **[{a.status}]** {a.description}{assignee}{due} — Priority: `{a.severity_or_priority}`")
    else:
        md_lines.append("_No pending action items found._")

    md_lines.append("")
    md_lines.append("## Active Business Risks")
    if data["active_risks"]:
        for idx, r in enumerate(data["active_risks"], 1):
            md_lines.append(f"{idx}. **[{r.severity_or_priority}]** {r.description}")
            if r.evidence_snippet:
                md_lines.append(f"   > _Evidence: \"{r.evidence_snippet}\"_")
    else:
        md_lines.append("_No active business risks logged._")

    md_lines.append("")
    md_lines.append("## Strategic Decisions")
    if data["recent_decisions"]:
        for idx, d in enumerate(data["recent_decisions"], 1):
            md_lines.append(f"{idx}. {d.description}")
    else:
        md_lines.append("_No recorded decisions._")

    md_content = "\n".join(md_lines)
    return Response(
        content=md_content,
        media_type="text/markdown",
        headers={"Content-Disposition": 'attachment; filename="mailops-executive-digest.md"'},
    )
