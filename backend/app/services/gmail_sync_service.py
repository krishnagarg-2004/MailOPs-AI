import asyncio
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any
import uuid

import logging
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.events import event_bus
from backend.app.integrations.gmail import GmailAPIError, GmailClient
from backend.app.models.email_message import EmailMessage
from backend.app.models.oauth import OAuthAccount
from backend.app.models.user import User
from backend.app.repositories.gmail_repository import GmailRepository
from backend.app.utils.mime_parser import MIMEParser

SUPPORTED_DOWNLOAD_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".docx"}

logger = logging.getLogger(__name__)


class GmailSyncService:
    """Independent domain service orchestrating Gmail mailbox synchronization."""

    def __init__(self, client: GmailClient | None = None):
        self.client = client or GmailClient()

    async def execute_sync(self, db: Session, user: User) -> dict[str, Any]:
        """Main synchronization entrypoint.

        Routes to incremental History API sync when a valid last_history_id
        exists, otherwise performs a baseline initial synchronization.
        """
        try:
            # 1. Fetch user's Google OAuth Account
            oauth_account = (
                db.query(OAuthAccount)
                .filter(OAuthAccount.user_id == user.id, OAuthAccount.provider == "google")
                .first()
            )
            if not oauth_account:
                GmailRepository.update_sync_state(
                    db, user.id, sync_status="FAILED", error_message="No Google OAuth account connected."
                )
                raise ValueError("No Google OAuth account connected.")

            # 2. Get valid access token (refreshes if expired)
            access_token = self.client.get_valid_access_token(db, oauth_account)
            sync_state = GmailRepository.get_or_create_sync_state(db, user.id)

            # 3. Mark sync_status = SYNCING
            GmailRepository.update_sync_state(db, user.id, sync_status="SYNCING")
            await event_bus.publish(
                user.id,
                "sync_started",
                {"status": "SYNCING", "message": "Mailbox synchronization started."},
            )

            # Check for demo persona bypass - avoid unauthorized calls to Google REST API
            if self._is_demo_account(user, access_token):
                return await self._sync_demo_messages(db, user)

            if sync_state.last_history_id:
                # Attempt incremental History API sync
                try:
                    return await self._sync_history_incremental(
                        db, user, oauth_account, access_token, sync_state.last_history_id
                    )
                except GmailAPIError as e:
                    if e.status_code == 404 or "historyIdNotFound" in e.message:
                        # Expired or invalid historyId → fallback to full initial sync
                        GmailRepository.update_sync_state(db, user.id, last_history_id=None)
                        return await self._sync_initial_baseline(
                            db, user, oauth_account, access_token
                        )
                    raise
            else:
                # Perform baseline initial sync
                return await self._sync_initial_baseline(db, user, oauth_account, access_token)
        except Exception as e:
            GmailRepository.update_sync_state(
                db, user.id, sync_status="FAILED", error_message=str(e)
            )
            await event_bus.publish(
                user.id,
                "sync_completed",
                {"status": "FAILED", "error": str(e)},
            )
            raise

    async def sync_older_messages(
        self,
        db: Session,
        user: User,
        count: int = 50,
    ) -> dict[str, Any]:
        """Fetch and persist older historical messages prior to the earliest stored message."""
        try:
            # 1. Fetch user's Google OAuth Account
            oauth_account = (
                db.query(OAuthAccount)
                .filter(OAuthAccount.user_id == user.id, OAuthAccount.provider == "google")
                .first()
            )
            if not oauth_account:
                GmailRepository.update_sync_state(
                    db, user.id, sync_status="FAILED", error_message="No Google OAuth account connected."
                )
                raise ValueError("No Google OAuth account connected.")

            # 2. Get valid access token
            access_token = self.client.get_valid_access_token(db, oauth_account)
            sync_state = GmailRepository.get_or_create_sync_state(db, user.id)

            # 3. Mark sync_status = SYNCING
            GmailRepository.update_sync_state(db, user.id, sync_status="SYNCING")
            await event_bus.publish(
                user.id,
                "sync_started",
                {"status": "SYNCING", "message": f"Fetching up to {count} older emails..."},
            )

            # Check for demo persona bypass - synthesize older emails without Google API calls
            if self._is_demo_account(user, access_token):
                return await self._sync_older_demo_messages(db, user, count=count)

            # 4. Find the oldest message currently stored in DB for this user
            oldest_msg = (
                db.query(EmailMessage)
                .filter(EmailMessage.user_id == user.id)
                .filter(EmailMessage.received_at.isnot(None))
                .order_by(EmailMessage.received_at.asc())
                .first()
            )

            q_param = None
            if oldest_msg and oldest_msg.received_at:
                epoch_sec = int(oldest_msg.received_at.timestamp())
                # Add 1s margin to capture boundary and filter duplicates via ID check
                q_param = f"before:{epoch_sec + 1}"

            # Preload known message IDs for fast deduplication check
            known_ids = set(
                m[0]
                for m in db.query(EmailMessage.gmail_message_id)
                .filter(EmailMessage.user_id == user.id)
                .all()
            )

            messages_processed = 0
            failed_count = 0
            page_token = None

            while messages_processed < count:
                batch_size = min(50, count - messages_processed)
                try:
                    list_resp = await self.client.list_messages(
                        access_token,
                        page_token=page_token,
                        q=q_param,
                        max_results=batch_size,
                    )
                except Exception as batch_exc:
                    logger.error("Sync older: list_messages failed: %s", batch_exc)
                    if messages_processed > 0:
                        break
                    raise

                msg_summaries = list_resp.get("messages", [])
                if not msg_summaries:
                    break

                for summary in msg_summaries:
                    msg_id = summary["id"]
                    if msg_id in known_ids:
                        continue

                    try:
                        await self._fetch_and_persist_message(db, user, access_token, msg_id)
                        known_ids.add(msg_id)
                        messages_processed += 1

                        if messages_processed % 5 == 0:
                            GmailRepository.update_sync_state(
                                db,
                                user.id,
                                sync_status="SYNCING",
                                synced_message_count=len(known_ids),
                            )

                        await event_bus.publish(
                            user.id,
                            "sync_progress",
                            {
                                "processed": messages_processed,
                                "limit": count,
                                "message_id": msg_id,
                            },
                        )
                        await asyncio.sleep(0.02)
                    except Exception as exc:
                        logger.warning(
                            "Sync older: skipping message_id=%s user_id=%s reason=%s",
                            msg_id,
                            user.id,
                            type(exc).__name__,
                        )
                        failed_count += 1

                    if messages_processed >= count:
                        break

                page_token = list_resp.get("nextPageToken")
                if not page_token:
                    break

            total_synced = (
                db.query(EmailMessage)
                .filter(EmailMessage.user_id == user.id)
                .count()
            )

            partial_error = (
                f"Skipped {failed_count} older message(s) due to fetch errors."
                if failed_count
                else None
            )

            GmailRepository.update_sync_state(
                db,
                user.id,
                sync_status="COMPLETED",
                last_history_id=sync_state.last_history_id,
                synced_message_count=total_synced,
                error_message=partial_error,
            )

            await event_bus.publish(
                user.id,
                "sync_completed",
                {
                    "status": "COMPLETED",
                    "synced_count": messages_processed,
                    "total_messages": total_synced,
                    "failed_count": failed_count,
                },
            )

            return {
                "status": "COMPLETED",
                "type": "OLDER_MESSAGES",
                "messages_synced": messages_processed,
                "total_messages": total_synced,
                "failed_count": failed_count,
            }

        except Exception as e:
            GmailRepository.update_sync_state(
                db, user.id, sync_status="FAILED", error_message=str(e)
            )
            await event_bus.publish(
                user.id,
                "sync_completed",
                {"status": "FAILED", "error": str(e)},
            )
            raise

    @staticmethod
    def _is_demo_account(user: User, access_token: str | None) -> bool:
        """Determine whether the user belongs to the demo persona requiring mock synthesis."""
        if user.email and (
            user.email == "alex.morgan@enterprise-mailops.io"
            or user.email.endswith("@enterprise-mailops.io")
        ):
            return True
        if access_token == "mock_access_token_demo":
            return True
        return False

    async def _sync_demo_messages(self, db: Session, user: User) -> dict[str, Any]:
        """Perform simulated synchronization for demo persona accounts without calling Google API."""
        existing_count = (
            db.query(EmailMessage).filter(EmailMessage.user_id == user.id).count()
        )
        if existing_count == 0:
            from backend.app.scripts.seed_demo_data import seed_demo_environment
            seed_demo_environment(db, target_user=user, include_embeddings=False)

        total_synced = (
            db.query(EmailMessage).filter(EmailMessage.user_id == user.id).count()
        )

        await event_bus.publish(
            user.id,
            "sync_progress",
            {"processed": total_synced, "limit": total_synced, "message_id": "demo_baseline"},
        )
        await asyncio.sleep(0.01)

        GmailRepository.update_sync_state(
            db,
            user.id,
            sync_status="COMPLETED",
            synced_message_count=total_synced,
            error_message=None,
        )

        await event_bus.publish(
            user.id,
            "sync_completed",
            {
                "status": "COMPLETED",
                "synced_count": total_synced,
                "total_messages": total_synced,
                "failed_count": 0,
            },
        )

        return {
            "status": "COMPLETED",
            "type": "DEMO_BASELINE",
            "messages_synced": total_synced,
            "total_messages": total_synced,
            "failed_count": 0,
        }

    async def _sync_older_demo_messages(
        self, db: Session, user: User, count: int = 50
    ) -> dict[str, Any]:
        """Synthesize batches of realistic older emails for demo persona pagination without calling Google API."""
        oldest_msg = (
            db.query(EmailMessage)
            .filter(EmailMessage.user_id == user.id)
            .filter(EmailMessage.received_at.isnot(None))
            .order_by(EmailMessage.received_at.asc())
            .first()
        )

        if oldest_msg and oldest_msg.received_at:
            base_time = oldest_msg.received_at - timedelta(hours=1)
        else:
            base_time = datetime.now(timezone.utc) - timedelta(days=7)

        # Enterprise topics catalog for realistic synthetic emails
        catalog = [
            (
                "Alert: Kubernetes node pool memory pressure in prod-us-east-1",
                "DevOps Monitoring <alerts@infra-mailops.internal>",
                "Kubernetes cluster prod-us-east-1 node pool 04 has exceeded 88% memory utilization threshold. Automated pod eviction initiated to safeguard core services.",
            ),
            (
                "Action Required: Quarterly IAM privilege audit for Q3",
                "Security & Compliance <infosec@enterprise-mailops.io>",
                "All team leads must verify principle of least privilege across production databases and cloud console roles before Friday. Report non-compliant accounts to sec-ops.",
            ),
            (
                "PostgreSQL read replica replication lag warning",
                "DBA Oncall <dba@infra-mailops.internal>",
                "Primary database to read replica pg-repl-02 replication lag exceeded 45 seconds during batch ETL processing. Failover standby remained synchronized.",
            ),
            (
                "Sprint 41 retrospective notes and action item matrix",
                "Marcus Vance <marcus.vance@enterprise-mailops.io>",
                "Attached is the sprint retrospective summary. Key priorities include resolving SSE reconnection stability, improving draft latency, and refining test coverage.",
            ),
            (
                "Vendor invoice reconciliation: Cloudflare Enterprise agreement",
                "Procurement Operations <procurement@enterprise-mailops.io>",
                "Please review the updated bandwidth overage tiering for Cloudflare Enterprise CDN contract renewal scheduled for end of month.",
            ),
            (
                "RFC: Deprecation schedule for Legacy REST API v1 endpoints",
                "Architecture Guild <arch-review@enterprise-mailops.io>",
                "The Architecture Guild proposes sunsetting v1 legacy endpoints by Q1 2027. Review the migration guide and submit comments on the RFC draft.",
            ),
            (
                "Customer escalation: Webhook delivery failure on partner checkout",
                "Support Escalations <support-tier3@enterprise-mailops.io>",
                "High-priority ticket #8942: Acme Corp reported intermittent 504 timeouts on webhook endpoints during peak transaction volume. Engineering investigation requested.",
            ),
            (
                "SOC 2 Type II audit readiness review: Evidence checklist",
                "GRC Lead <compliance@enterprise-mailops.io>",
                "External auditors from EY will begin sampling change management tickets next week. Ensure all production PRs have approved code reviews and CI status checks.",
            ),
            (
                "Frontend Core Web Vitals optimization report (LCP < 1.2s achieved)",
                "Sarah Chen <sarah.chen@enterprise-mailops.io>",
                "Bundle size optimizations and font preloading have reduced Largest Contentful Paint to 1.14s on desktop and 1.8s on mobile. Full metrics breakdown in dashboard.",
            ),
            (
                "Disaster Recovery tabletop simulation findings and next steps",
                "BCP Working Group <bcp-team@enterprise-mailops.io>",
                "Summary of regional failover drill executed yesterday: RTO was 14 minutes (target: < 30m), RPO was 0 transactions lost. Runbook updates committed.",
            ),
            (
                "TLS wildcard certificate auto-renewal succeeded (*.enterprise-mailops.io)",
                "CertBot Automation <sec-ops@enterprise-mailops.io>",
                "Let's Encrypt automated ACME renewal succeeded for primary domain certificates. New cert valid through 2027-02-15.",
            ),
            (
                "Release v2.8.0 deployment checklist and verification protocol",
                "Release Engineering <releases@enterprise-mailops.io>",
                "Version 2.8.0 release candidate has passed integration testing. Canary deployment to 10% traffic starts at 14:00 UTC. Monitor error budgets during rollout.",
            ),
            (
                "Customer satisfaction report: Enterprise Pilot Q3 feedback",
                "VP Customer Success <cs-leadership@enterprise-mailops.io>",
                "Net Promoter Score increased to +68 following the introduction of AI-assisted drafting and automated action graphs. Detailed customer quotes attached.",
            ),
            (
                "Cloud infrastructure monthly cost optimization analysis",
                "FinOps Team <finops@enterprise-mailops.io>",
                "Reserved instance utilization reached 92%, resulting in $14,200 monthly savings. Recommended downsizing idle staging RDS instances.",
            ),
            (
                "Security Advisory: Dependabot updates for critical dependencies",
                "SecOps Automation <sec-ops@enterprise-mailops.io>",
                "Automated PRs opened for high-severity CVEs in underlying cryptographic and network libraries. Merge required before staging deployment.",
            ),
        ]

        # Preload known message IDs
        known_ids = set(
            m[0]
            for m in db.query(EmailMessage.gmail_message_id)
            .filter(EmailMessage.user_id == user.id)
            .all()
        )

        messages_created = 0
        cat_len = len(catalog)

        for i in range(count):
            subject_base, sender, body = catalog[i % cat_len]
            batch_num = (i // cat_len) + 1
            subject = f"{subject_base} (Batch #{batch_num})" if batch_num > 1 else subject_base

            # Decrement timestamp so each message is older than the previous
            msg_time = base_time - timedelta(hours=2 * (i + 1), minutes=(i * 13) % 60)

            unique_thread_token = f"demo_th_older_{user.id.hex[:6]}_{i + 1}_{int(msg_time.timestamp())}"
            unique_msg_token = f"demo_msg_older_{user.id.hex[:6]}_{i + 1}_{int(msg_time.timestamp())}"

            if unique_msg_token in known_ids:
                continue

            snippet = body[:120] + "..." if len(body) > 120 else body

            thread = GmailRepository.upsert_thread(
                db,
                user_id=user.id,
                gmail_thread_id=unique_thread_token,
                snippet=snippet,
                history_id=1000000 - i,
                last_message_at=msg_time,
            )

            GmailRepository.upsert_message(
                db,
                user_id=user.id,
                thread_id=thread.id,
                gmail_message_id=unique_msg_token,
                gmail_thread_id=unique_thread_token,
                sender=sender,
                recipients=user.email or "alex.morgan@enterprise-mailops.io",
                subject=subject,
                snippet=snippet,
                body_plain=body,
                body_html=f"<p>{body}</p>",
                sent_at=msg_time,
                received_at=msg_time,
                labels=["INBOX", "DEMO_OLDER"],
                has_attachments=False,
                history_id=1000000 - i,
            )

            known_ids.add(unique_msg_token)
            messages_created += 1

            if messages_created % 5 == 0 or messages_created == count:
                GmailRepository.update_sync_state(
                    db,
                    user.id,
                    sync_status="SYNCING",
                    synced_message_count=len(known_ids),
                )
                await event_bus.publish(
                    user.id,
                    "sync_progress",
                    {
                        "processed": messages_created,
                        "limit": count,
                        "message_id": unique_msg_token,
                    },
                )
                await asyncio.sleep(0.01)

        total_synced = (
            db.query(EmailMessage).filter(EmailMessage.user_id == user.id).count()
        )

        GmailRepository.update_sync_state(
            db,
            user.id,
            sync_status="COMPLETED",
            synced_message_count=total_synced,
            error_message=None,
        )

        await event_bus.publish(
            user.id,
            "sync_completed",
            {
                "status": "COMPLETED",
                "synced_count": messages_created,
                "total_messages": total_synced,
                "failed_count": 0,
            },
        )

        return {
            "status": "COMPLETED",
            "type": "OLDER_MESSAGES",
            "messages_synced": messages_created,
            "total_messages": total_synced,
            "failed_count": 0,
        }

    async def _sync_initial_baseline(
        self,
        db: Session,
        user: User,
        oauth_account: OAuthAccount,
        access_token: str,
    ) -> dict[str, Any]:
        """Perform initial mailbox synchronization with baseline historyId capture.

        Captures baseline historyId BEFORE message ingestion to guarantee no
        lost updates from mail arriving during sync.

        FIX-SYNC-5: Per-message failures are logged and skipped without
        aborting the overall sync. The final status reflects partial failures
        if any messages could not be fetched.
        """
        # STEP 1: Baseline History ID Capture Invariant
        profile = await self.client.get_profile(access_token)
        baseline_history_id_str = profile.get("historyId")
        baseline_history_id = int(baseline_history_id_str) if baseline_history_id_str else None

        # STEP 2: List messages up to INITIAL_SYNC_LIMIT
        limit = settings.INITIAL_SYNC_LIMIT
        messages_processed = 0
        failed_count = 0
        page_token = None

        while messages_processed < limit:
            batch_size = min(50, limit - messages_processed)
            try:
                list_resp = await self.client.list_messages(
                    access_token, page_token=page_token, max_results=batch_size
                )
            except Exception as batch_exc:
                logger.error("Initial sync: list_messages failed: %s", batch_exc)
                if messages_processed > 0:
                    break
                raise

            msg_summaries = list_resp.get("messages", [])
            if not msg_summaries:
                break

            for summary in msg_summaries:
                msg_id = summary["id"]
                # FIX-SYNC-5: Isolate per-message failures — a single bad message
                # does not abort the entire sync.
                try:
                    await self._fetch_and_persist_message(db, user, access_token, msg_id)
                    messages_processed += 1
                    await event_bus.publish(
                        user.id,
                        "sync_progress",
                        {
                            "processed": messages_processed,
                            "limit": limit,
                            "message_id": msg_id,
                        },
                    )
                    # Pacing delay to avoid triggering Google per-second quota bursts
                    await asyncio.sleep(0.02)
                except Exception as exc:
                    logger.warning(
                        "Initial sync: skipping message_id=%s user_id=%s reason=%s",
                        msg_id,
                        user.id,
                        type(exc).__name__,
                    )
                    failed_count += 1
                if messages_processed >= limit:
                    break

            page_token = list_resp.get("nextPageToken")
            if not page_token:
                break

        # STEP 3: Complete sync and save baseline_history_id
        # Propagate partial failure note when some messages were skipped.
        partial_error = (
            f"Skipped {failed_count} message(s) due to fetch errors." if failed_count else None
        )

        GmailRepository.update_sync_state(
            db,
            user.id,
            sync_status="COMPLETED",
            last_history_id=baseline_history_id,
            synced_message_count=messages_processed,
            error_message=partial_error,
        )

        await event_bus.publish(
            user.id,
            "sync_completed",
            {
                "status": "COMPLETED",
                "synced_count": messages_processed,
                "failed_count": failed_count,
            },
        )

        return {
            "status": "COMPLETED",
            "type": "INITIAL_BASELINE",
            "messages_synced": messages_processed,
            "failed_count": failed_count,
            "last_history_id": baseline_history_id,
        }

    async def _sync_history_incremental(
        self,
        db: Session,
        user: User,
        oauth_account: OAuthAccount,
        access_token: str,
        start_history_id: int,
    ) -> dict[str, Any]:
        """Perform incremental History API synchronization starting from start_history_id.

        FIX-SYNC-4: Paginates through ALL History API pages until nextPageToken
        is absent. Without pagination, history events on pages after the first
        were silently dropped.

        FIX-SYNC-5: Per-message failures are logged and skipped without
        aborting the overall sync.
        """
        # FIX-SYNC-4: Paginate through all History API pages before processing events.
        history_records: list[dict] = []
        new_history_id = start_history_id
        page_token: str | None = None

        while True:
            history_resp = await self.client.list_history(
                access_token, start_history_id, page_token=page_token
            )
            page_records = history_resp.get("history", [])
            history_records.extend(page_records)

            history_id_str = history_resp.get("historyId")
            if history_id_str:
                new_history_id = int(history_id_str)

            page_token = history_resp.get("nextPageToken")
            if not page_token:
                break

        messages_added_count = 0
        messages_deleted_count = 0
        failed_message_ids: list[str] = []

        for record in history_records:
            # 1. Handle messagesAdded
            for add_event in record.get("messagesAdded", []):
                msg_id = add_event.get("message", {}).get("id")
                if msg_id:
                    # FIX-SYNC-5: Isolate per-message failures.
                    try:
                        await self._fetch_and_persist_message(db, user, access_token, msg_id)
                        messages_added_count += 1
                    except Exception as exc:
                        logger.warning(
                            "Incremental sync: failed message_id=%s user_id=%s reason=%s",
                            msg_id,
                            user.id,
                            type(exc).__name__,
                        )
                        failed_message_ids.append(msg_id)

            # 2. Handle labelsAdded / labelsRemoved
            for label_event in record.get("labelsAdded", []) + record.get("labelsRemoved", []):
                msg_info = label_event.get("message", {})
                msg_id = msg_info.get("id")
                labels = msg_info.get("labelIds", [])
                if msg_id and labels:
                    GmailRepository.update_message_labels(db, user.id, msg_id, labels)

            # 3. Handle messagesDeleted
            for delete_event in record.get("messagesDeleted", []):
                msg_id = delete_event.get("message", {}).get("id")
                if msg_id:
                    GmailRepository.delete_message_by_gmail_id(db, user.id, msg_id)
                    messages_deleted_count += 1

        # Update sync state with the advanced historyId from the last page.
        current_state = GmailRepository.get_or_create_sync_state(db, user.id)
        total_count = (
            current_state.synced_message_count + messages_added_count - messages_deleted_count
        )

        partial_error = (
            f"Skipped {len(failed_message_ids)} message(s) due to fetch errors."
            if failed_message_ids
            else None
        )

        GmailRepository.update_sync_state(
            db,
            user.id,
            sync_status="COMPLETED",
            last_history_id=new_history_id,
            synced_message_count=max(0, total_count),
            error_message=partial_error,
        )

        return {
            "status": "COMPLETED",
            "type": "INCREMENTAL_HISTORY",
            "messages_added": messages_added_count,
            "messages_deleted": messages_deleted_count,
            "last_history_id": new_history_id,
            "failed_count": len(failed_message_ids),
        }

    async def _fetch_and_persist_message(
        self,
        db: Session,
        user: User,
        access_token: str,
        message_id: str,
    ):
        """Fetch full message from Gmail API, parse MIME content, and upsert into PostgreSQL.

        Raises on any fetch or persistence error so the caller can decide whether
        to abort or isolate the failure (see FIX-SYNC-5 wrappers in callers).
        """
        msg_data = await self.client.get_message(access_token, message_id)

        gmail_msg_id = msg_data["id"]
        gmail_thread_id = msg_data["threadId"]
        snippet = msg_data.get("snippet")
        history_id = int(msg_data["historyId"]) if "historyId" in msg_data else None
        labels = msg_data.get("labelIds", [])

        # Internal date timestamp
        internal_date_ms = int(msg_data.get("internalDate", 0))
        received_at = (
            datetime.fromtimestamp(internal_date_ms / 1000.0, tz=timezone.utc)
            if internal_date_ms
            else None
        )

        # Parse MIME headers and body parts
        headers_data = MIMEParser.parse_headers(msg_data.get("payload", {}).get("headers", []))
        payload_data = MIMEParser.parse_payload(msg_data.get("payload", {}))

        # 1. Upsert parent EmailThread
        thread = GmailRepository.upsert_thread(
            db,
            user_id=user.id,
            gmail_thread_id=gmail_thread_id,
            snippet=snippet,
            history_id=history_id,
            last_message_at=received_at or headers_data["sent_at"],
        )

        # 2. Upsert child EmailMessage
        attachments_list = payload_data["attachments"]
        has_attachments = len(attachments_list) > 0

        email_msg = GmailRepository.upsert_message(
            db,
            user_id=user.id,
            thread_id=thread.id,
            gmail_message_id=gmail_msg_id,
            gmail_thread_id=gmail_thread_id,
            sender=headers_data["sender"],
            recipients=headers_data["recipients"],
            subject=headers_data["subject"],
            snippet=snippet,
            body_plain=payload_data["body_plain"],
            body_html=payload_data["body_html"],
            sent_at=headers_data["sent_at"],
            received_at=received_at,
            labels=labels,
            has_attachments=has_attachments,
            history_id=history_id,
        )

        # Index message into pgvector for immediate semantic search and RAG
        try:
            from backend.app.services.vector_search_service import VectorSearchService
            VectorSearchService().index_email_message(db, user.id, email_msg.id)
        except Exception as idx_err:
            logger.debug("Automatic vector indexing skipped for message %s: %s", gmail_msg_id, idx_err)

        # 3. Process Attachment Metadata & Selective Download
        for att in attachments_list:
            filename = att["filename"]
            mime_type = att.get("mime_type")
            size_bytes = att.get("size_bytes", 0)
            att_id = att.get("gmail_attachment_id")

            # Check if file extension is supported for selective download
            ext = Path(filename).suffix.lower()
            should_download = (
                ext in SUPPORTED_DOWNLOAD_EXTENSIONS
                and size_bytes <= settings.ATTACHMENT_MAX_SIZE_BYTES
                and att_id is not None
            )

            storage_path = None
            is_downloaded = False

            if should_download and att_id:
                try:
                    content = await self.client.get_attachment(access_token, gmail_msg_id, att_id)
                    # Verify actual downloaded byte size
                    if len(content) <= settings.ATTACHMENT_MAX_SIZE_BYTES:
                        storage_dir = Path("storage") / "attachments" / str(user.id)
                        storage_dir.mkdir(parents=True, exist_ok=True)

                        # UUID filename prevents path traversal attacks
                        uuid_filename = f"{uuid.uuid4().hex}.dat"
                        file_path = storage_dir / uuid_filename

                        with open(file_path, "wb") as f:
                            f.write(content)

                        # FIX-ATT-1: Use resolved absolute path — stable regardless of CWD.
                        # Relative-to-CWD paths break when the process working directory
                        # changes (e.g., during tests or container restarts).
                        storage_path = str(file_path.resolve())
                        is_downloaded = True
                except Exception as exc:
                    logger.warning(
                        "Attachment download failed: message_id=%s attachment_id=%s "
                        "filename=%s error=%s",
                        gmail_msg_id,
                        att_id,
                        filename,
                        type(exc).__name__,
                    )

            GmailRepository.create_or_update_attachment(
                db,
                user_id=user.id,
                message_id=email_msg.id,
                filename=filename,
                mime_type=mime_type,
                size_bytes=size_bytes,
                gmail_attachment_id=att_id,
                storage_path=storage_path,
                is_downloaded=is_downloaded,
            )
