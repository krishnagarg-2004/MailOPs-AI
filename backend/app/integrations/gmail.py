from datetime import datetime, timezone, timedelta
from typing import Any
import httpx
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.crypto import decrypt_token, encrypt_token
from backend.app.models.oauth import OAuthAccount


class GmailAPIError(Exception):
    """Exception raised when Gmail REST API returns an error status code."""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"Gmail API Error ({status_code}): {message}")


class GmailClient:
    """Async client for interacting with Google Gmail REST API with automatic OAuth token refresh."""

    BASE_URL = "https://gmail.googleapis.com/gmail/v1/users/me"

    @staticmethod
    def get_valid_access_token(db: Session, oauth_account: OAuthAccount) -> str:
        """
        Verify OAuth access token expiration. Decrypt refresh token and execute
        refresh operation if expired or expiring within 5 minutes.
        """
        now_utc = datetime.now(timezone.utc)

        # 1. If access token is valid (expires in > 5 minutes), decrypt and return
        if (
            oauth_account.encrypted_access_token
            and oauth_account.token_expires_at
            and oauth_account.token_expires_at > (now_utc + timedelta(minutes=5))
        ):
            decrypted = decrypt_token(oauth_account.encrypted_access_token)
            if decrypted:
                return decrypted

        # 2. Access token is expired or missing -> check refresh token
        if not oauth_account.encrypted_refresh_token:
            raise ValueError("Missing OAuth refresh token. Re-authentication required.")

        refresh_token = decrypt_token(oauth_account.encrypted_refresh_token)
        if not refresh_token:
            raise ValueError("Failed to decrypt OAuth refresh token. Re-authentication required.")

        # 3. Request new access token from Google OAuth token endpoint
        token_url = "https://oauth2.googleapis.com/token"
        payload = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(token_url, data=payload)
        except Exception as e:
            raise ValueError(f"OAuth token refresh request failed: {str(e)}") from e

        if response.status_code != 200:
            err_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            error_code = err_data.get("error", "")
            if error_code == "invalid_grant" or response.status_code in (400, 401):
                # Revoked authorization -> clear tokens
                oauth_account.encrypted_access_token = None
                db.add(oauth_account)
                db.commit()
                raise ValueError("Google authorization revoked or expired. Re-authentication required.")
            raise ValueError(f"Token refresh failed with status {response.status_code}: {response.text}")

        data = response.json()
        new_access_token = data.get("access_token")
        expires_in = data.get("expires_in", 3600)

        if not new_access_token:
            raise ValueError("No access_token returned in Google refresh response.")

        # 4. Encrypt new access token and update OAuthAccount in PostgreSQL
        oauth_account.encrypted_access_token = encrypt_token(new_access_token)
        oauth_account.token_expires_at = now_utc + timedelta(seconds=expires_in)
        db.add(oauth_account)
        db.commit()
        db.refresh(oauth_account)

        return new_access_token

    async def get_profile(self, access_token: str) -> dict[str, Any]:
        """Fetch user Gmail profile (emailAddress, historyId, messagesTotal)."""
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{self.BASE_URL}/profile", headers=headers)
            if resp.status_code != 200:
                raise GmailAPIError(resp.status_code, resp.text)
            return resp.json()

    async def list_messages(
        self,
        access_token: str,
        page_token: str | None = None,
        q: str | None = None,
        max_results: int = 100,
    ) -> dict[str, Any]:
        """List messages in user's mailbox with pagination."""
        headers = {"Authorization": f"Bearer {access_token}"}
        params: dict[str, Any] = {"maxResults": min(max_results, 100), "includeSpamTrash": "false"}
        if page_token:
            params["pageToken"] = page_token
        if q:
            params["q"] = q

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{self.BASE_URL}/messages", headers=headers, params=params)
            if resp.status_code != 200:
                raise GmailAPIError(resp.status_code, resp.text)
            return resp.json()

    async def get_message(self, access_token: str, message_id: str) -> dict[str, Any]:
        """Get full message payload by message ID."""
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {"format": "full"}
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{self.BASE_URL}/messages/{message_id}", headers=headers, params=params)
            if resp.status_code != 200:
                raise GmailAPIError(resp.status_code, resp.text)
            return resp.json()

    async def list_history(
        self,
        access_token: str,
        start_history_id: int,
        page_token: str | None = None,
    ) -> dict[str, Any]:
        """List incremental mailbox history changes starting from start_history_id."""
        headers = {"Authorization": f"Bearer {access_token}"}
        params: dict[str, Any] = {
            "startHistoryId": str(start_history_id),
            "historyTypes": ["messageAdded", "messageDeleted", "labelAdded", "labelRemoved"],
        }
        if page_token:
            params["pageToken"] = page_token

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{self.BASE_URL}/history", headers=headers, params=params)
            if resp.status_code != 200:
                raise GmailAPIError(resp.status_code, resp.text)
            return resp.json()

    async def get_attachment(
        self,
        access_token: str,
        message_id: str,
        attachment_id: str,
    ) -> bytes:
        """Download raw attachment byte content by message ID and attachment ID."""
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{self.BASE_URL}/messages/{message_id}/attachments/{attachment_id}",
                headers=headers,
            )
            if resp.status_code != 200:
                raise GmailAPIError(resp.status_code, resp.text)
            data = resp.json()
            raw_b64 = data.get("data", "")
            padded = raw_b64.replace("-", "+").replace("_", "/")
            padding = len(padded) % 4
            if padding:
                padded += "=" * (4 - padding)
            return base64.b64decode(padded)
