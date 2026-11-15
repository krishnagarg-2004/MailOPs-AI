"""
DSPy Signatures for MailOps AI.
Defines input-output interfaces for structured extraction and RAG answer generation.
"""

from typing import Any
import dspy


class EmailIntelligenceSignature(dspy.Signature):
    """
    Analyze enterprise emails to classify intent and extract action items
    with strict verbatim evidence quotes.
    """
    sender: str = dspy.InputField(desc="Email sender address or name")
    subject: str = dspy.InputField(desc="Email subject line")
    body: str = dspy.InputField(desc="Email body text within untrusted content bounds")

    summary: str = dspy.OutputField(desc="1-2 sentence executive operational summary")
    intent: str = dspy.OutputField(desc="One of WORK_REQUEST, STATUS_UPDATE, FINANCIAL_INVOICE, CONTRACT_LEGAL, URGENT_ACTION, INFORMATIONAL, OTHER")
    priority: str = dspy.OutputField(desc="One of HIGH, MEDIUM, LOW")
    sentiment: str = dspy.OutputField(desc="One of POSITIVE, NEUTRAL, NEGATIVE")
    actions: list[dict[str, Any]] = dspy.OutputField(desc="List of objects with description, priority, and verbatim evidence_snippet")
    decisions: list[dict[str, Any]] = dspy.OutputField(desc="List of decisions with description and verbatim evidence_snippet")
    risks: list[dict[str, Any]] = dspy.OutputField(desc="List of operational risks with description, severity, and verbatim evidence_snippet")


class RAGQuestionAnsweringSignature(dspy.Signature):
    """
    Answer operational questions grounded in retrieved email context chunks with exact citations.
    """
    context: str = dspy.InputField(desc="Retrieved email thread context chunks and metadata")
    question: str = dspy.InputField(desc="User's operational query about emails, deadlines, or decisions")

    answer: str = dspy.OutputField(desc="Direct, factual answer grounded exclusively in the provided context")
    citations: list[str] = dspy.OutputField(desc="List of referenced email subject lines, thread IDs, or dates")
