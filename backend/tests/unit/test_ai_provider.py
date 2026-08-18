import pytest
from backend.app.ai.provider import MockAIProvider
from backend.app.schemas.ai import IntentEnum, PriorityEnum


@pytest.mark.asyncio
async def test_mock_ai_provider_invoice_extraction():
    provider = MockAIProvider()
    subject = "Vendor Invoice #9921 Payment Due"
    body = "Hi, please pay invoice #9921 of $4,500 due on 2026-08-30."
    sender = "billing@vendor.com"

    result = await provider.extract_email_intelligence(subject, body, sender)

    assert result.intent == IntentEnum.FINANCIAL_INVOICE
    assert result.priority == PriorityEnum.HIGH
    assert len(result.actions) > 0
    assert "pay invoice" in result.actions[0].evidence_snippet.lower()


@pytest.mark.asyncio
async def test_mock_ai_provider_urgent_work_request():
    provider = MockAIProvider()
    subject = "URGENT: Please submit status update"
    body = "Team, please review and submit the project deliverable due by 2026-08-25."
    sender = "manager@company.com"

    result = await provider.extract_email_intelligence(subject, body, sender)

    assert result.intent == IntentEnum.URGENT_ACTION
    assert result.priority == PriorityEnum.HIGH
    assert len(result.actions) > 0
    assert result.actions[0].due_date == "2026-08-25"
