"""
PII and Secret Sanitization Guardrail for MailOps AI.
Redacts API keys, credentials, credit card numbers, and SSNs before sending email data to LLMs or vector databases.
"""

import re
from typing import NamedTuple


class SanitizedResult(NamedTuple):
    sanitized_text: str
    redacted_count: int
    detected_types: list[str]


# Precompiled regular expressions for enterprise secrets and PII patterns
_PATTERNS: list[tuple[str, re.Pattern]] = [
    # API Keys / Tokens (OpenAI, Gemini, AWS, Generic Bearer)
    ("API_KEY", re.compile(r"(?i)\b(sk-[a-zA-Z0-9_-]{20,}|AIza[0-9A-Za-z_-]{35}|AKIA[0-9A-Z]{16})\b")),
    ("BEARER_TOKEN", re.compile(r"(?i)\b(bearer\s+[a-zA-Z0-9_\-\.]{24,})\b")),
    
    # Credit Card Numbers (Visa, Mastercard, Amex, Discover with dashes/spaces)
    ("CREDIT_CARD", re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b|\b\d{4}[ -]?\d{6}[ -]?\d{5}\b")),
    
    # US Social Security Numbers (SSN: XXX-XX-XXXX)
    ("SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    
    # Passwords or secrets in plaintext assignment
    ("SECRET_ASSIGNMENT", re.compile(r"(?i)\b(password|secret|passcode|token)\s*[:=]\s*(?:'[^']*'|\"[^\"]*\"|[^\s,;]+)")),
]


class PIIGuardrail:
    """Enterprise privacy and confidential information redaction guardrail."""

    @classmethod
    def sanitize(cls, text: str | None) -> SanitizedResult:
        """
        Scans and redacts sensitive PII and secrets, returning sanitized text
        and detection metadata.
        """
        if not text:
            return SanitizedResult(sanitized_text="", redacted_count=0, detected_types=[])

        sanitized = text
        redacted_count = 0
        detected_types: set[str] = set()

        for type_name, pattern in _PATTERNS:
            def replacer(match: re.Match) -> str:
                nonlocal redacted_count
                redacted_count += 1
                detected_types.add(type_name)
                # Keep parameter name if it was a secret assignment like password=XXXX
                if type_name == "SECRET_ASSIGNMENT":
                    return f"{match.group(1)}=[REDACTED_SECRET]"
                return f"[REDACTED_{type_name}]"

            sanitized = pattern.sub(replacer, sanitized)

        return SanitizedResult(
            sanitized_text=sanitized,
            redacted_count=redacted_count,
            detected_types=sorted(list(detected_types)),
        )
