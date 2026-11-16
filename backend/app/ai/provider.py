import asyncio
import logging
from typing import Any, Protocol
from backend.app.ai.prompts import PROMPT_VERSION, SYSTEM_EXTRACTION_PROMPT, build_email_extraction_prompt
from backend.app.core.config import settings
from backend.app.schemas.ai import (
    EmailExtractionResult,
    ExtractedActionSchema,
    ExtractedDecisionSchema,
    ExtractedRiskSchema,
    IntentEnum,
    PriorityEnum,
    SentimentEnum,
)

logger = logging.getLogger(__name__)


class AIProvider(Protocol):
    """Abstract protocol for AI/LLM providers."""

    async def extract_email_intelligence(
        self,
        subject: str | None,
        body: str | None,
        sender: str | None,
        context: dict[str, Any] | None = None,
    ) -> EmailExtractionResult:
        ...

    async def generate_reply_draft(
        self,
        context_prompt: str,
        tone: str = "PROFESSIONAL",
        intent: str = "REPLY_RESPONSE",
    ) -> Any:  # Returns ReplyDraftResult
        ...

    @property
    def model_name(self) -> str:
        ...




class GeminiProvider:
    """Official Gemini API provider using google-genai SDK."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self._model = model or settings.GEMINI_MODEL

        # Deferred import of google-genai to allow execution when package is not active
        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
        except ImportError:
            logger.warning("google-genai library not installed. GeminiProvider will fail if invoked.")
            self.client = None

    @property
    def model_name(self) -> str:
        return self._model

    async def extract_email_intelligence(
        self,
        subject: str | None,
        body: str | None,
        sender: str | None,
        context: dict[str, Any] | None = None,
    ) -> EmailExtractionResult:
        if not self.client:
            raise RuntimeError("google-genai client is not initialized. Please ensure google-genai is installed and GEMINI_API_KEY is configured.")

        prompt = build_email_extraction_prompt(subject, body, sender)
        
        # Exponential backoff retry loop for rate limits / transient API errors
        max_retries = settings.AI_MAX_RETRIES
        delay = 1.0
        last_exception = None

        for attempt in range(1, max_retries + 1):
            try:
                # Synchronous SDK call wrapped in asyncio.to_thread
                def _call_gemini():
                    from google.genai import types
                    config = types.GenerateContentConfig(
                        system_instruction=SYSTEM_EXTRACTION_PROMPT,
                        response_mime_type="application/json",
                        response_schema=EmailExtractionResult,
                        temperature=0.1,
                    )
                    response = self.client.models.generate_content(
                        model=self._model,
                        contents=prompt,
                        config=config,
                    )
                    return response.parsed or EmailExtractionResult.model_validate_json(response.text)

                result = await asyncio.to_thread(_call_gemini)
                if isinstance(result, EmailExtractionResult):
                    return result
                return EmailExtractionResult.model_validate(result)

            except Exception as exc:
                last_exception = exc
                logger.warning("Gemini API call failed (attempt %d/%d): %s", attempt, max_retries, exc)
                if attempt < max_retries:
                    await asyncio.sleep(delay)
                    delay *= 2.0

        raise RuntimeError(f"Gemini API extraction failed after {max_retries} retries: {last_exception}") from last_exception

    async def generate_reply_draft(
        self,
        context_prompt: str,
        tone: str = "PROFESSIONAL",
        intent: str = "REPLY_RESPONSE",
    ) -> Any:
        from backend.app.schemas.reply_draft import ReplyDraftResult
        if not self.client:
            raise RuntimeError("google-genai client is not initialized.")

        system_instruction = (
            f"You are an AI assistant for MailOps. Generate a context-aware email reply draft in tone '{tone}' "
            f"and intent '{intent}'. Structure output as JSON with fields: subject, body_text, recipient_email, rationale_and_provenance."
        )

        def _call():
            from google.genai import types
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=ReplyDraftResult,
                temperature=0.2,
            )
            resp = self.client.models.generate_content(
                model=self._model,
                contents=context_prompt,
                config=config,
            )
            return resp.parsed or ReplyDraftResult.model_validate_json(resp.text)

        result = await asyncio.to_thread(_call)
        if isinstance(result, ReplyDraftResult):
            return result
        return ReplyDraftResult.model_validate(result)


class MockAIProvider:
    """Deterministic offline AI provider for testing, offline dev, and CI/CD."""

    def __init__(self, model_name: str = "mock-gemini-2.5"):
        self._model_name = model_name

    @property
    def model_name(self) -> str:
        return self._model_name

    async def generate_reply_draft(
        self,
        context_prompt: str,
        tone: str = "PROFESSIONAL",
        intent: str = "REPLY_RESPONSE",
    ) -> Any:
        from backend.app.schemas.reply_draft import ReplyDraftResult

        body_intro = {
            "PROFESSIONAL": "Thank you for reaching out regarding this matter.",
            "CONCISE": "Acknowledged.",
            "URGENT": "I am addressing this request immediately.",
            "EMPATHETIC": "Thank you for your update; I understand the situation.",
        }.get(tone.upper(), "Thank you for your message.")

        return ReplyDraftResult(
            subject="Re: Operational Response",
            body_text=f"{body_intro}\n\nWe have reviewed the context and confirmed all action items.\n\nBest regards,\nMailOps AI Assistant",
            recipient_email="sender@example.com",
            rationale_and_provenance=[
                {
                    "source_type": "EMAIL_THREAD",
                    "source_id": "mock_thread_id",
                    "description": "Formulated response based on preceding email thread context.",
                }
            ],
        )


    async def extract_email_intelligence(
        self,
        subject: str | None,
        body: str | None,
        sender: str | None,
        context: dict[str, Any] | None = None,
    ) -> EmailExtractionResult:
        clean_subject = (subject or "").lower()
        clean_body = body or ""
        clean_body_lower = clean_body.lower()

        actions: list[ExtractedActionSchema] = []
        decisions: list[ExtractedDecisionSchema] = []
        risks: list[ExtractedRiskSchema] = []

        intent = IntentEnum.INFORMATIONAL
        priority = PriorityEnum.MEDIUM
        sentiment = SentimentEnum.NEUTRAL
        rationale = "The message provides operational communication."

        # Clean sender and subject
        clean_sender = sender.split("<")[0].strip() if sender else "External Contact"
        if not clean_sender:
            clean_sender = sender or "External Contact"

        # Extract informative body lines (ignoring greetings, footers, signatures)
        raw_lines = [line.strip() for line in clean_body.splitlines() if line.strip()]
        meaningful_lines = [
            line for line in raw_lines
            if not any(line.lower().startswith(prefix) for prefix in [
                "hi", "hello", "dear", "thanks", "thank you", "best", "regards", "cheers",
                "sent from", "view on github", "subscribed to", "unsubscribe"
            ])
            and len(line) > 15
        ]

        # Scenario 1: CI/CD / GitHub / DevOps Pipeline Failure
        if "fail" in clean_subject or "ci/cd" in clean_subject or "pipeline" in clean_subject or "github" in clean_body_lower:
            intent = IntentEnum.URGENT_ACTION
            priority = PriorityEnum.HIGH
            sentiment = SentimentEnum.NEGATIVE
            rationale = "Automated pipeline alert flags build or test suite failures requiring immediate engineering triage."

            failure_detail = meaningful_lines[0] if meaningful_lines else "Workflow run failed during execution."
            summary = (
                f"Automated alert regarding '{subject or 'CI/CD Pipeline'}'. "
                f"{failure_detail} "
                "Engineering intervention is required to inspect execution logs, address breaking test failures, and restore build stability."
            )

            # Find evidence snippet
            evidence_snippet = raw_lines[0] if raw_lines else "CI/CD Pipeline workflow run failed"
            for line in raw_lines:
                if any(w in line.lower() for w in ["fail", "error", "failed", "broken"]):
                    evidence_snippet = line
                    break

            actions.append(
                ExtractedActionSchema(
                    description=f"Triage and resolve CI/CD pipeline failure for {subject or 'project'}",
                    assignee=clean_sender,
                    due_date=None,
                    priority=PriorityEnum.HIGH,
                    confidence=0.95,
                    evidence_snippet=evidence_snippet,
                )
            )

            risks.append(
                ExtractedRiskSchema(
                    description="Continuous deployment blocked by failing tests or lint checks on branch",
                    severity=PriorityEnum.HIGH,
                    mitigation_suggestion="Check recent commits and local test suite logs to isolate broken dependencies.",
                    confidence=0.92,
                    evidence_snippet=evidence_snippet,
                )
            )

        # Scenario 2: Invoice / Billing
        elif "invoice" in clean_subject or "payment" in clean_body_lower or "invoice" in clean_body_lower:
            intent = IntentEnum.FINANCIAL_INVOICE
            priority = PriorityEnum.HIGH
            sentiment = SentimentEnum.NEUTRAL
            rationale = "The message requests invoice processing, vendor account verification, and payment settlement."

            key_detail = meaningful_lines[0] if meaningful_lines else "Vendor requested invoice settlement."
            summary = (
                f"Financial billing request from {clean_sender} regarding '{subject or 'Invoice'}'. "
                f"{key_detail} "
                "Review document line items against procurement purchase orders and submit for accounting approval."
            )

            evidence_snippet = "Invoice payment due"
            for line in clean_body.splitlines():
                if any(k in line.lower() for k in ["pay", "due", "invoice", "total", "$"]):
                    evidence_snippet = line.strip()
                    break

            actions.append(
                ExtractedActionSchema(
                    description="Verify line items and authorize invoice payment",
                    assignee=clean_sender,
                    due_date="2026-08-30",
                    priority=PriorityEnum.HIGH,
                    confidence=0.95,
                    evidence_snippet=evidence_snippet,
                )
            )

        # Scenario 3: Contract / Legal
        elif "contract" in clean_subject or "agreement" in clean_body_lower or "clause" in clean_body_lower:
            intent = IntentEnum.CONTRACT_LEGAL
            priority = PriorityEnum.HIGH
            sentiment = SentimentEnum.NEUTRAL
            rationale = "The communication involves legal agreements, liability clauses, or contractual compliance terms."

            key_detail = meaningful_lines[0] if meaningful_lines else "Agreement terms submitted for review."
            summary = (
                f"Legal communication from {clean_sender} concerning '{subject or 'Contract Agreement'}'. "
                f"{key_detail} "
                "Requires legal counsel and executive review before signing."
            )

            evidence_snippet = "Contract terms review requested"
            for line in clean_body.splitlines():
                if any(k in line.lower() for k in ["contract", "agreement", "sign", "clause", "review"]):
                    evidence_snippet = line.strip()
                    break

            actions.append(
                ExtractedActionSchema(
                    description="Review contract clauses and verify indemnity terms",
                    assignee=clean_sender,
                    due_date="2026-09-01",
                    priority=PriorityEnum.HIGH,
                    confidence=0.92,
                    evidence_snippet=evidence_snippet,
                )
            )

        # Scenario 4: Urgent Work Request / Action Item
        elif "urgent" in clean_subject or "please review" in clean_body_lower or "submit" in clean_body_lower or "action" in clean_subject:
            intent = IntentEnum.URGENT_ACTION
            priority = PriorityEnum.HIGH
            sentiment = SentimentEnum.NEGATIVE if "delay" in clean_body_lower else SentimentEnum.NEUTRAL
            rationale = "The message requests immediate deliverable review, issue resolution, or executive feedback."

            key_detail = meaningful_lines[0] if meaningful_lines else "Immediate response and deliverables requested."
            summary = (
                f"Urgent operational request from {clean_sender} regarding '{subject or 'Action Required'}'. "
                f"{key_detail} "
                "Team action is requested to meet the stated timeline."
            )

            evidence_snippet = "Deliverable review requested"
            for line in clean_body.splitlines():
                if any(k in line.lower() for k in ["please", "submit", "review", "due", "urgent", "asap"]):
                    evidence_snippet = line.strip()
                    break

            actions.append(
                ExtractedActionSchema(
                    description="Review and complete requested deliverables",
                    assignee=clean_sender,
                    due_date="2026-08-25",
                    priority=PriorityEnum.HIGH,
                    confidence=0.90,
                    evidence_snippet=evidence_snippet,
                )
            )

        # Scenario 5: General Correspondence / Informational
        else:
            intent = IntentEnum.INFORMATIONAL
            priority = PriorityEnum.MEDIUM
            sentiment = SentimentEnum.POSITIVE if any(w in clean_body_lower for w in ["great", "good", "thank", "pleasure"]) else SentimentEnum.NEUTRAL
            rationale = "The message provides routine project communication, status updates, or notifications."

            if meaningful_lines:
                body_excerpt = " ".join(meaningful_lines[:2])
                if len(body_excerpt) > 220:
                    body_excerpt = body_excerpt[:217] + "..."
                summary = (
                    f"Message from {clean_sender} regarding '{subject or 'Correspondence'}'. "
                    f"{body_excerpt} "
                    "Follow up as appropriate to acknowledge or address the points raised."
                )
            else:
                summary = (
                    f"Routine correspondence from {clean_sender} regarding '{subject or 'No Subject'}'. "
                    "Message contains operational details for reference and logging."
                )

        # Default fallback extraction if no actions were dynamically added
        if not actions and clean_body.strip():
            first_line = meaningful_lines[0] if meaningful_lines else (raw_lines[0] if raw_lines else "Follow up on email")
            actions.append(
                ExtractedActionSchema(
                    description=f"Follow up on '{subject or 'communication'}'",
                    assignee=clean_sender,
                    due_date=None,
                    priority=PriorityEnum.MEDIUM,
                    confidence=0.88,
                    evidence_snippet=first_line,
                )
            )

        return EmailExtractionResult(
            summary=summary,
            intent=intent,
            priority=priority,
            sentiment=sentiment,
            confidence_score=0.94,
            rationale=rationale,
            actions=actions,
            decisions=decisions,
            risks=risks,
        )


def get_ai_provider() -> AIProvider:
    """Factory function returning configured AI provider instance."""
    provider_type = settings.AI_PROVIDER_TYPE.lower()
    if (
        provider_type == "gemini"
        and settings.GEMINI_API_KEY
        and not settings.GEMINI_API_KEY.startswith("your_")
    ):
        return GeminiProvider()
    return MockAIProvider()
