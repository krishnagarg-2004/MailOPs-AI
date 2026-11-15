"""
Prometheus Metrics & Operational Telemetry Collector for MailOps AI.
Collects and formats application metrics in Prometheus text exposition format.
"""

from datetime import datetime, timezone
import time
from typing import Any
from backend.app.core.events import event_bus
from backend.app.core.worker_queue import worker_queue


class PrometheusMetricsCollector:
    """Collects system health, queue depth, SSE subscribers, and inference counts."""

    _start_time: float = time.time()
    _total_http_requests: int = 0
    _total_ai_inferences: int = 0
    _total_webhooks_received: int = 0

    @classmethod
    def record_http_request(cls):
        cls._total_http_requests += 1

    @classmethod
    def record_ai_inference(cls):
        cls._total_ai_inferences += 1

    @classmethod
    def record_webhook(cls):
        cls._total_webhooks_received += 1

    @classmethod
    def generate_metrics_text(cls) -> str:
        """Generates Prometheus-standard plaintext exposition."""
        uptime_seconds = time.time() - cls._start_time
        worker_stats = worker_queue.get_stats()
        active_sse_users = len(event_bus._subscribers)

        lines = [
            "# HELP mailops_uptime_seconds Total application uptime in seconds.",
            "# TYPE mailops_uptime_seconds gauge",
            f"mailops_uptime_seconds {uptime_seconds:.2f}",
            "",
            "# HELP mailops_http_requests_total Total HTTP requests served.",
            "# TYPE mailops_http_requests_total counter",
            f"mailops_http_requests_total {cls._total_http_requests}",
            "",
            "# HELP mailops_ai_inferences_total Total AI extractions and reply drafts generated.",
            "# TYPE mailops_ai_inferences_total counter",
            f"mailops_ai_inferences_total {cls._total_ai_inferences}",
            "",
            "# HELP mailops_webhooks_received_total Total Gmail Pub/Sub push webhooks received.",
            "# TYPE mailops_webhooks_received_total counter",
            f"mailops_webhooks_received_total {cls._total_webhooks_received}",
            "",
            "# HELP mailops_worker_queue_depth Pending background jobs in worker queue.",
            "# TYPE mailops_worker_queue_depth gauge",
            f"mailops_worker_queue_depth {worker_stats['queue_depth']}",
            "",
            "# HELP mailops_worker_completed_jobs_total Successfully completed background jobs.",
            "# TYPE mailops_worker_completed_jobs_total counter",
            f"mailops_worker_completed_jobs_total {worker_stats['completed_jobs']}",
            "",
            "# HELP mailops_worker_dead_letter_total Failed jobs in dead-letter queue.",
            "# TYPE mailops_worker_dead_letter_total counter",
            f"mailops_worker_dead_letter_total {worker_stats['dead_letter_jobs']}",
            "",
            "# HELP mailops_sse_active_users Number of active SSE event stream connections.",
            "# TYPE mailops_sse_active_users gauge",
            f"mailops_sse_active_users {active_sse_users}",
            "",
        ]
        return "\n".join(lines)
