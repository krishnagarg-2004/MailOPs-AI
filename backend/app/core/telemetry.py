"""
LLM Telemetry and Token Consumption Tracker for MailOps AI.
Tracks estimated token usage, latency, and cost per AI request for enterprise observability.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import logging
from typing import Any

logger = logging.getLogger("mailops.telemetry")

# Approximate Gemini 2.5 Flash pricing per 1M tokens (USD)
INPUT_TOKEN_COST_PER_MILLION = 0.075
OUTPUT_TOKEN_COST_PER_MILLION = 0.30


@dataclass
class LLMMetrics:
    model_name: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: float
    estimated_cost_usd: float
    timestamp: str


class LLMObservability:
    """Enterprise observability logger for LLM invocations."""

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Heuristic calculation: ~4 characters per token."""
        return max(1, len(text) // 4) if text else 0

    @classmethod
    def track_invocation(
        cls,
        model_name: str,
        input_text: str,
        output_text: str,
        latency_ms: float,
        metadata: dict[str, Any] | None = None,
    ) -> LLMMetrics:
        """Computes token metrics, calculates cost, and logs structured telemetry."""
        p_tokens = cls.estimate_tokens(input_text)
        c_tokens = cls.estimate_tokens(output_text)
        total_tokens = p_tokens + c_tokens

        cost = (
            (p_tokens / 1_000_000) * INPUT_TOKEN_COST_PER_MILLION
            + (c_tokens / 1_000_000) * OUTPUT_TOKEN_COST_PER_MILLION
        )

        metrics = LLMMetrics(
            model_name=model_name,
            prompt_tokens=p_tokens,
            completion_tokens=c_tokens,
            total_tokens=total_tokens,
            latency_ms=round(latency_ms, 2),
            estimated_cost_usd=round(cost, 6),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        logger.info(
            f"LLM_TELEMETRY: model={metrics.model_name} total_tokens={metrics.total_tokens} "
            f"latency={metrics.latency_ms}ms cost=${metrics.estimated_cost_usd:.6f} "
            f"meta={metadata or {}}"
        )

        return metrics
