from datetime import datetime, timezone
import os
from pathlib import Path
import uuid
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.integrations.gmail import GmailAPIError, GmailClient
from backend.app.models.oauth import OAuthAccount
from backend.app.models.user import User
from backend.app.repositories.gmail_repository import GmailRepository
from backend.app.utils.mime_parser import MIMEParser

SUPPORTED_DOWNLOAD_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".docx"}


class GmailSyncService:
    """Independent domain service orchestrating Gmail mailbox synchronization."""

    def __init__(self, client: GmailClient | None = None):
        self.client = client or GmailClient()

    async def execute_sync(self, db: Session, user: User) -> dict[str, Any]:
        """
        Main synchronization entrypoint. Checks existing sync state and routes
        to incremental History API sync if valid last_history_id exists, or
        performs baseline initial synchronization.
        """
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
        try:
            access_token = self.client.get_valid_access_token(db, oauth_account)
        except ValueError as e:
            GmailRepository.update_sync_state(
                db, user.id, sync_status="FAILED", error_message=str(e)
            )
            raise

        sync_state = GmailRepository.get_or_create_sync_state(db, user.id)

        # 3. Mark sync_status = SYNCING
        GmailRepository.update_sync_state(db, user.id, sync_status="SYNCING")

        try:
            if sync_state.last_history_id:
                # Attempt incremental History API sync
                try:
                    return await self._sync_history_incremental(db, user, oauth_account, access_token, sync_state.last_history_id)
                except GmailAPIError as e:
                    if e.status_code == 404 or "historyIdNotFound" in e.message:
                        # Expired or invalid historyId -> fallback to full initial sync
                        GmailRepository.update_sync_state(db, user.id, last_history_id=None)
                        return await self._sync_initial_baseline(db, user, oauth_account, access_token)
                    raise
            else:
                # Perform baseline initial sync
                return await self._sync_initial_baseline(db, user, oauth_account, access_token)
        except Exception as e:
            GmailRepository.update_sync_state(
                db, user.id, sync_status="FAILED", error_message=str(e)
            )
            raise

    async def _sync_initial_baseline(
        self,
        db: Session,
        user: User,
        oauth_account: OAuthAccount,
        access_token: str,
    ) -> dict[str, Any]:
        """
        Perform initial mailbox synchronization with baseline historyId capture.
        Captures baseline historyId BEFORE message ingestion to guarantee no lost updates.
        """
        # STEP 1: Baseline History ID Capture Invariant
        profile = await self.client.get_profile(access_token)
        baseline_history_id_str = profile.get("historyId")
        baseline_history_id = int(baseline_history_id_str) if baseline_history_id_str else None

        # STEP 2: List messages up to INITIAL_SYNC_LIMIT
        limit = settings.INITIAL_SYNC_LIMIT
        messages_processed = 0
        page_token = None

        while messages_processed < limit:
            batch_size = min(100, limit - messages_processed)
            list_resp = await self.client.list_messages(
                access_token, page_token=page_token, max_results=batch_size
            )

            msg_summaries = list_resp.get("messages", [])
            if not msg_summaries:
                break

            for summary in msg_summaries:
                msg_id = summary["id"]
                await self._fetch_and_persist_message(db, user, access_token, msg_id)
                messages_processed += 1
                if messages_processed >= limit:
                    break

            page_token = list_resp.get("nextPageToken")
            if not page_token:
                break

        # STEP 3: Complete sync and save baseline_history_id
        GmailRepository.update_sync_state(
            db,
            user.id,
            sync_status="COMPLETED",
            last_history_id=baseline_history_id,
            synced_message_count=messages_processed,
        )

        return {
            "status": "COMPLETED",
            "type": "INITIAL_BASELINE",
            "messages_synced": messages_processed,
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
        """Perform incremental History API synchronization starting from start_history_id."""
        history_resp = await self.client.list_history(access_token, start_history_id)
        history_records = history_resp.get("history", [])
        new_history_id_str = history_resp.get("historyId")
        new_history_id = int(new_history_id_str) if new_history_id_str else start_history_id

        messages_added_count = 0
        messages_deleted_count = 0

        for record in history_records:
            # 1. Handle messagesAdded
            for add_event in record.get("messagesAdded", []):
                msg_id = add_event.get("message", {}).get("id")
                if msg_id:
                    await self._fetch_and_persist_message(db, user, access_token, msg_id)
                    messages_added_count += 1

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

        # Update sync state with advanced history_id
        current_state = GmailRepository.get_or_create_sync_state(db, user.id)
        total_count = current_state.synced_message_count + messages_added_count - messages_deleted_count
        
        GmailRepository.update_sync_state(
            db,
            user.id,
            sync_status="COMPLETED",
            last_history_id=new_history_id,
            synced_message_count=max(0, total_count),
        )

        return {
            "status": "COMPLETED",
            "type": "INCREMENTAL_HISTORY",
            "messages_added": messages_added_count,
            "messages_deleted": messages_deleted_count,
            "last_history_id": new_history_id,
        }

    async def _fetch_and_persist_message(
        self,
        db: Session,
        user: User,
        access_token: str,
        message_id: str,
    ):
        """Fetch full message from Gmail API, parse MIME content, and upsert records into PostgreSQL."""
        msg_data = await self.client.get_message(access_token, message_id)
        
        gmail_msg_id = msg_data["id"]
        gmail_thread_id = msg_data["threadId"]
        snippet = msg_data.get("snippet")
        history_id = int(msg_data["historyId"]) if "historyId" in msg_data else None
        labels = msg_data.get("labelIds", [])
        
        # Internal date timestamp
        internal_date_ms = int(msg_data.get("internalDate", 0))
        received_at = datetime.fromtimestamp(internal_date_ms / 1000.0, tz=timezone.utc) if internal_date_ms else None

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
                        storage_dir = Path(f"storage/attachments/{user.id}")
                        storage_dir.mkdir(parents=True, exist_ok=True)
                        
                        # Generate random UUID filename to prevent path traversal
                        uuid_filename = f"{uuid.uuid4().hex}.dat"
                        file_path = storage_dir / uuid_filename
                        
                        with open(file_path, "wb") as f:
                            f.write(content)
                            
                        storage_path = str(file_path.relative_to(Path.cwd()) if file_path.is_relative_to(Path.cwd()) else file_path)
                        is_downloaded = True
                except Exception:
                    # Non-fatal: save metadata even if content download fails
                    pass

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
