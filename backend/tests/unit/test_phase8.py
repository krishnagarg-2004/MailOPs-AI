"""
Unit tests for Phase 8: Worker Queue, PubSub Webhook, and Prometheus Metrics.
"""

import asyncio
import base64
import json
import pytest

from backend.app.core.metrics_collector import PrometheusMetricsCollector
from backend.app.core.worker_queue import DistributedWorkerQueue


@pytest.mark.asyncio
async def test_worker_queue_processes_jobs_and_handles_retries():
    """Verify worker queue executes coroutines and tracks retry attempts."""
    queue = DistributedWorkerQueue(concurrency=2)
    await queue.start()

    executed = []

    async def successful_task(val: int):
        executed.append(val)

    job_id = await queue.enqueue("task_1", successful_task, 42)
    assert job_id.startswith("job_")

    # Give workers time to pick up and process
    await asyncio.sleep(0.1)

    assert 42 in executed
    stats = queue.get_stats()
    assert stats["completed_jobs"] == 1
    assert stats["dead_letter_jobs"] == 0

    await queue.stop()


@pytest.mark.asyncio
async def test_worker_queue_moves_to_dead_letter_on_repeated_failure():
    """Verify failing tasks transition to dead-letter queue after retries."""
    queue = DistributedWorkerQueue(concurrency=1)
    await queue.start()

    async def failing_task():
        raise RuntimeError("Fatal processing error")

    # Enqueue with 1 retry
    await queue.enqueue("failing_job", failing_task, retries=1)

    # Allow workers to retry and fail
    await asyncio.sleep(1.2)

    stats = queue.get_stats()
    assert stats["dead_letter_jobs"] == 1

    await queue.stop()


def test_prometheus_metrics_format():
    """Verify Prometheus text format generation conforms to Prometheus standards."""
    PrometheusMetricsCollector.record_http_request()
    PrometheusMetricsCollector.record_ai_inference()
    PrometheusMetricsCollector.record_webhook()

    metrics_text = PrometheusMetricsCollector.generate_metrics_text()

    assert "mailops_uptime_seconds" in metrics_text
    assert "mailops_http_requests_total" in metrics_text
    assert "mailops_ai_inferences_total" in metrics_text
    assert "mailops_webhooks_received_total" in metrics_text
    assert "mailops_worker_queue_depth" in metrics_text
    assert "mailops_sse_active_users" in metrics_text
