import base64
from datetime import datetime, timezone
import json
import re
from email.utils import parsedate_to_datetime
from typing import Any


def decode_base64url(data: str | None) -> str:
    """Decode base64url encoded string from Gmail API payload."""
    if not data:
        return ""
    try:
        # Standardize base64url padding
        padded_data = data.replace("-", "+").replace("_", "/")
        padding = len(padded_data) % 4
        if padding:
            padded_data += "=" * (4 - padding)
        return base64.b64decode(padded_data).decode("utf-8", errors="replace")
    except Exception:
        return ""


def parse_rfc2822_date(date_str: str | None) -> datetime | None:
    """Parse RFC 2822 date header string into UTC datetime object."""
    if not date_str:
        return None
    try:
        dt = parsedate_to_datetime(date_str)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def strip_quoted_replies(text: str | None) -> str:
    """Strip quoted reply text (On ... wrote:, lines starting with >) for clean body storage."""
    if not text:
        return ""
    
    lines = text.splitlines()
    clean_lines = []
    
    for line in lines:
        # Stop at standard quoted reply header pattern
        if re.match(r"^On\s+.*wrote:\s*$", line.strip(), re.IGNORECASE):
            break
        if re.match(r"^-+\s*Original Message\s*-+", line.strip(), re.IGNORECASE):
            break
        # Skip lines starting with quote mark >
        if line.strip().startswith(">"):
            continue
        clean_lines.append(line)
        
    return "\n".join(clean_lines).strip()


class MIMEParser:
    """Utility class for parsing raw Gmail API message payload dictionaries."""

    @staticmethod
    def parse_headers(headers: list[dict[str, str]]) -> dict[str, Any]:
        """Extract key headers (From, To, Cc, Bcc, Subject, Date) from headers list."""
        header_map = {h.get("name", "").lower(): h.get("value", "") for h in headers if "name" in h}
        
        sender = header_map.get("from")
        subject = header_map.get("subject")
        date_raw = header_map.get("date")
        sent_at = parse_rfc2822_date(date_raw)

        to_str = header_map.get("to", "")
        cc_str = header_map.get("cc", "")
        bcc_str = header_map.get("bcc", "")
        
        recipients_dict = {
            "to": [addr.strip() for addr in to_str.split(",") if addr.strip()],
            "cc": [addr.strip() for addr in cc_str.split(",") if addr.strip()],
            "bcc": [addr.strip() for addr in bcc_str.split(",") if addr.strip()],
        }
        recipients_json = json.dumps(recipients_dict)

        return {
            "sender": sender,
            "subject": subject,
            "sent_at": sent_at,
            "recipients": recipients_json,
        }

    @classmethod
    def parse_payload(cls, payload: dict[str, Any]) -> dict[str, Any]:
        """Recursively traverse message payload to extract plain text, HTML body, and attachments."""
        plain_parts = []
        html_parts = []
        attachments = []

        def _traverse_part(part: dict[str, Any]):
            mime_type = part.get("mimeType", "")
            filename = part.get("filename", "")
            body = part.get("body", {})
            attachment_id = body.get("attachmentId")

            # Check if this part is an attachment
            if filename and (attachment_id or body.get("size", 0) > 0):
                attachments.append({
                    "gmail_attachment_id": attachment_id,
                    "filename": filename,
                    "mime_type": mime_type,
                    "size_bytes": body.get("size", 0),
                })

            # Check text body parts
            if mime_type == "text/plain" and "data" in body and not filename:
                plain_parts.append(decode_base64url(body["data"]))
            elif mime_type == "text/html" and "data" in body and not filename:
                html_parts.append(decode_base64url(body["data"]))

            # Recurse through sub-parts if multipart
            for sub_part in part.get("parts", []):
                _traverse_part(sub_part)

        _traverse_part(payload)

        body_plain_raw = "\n".join(plain_parts) if plain_parts else None
        body_html = "\n".join(html_parts) if html_parts else None
        body_plain_clean = strip_quoted_replies(body_plain_raw) if body_plain_raw else None

        return {
            "body_plain": body_plain_clean or body_plain_raw,
            "body_html": body_html,
            "attachments": attachments,
        }
