"""
Gmail Push Notifications & Google Cloud Pub/Sub Webhook Handler for MailOps AI.
Receives real-time push notifications from Google Cloud Pub/Sub when new emails arrive,
triggering asynchronous background ingestion and AI analysis.
"""

import base64
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.events import event_bus
from backend.app.core.metrics_collector import PrometheusMetricsCollector
from backend.app.core.worker_queue import worker_queue
from backend.app.db.session import SessionLocal, get_db
from backend.app.models.oauth import OAuthAccount
from backend.app.models.user import User
from backend.app.services.gmail_sync_service import GmailSyncService

logger = logging.getLogger("mailops.webhook")

router = APIRouter(prefix="/webhooks", tags=["Webhooks & Ingestion"])


class PubSubMessagePayload(BaseModel):
    message: dict
    subscription: str | None = None


async def _async_webhook_sync_task(user_email: str):
    """Worker job triggered by webhook notification."""
    db = SessionLocal()
    try:
        user = db.execute(select(User).where(User.email == user_email)).scalar_one_or_none()
        if user:
            logger.info(f"Executing real-time webhook sync for user: {user.email}")
            service = GmailSyncService()
            await service.execute_sync(db, user)
            await event_bus.publish(
                user.id,
                "realtime_mail_received",
                {"message": "New inbound email arrived and was analyzed in real-time."},
            )
        else:
            logger.warning(f"Webhook user {user_email} not found in database.")
    except Exception as exc:
        logger.error(f"Error during webhook-triggered sync: {exc}")
    finally:
        db.close()


@router.post("/gmail", status_code=status.HTTP_200_OK)
async def gmail_pubsub_webhook(
    request: Request,
    payload: PubSubMessagePayload,
):
    """
    Receives Google Cloud Pub/Sub push notification for Gmail watch().
    Decodes the base64 PubSub payload and enqueues a background sync job.
    """
    PrometheusMetricsCollector.record_webhook()

    msg = payload.message
    if not msg or "data" not in msg:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing 'data' field in Pub/Sub message.",
        )

    try:
        # Base64 decode Pub/Sub data payload: {"emailAddress": "user@example.com", "historyId": "123456"}
        decoded_bytes = base64.b64decode(msg["data"])
        notification_data = json.loads(decoded_bytes.decode("utf-8"))
        user_email = notification_data.get("emailAddress")

        if not user_email:
            logger.warning("PubSub notification missing emailAddress.")
            return {"status": "ignored", "reason": "no emailAddress"}

        logger.info(f"Received Gmail push notification for: {user_email} (historyId={notification_data.get('historyId')})")

        # Enqueue to background worker queue
        job_id = await worker_queue.enqueue(
            f"pubsub_sync_{user_email}",
            _async_webhook_sync_task,
            user_email,
        )

        return {
            "status": "enqueued",
            "job_id": job_id,
            "emailAddress": user_email,
        }

    except Exception as exc:
        logger.error(f"Failed to process Pub/Sub message: {exc}")
        return {"status": "error", "detail": str(exc)}


@router.get("/metrics")
async def prometheus_metrics():
    """Prometheus exposition endpoint for system observability."""
    metrics_text = PrometheusMetricsCollector.generate_metrics_text()
    return Response(content=metrics_text, media_type="text/plain; version=0.0.4; charset=utf-8")
