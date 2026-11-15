"""
Agentic Tool Execution Registry for MailOps AI.
Provides structured tools that AI reasoning agents can invoke to inspect past records,
check vendor invoices, and resolve graph dependencies.
"""

import json
import logging
import uuid
from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.business_document_extraction import BusinessDocumentExtraction
from backend.app.models.extracted_action import ExtractedAction
from backend.app.models.graph_edge import GraphEdge
from backend.app.models.graph_node import GraphNode

logger = logging.getLogger("mailops.agent.tools")


class AgentToolRegistry:
    """Registry of executable operational tools for autonomous agent workflows."""

    @classmethod
    def lookup_previous_invoice(
        cls, db: Session, user_id: uuid.UUID, vendor_name: str
    ) -> dict[str, Any]:
        """Tool: Looks up past invoices and line item costs for a vendor."""
        results = db.execute(
            select(BusinessDocumentExtraction).where(
                BusinessDocumentExtraction.user_id == user_id,
                BusinessDocumentExtraction.vendor_or_party.ilike(f"%{vendor_name}%"),
                BusinessDocumentExtraction.document_category == "INVOICE",
            )
        ).scalars().all()

        if not results:
            return {"found": False, "message": f"No previous invoices found for vendor: {vendor_name}"}

        invoices = []
        for r in results:
            data = r.extracted_data or {}
            invoices.append({
                "invoice_number": r.document_reference_number or data.get("invoice_number"),
                "total_amount": data.get("total_amount"),
                "due_date": data.get("due_date"),
                "currency": data.get("currency", "USD"),
            })

        return {"found": True, "vendor": vendor_name, "invoices": invoices}

    @classmethod
    def query_action_dependencies(
        cls, db: Session, user_id: uuid.UUID, action_description: str
    ) -> dict[str, Any]:
        """Tool: Discovers blocking prerequisites or dependencies for an action."""
        action = db.execute(
            select(ExtractedAction).where(
                ExtractedAction.user_id == user_id,
                ExtractedAction.description.ilike(f"%{action_description}%"),
            )
        ).scalars().first()

        if not action:
            return {"found": False, "message": f"Action '{action_description}' not found."}

        # Check graph nodes for this action
        node = db.execute(
            select(GraphNode).where(
                GraphNode.user_id == user_id,
                GraphNode.entity_reference_id == action.id,
            )
        ).scalar_one_or_none()

        blocking = []
        if node:
            edges = db.execute(
                select(GraphEdge).where(
                    GraphEdge.user_id == user_id,
                    GraphEdge.source_node_id == node.id,
                    GraphEdge.relationship_type.in_(["DEPENDS_ON", "BLOCKED_BY"]),
                )
            ).scalars().all()
            for edge in edges:
                target_node = db.execute(
                    select(GraphNode).where(GraphNode.id == edge.target_node_id)
                ).scalar_one_or_none()
                if target_node:
                    blocking.append(target_node.label)

        return {
            "found": True,
            "action": action.description,
            "status": action.status,
            "blocking_prerequisites": blocking,
        }

    @classmethod
    def execute_tool_call(
        cls, db: Session, user_id: uuid.UUID, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """Dispatches an agent tool invocation by name."""
        logger.info(f"Executing Agent Tool: {tool_name} with args={arguments}")

        if tool_name == "lookup_previous_invoice":
            vendor = str(arguments.get("vendor_name", ""))
            return cls.lookup_previous_invoice(db, user_id, vendor)

        elif tool_name == "query_action_dependencies":
            desc = str(arguments.get("action_description", ""))
            return cls.query_action_dependencies(db, user_id, desc)

        else:
            return {"error": f"Unknown tool: {tool_name}"}
