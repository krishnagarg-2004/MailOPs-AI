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

        # Scenario 1: Invoice / Billing
        if "invoice" in clean_subject or "payment" in clean_body_lower or "invoice" in clean_body_lower:
            intent = IntentEnum.FINANCIAL_INVOICE
            priority = PriorityEnum.HIGH
            sentiment = SentimentEnum.NEUTRAL
            rationale = "The message requests invoice processing and payment."
            
            # Find verbatim snippet for evidence
            for line in clean_body.splitlines():
                if "pay" in line.lower() or "due" in line.lower() or "invoice" in line.lower():
                    snippet = line.strip()
                    if snippet:
                        actions.append(
                            ExtractedActionSchema(
                                description="Process invoice payment",
                                assignee=sender,
                                due_date="2026-08-30",
                                priority=PriorityEnum.HIGH,
                                confidence=0.95,
                                evidence_snippet=snippet,
                            )
                        )
                        break

        # Scenario 2: Contract / Legal
        elif "contract" in clean_subject or "agreement" in clean_body_lower or "clause" in clean_body_lower:
            intent = IntentEnum.CONTRACT_LEGAL
            priority = PriorityEnum.HIGH
            sentiment = SentimentEnum.NEUTRAL
            rationale = "The message involves contract and legal agreement review."

            for line in clean_body.splitlines():
                if "contract" in line.lower() or "agreement" in line.lower() or "sign" in line.lower() or "review" in line.lower():
                    snippet = line.strip()
                    if snippet:
                        actions.append(
                            ExtractedActionSchema(
                                description="Review and process contract clauses",
                                assignee=sender,
                                due_date="2026-09-01",
                                priority=PriorityEnum.HIGH,
                                confidence=0.92,
                                evidence_snippet=snippet,
                            )
                        )
                        break

        # Scenario 3: Urgent Work Request / Action Item
        elif "urgent" in clean_subject or "please review" in clean_body_lower or "submit" in clean_body_lower:
            intent = IntentEnum.URGENT_ACTION
            priority = PriorityEnum.HIGH
            sentiment = SentimentEnum.NEGATIVE if "delay" in clean_body_lower else SentimentEnum.NEUTRAL
            rationale = "The message requests immediate review and action."

            for line in clean_body.splitlines():
                if "please" in line.lower() or "submit" in line.lower() or "review" in line.lower() or "due" in line.lower():
                    snippet = line.strip()
                    if snippet:
                        actions.append(
                            ExtractedActionSchema(
                                description="Review and submit requested deliverables",
                                assignee="Team Lead",
                                due_date="2026-08-25",
                                priority=PriorityEnum.HIGH,
                                confidence=0.9,
                                evidence_snippet=snippet,
                            )
                        )
                        break

        # Scenario 4: Status Update / Retrospective
        elif "status" in clean_subject or "retrospective" in clean_body_lower or "notes" in clean_body_lower:
            intent = IntentEnum.STATUS_UPDATE
            priority = PriorityEnum.LOW
            sentiment = SentimentEnum.POSITIVE if "great" in clean_body_lower else SentimentEnum.NEUTRAL
            rationale = "The message presents project status updates and retrospective notes."



        # Default fallback extraction if no actions were dynamically added
        if not actions and clean_body.strip():
            # Pick first non-empty line as evidence
            first_line = ""
            for line in clean_body.splitlines():
                if line.strip():
                    first_line = line.strip()
                    break
            if first_line:
                actions.append(
                    ExtractedActionSchema(
                        description="Follow up on email communication",
                        assignee=sender,
                        due_date=None,
                        priority=PriorityEnum.MEDIUM,
                        confidence=0.85,
                        evidence_snippet=first_line,
                    )
                )

        return EmailExtractionResult(
            summary=f"Analysis of email from {sender or 'unknown'} regarding '{subject or 'No Subject'}'",
            intent=intent,
            priority=priority,
            sentiment=sentiment,
            confidence_score=0.92,
            rationale=rationale,
            actions=actions,
            decisions=decisions,
            risks=risks,
        )


def get_ai_provider() -> AIProvider:
    """Factory function returning configured AI provider instance."""
    provider_type = settings.AI_PROVIDER_TYPE.lower()
    if provider_type == "gemini" and settings.GEMINI_API_KEY:
        return GeminiProvider()
    return MockAIProvider()
