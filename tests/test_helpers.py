"""
EnterpriseAIMailOPs_MIPRO Test Utilities and Helper Functions.
Provides AST/regex source scanners, color contrast calculators, fixture factories, and auth generators.
"""

from datetime import datetime, timezone
import math
import os
import re
import uuid
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.crypto import encrypt_token
from backend.app.models.email_message import EmailMessage
from backend.app.models.email_thread import EmailThread
from backend.app.models.oauth import OAuthAccount
from backend.app.models.user import User
from backend.app.services.auth_service import create_user_session


def scan_frontend_for_native_dialogs(
    root_dir: str = "frontend/src",
) -> List[Dict[str, Any]]:
    """Scan frontend source code for forbidden native browser alert() and confirm() calls.
    
    Returns:
        List of dicts with file path, line number, pattern matched, and code snippet.
    """
    violations = []
    # Pattern to match alert(...) or confirm(...) or window.alert(...) or window.confirm(...)
    # Exclude comments (// or /* ... */)
    pattern = re.compile(r"(?<!\/\/\s)(?<!\*\s)\b(?:window\.)?(alert|confirm)\s*\(", re.IGNORECASE)

    if not os.path.exists(root_dir):
        return violations

    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith((".tsx", ".ts")) and not file.endswith((".d.ts", ".test.ts", ".test.tsx")):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                    for idx, line in enumerate(lines, 1):
                        stripped = line.strip()
                        if stripped.startswith("//") or stripped.startswith("*"):
                            continue
                        match = pattern.search(line)
                        if match:
                            violations.append({
                                "file": file_path.replace("\\", "/"),
                                "line": idx,
                                "dialog_type": match.group(1).lower(),
                                "snippet": stripped,
                            })
                except Exception as e:
                    pass
    return violations


def scan_frontend_for_forbidden_colors(
    root_dir: str = "frontend/src",
    target_components: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Scan frontend components for forbidden non-theme colors (slate, indigo, amber, purple, etc.).
    
    The official theme is strictly Black/Gray/Red (black, zinc, neutral, red, white).
    """
    forbidden_pattern = re.compile(
        r"\b(?:text|bg|border|fill|stroke|ring|from|to)-(?:slate|indigo|amber|purple|cyan|emerald|blue|violet)-[0-9]{2,3}\b|"
        r"#(?:475569|94a3b8|1e293b|78350f|1e3a8a|581c87|064e3b|38bdf8)"
    )

    violations = []
    if not os.path.exists(root_dir):
        return violations

    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith((".tsx", ".ts", ".css")):
                rel_path = os.path.relpath(os.path.join(root, file), root_dir).replace("\\", "/")
                if target_components and not any(comp in rel_path for comp in target_components):
                    continue
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                    for idx, line in enumerate(lines, 1):
                        stripped = line.strip()
                        if stripped.startswith("//") or stripped.startswith("*"):
                            continue
                        matches = forbidden_pattern.findall(line)
                        for m in matches:
                            violations.append({
                                "file": file_path.replace("\\", "/"),
                                "line": idx,
                                "token": m,
                                "snippet": stripped,
                            })
                except Exception:
                    pass
    return violations


def parse_hex_color(hex_str: str) -> Tuple[int, int, int]:
    """Parse #RRGGBB or #RGB into (r, g, b) tuple."""
    hex_clean = hex_str.strip().lstrip("#")
    if len(hex_clean) == 3:
        hex_clean = "".join(c * 2 for c in hex_clean)
    if len(hex_clean) != 6:
        raise ValueError(f"Invalid hex color: {hex_str}")
    return (
        int(hex_clean[0:2], 16),
        int(hex_clean[2:4], 16),
        int(hex_clean[4:6], 16),
    )


def calculate_wcag_luminance(r: int, g: int, b: int) -> float:
    """Calculate WCAG 2.1 relative luminance for an sRGB color."""
    vals = []
    for c in (r, g, b):
        c_norm = c / 255.0
        if c_norm <= 0.03928:
            vals.append(c_norm / 12.92)
        else:
            vals.append(((c_norm + 0.055) / 1.055) ** 2.4)
    return 0.2126 * vals[0] + 0.7152 * vals[1] + 0.0722 * vals[2]


def calculate_wcag_contrast(fg_hex: str, bg_hex: str) -> float:
    """Calculate WCAG 2.1 contrast ratio between foreground and background hex colors.
    
    Formula: (L1 + 0.05) / (L2 + 0.05) where L1 is the lighter luminance.
    """
    l1 = calculate_wcag_luminance(*parse_hex_color(fg_hex))
    l2 = calculate_wcag_luminance(*parse_hex_color(bg_hex))
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def create_test_auth_session(
    db: Session,
    email: str = "testuser@enterprise-mailops.io",
    full_name: str = "Test MailOps Operator",
    access_token: str = "mock_access_token_demo",
    refresh_token: str = "mock_refresh_token_demo",
    scopes: str = "openid email profile https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.compose",
) -> Tuple[User, Dict[str, str], str]:
    """Helper to create a fully authenticated user with OAuth tokens and valid session cookies."""
    user = User(
        email=email,
        full_name=full_name,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    oauth_acc = OAuthAccount(
        user_id=user.id,
        provider="google",
        provider_account_id=f"sub_{uuid.uuid4().hex[:12]}",
        email=email,
        encrypted_access_token=encrypt_token(access_token),
        encrypted_refresh_token=encrypt_token(refresh_token),
        scopes=scopes,
        token_expires_at=datetime.now(timezone.utc),
    )
    db.add(oauth_acc)
    db.commit()

    raw_token, _ = create_user_session(db, user)
    cookies = {settings.SESSION_COOKIE_NAME: raw_token}
    return user, cookies, raw_token


def create_test_email(
    db: Session,
    user_id: uuid.UUID,
    subject: str = "Operational Alert: Payment Gateway Latency",
    body: str = "Payment gateway response times have exceeded 850ms. Please check database connection pools and confirm threshold stabilization.",
    sender: str = "devops-alerts@enterprise.internal",
    thread_id: Optional[uuid.UUID] = None,
    gmail_thread_id: Optional[str] = None,
    gmail_message_id: Optional[str] = None,
) -> Tuple[EmailThread, EmailMessage]:
    """Helper to create an EmailThread and EmailMessage pair."""
    g_thread_id = gmail_thread_id or f"thread_{uuid.uuid4().hex[:10]}"
    g_message_id = gmail_message_id or f"msg_{uuid.uuid4().hex[:10]}"

    if not thread_id:
        thread = EmailThread(
            user_id=user_id,
            gmail_thread_id=g_thread_id,
            snippet=body[:100],
            last_message_at=datetime.now(timezone.utc),
        )
        db.add(thread)
        db.commit()
        db.refresh(thread)
    else:
        thread = db.query(EmailThread).filter_by(id=thread_id).first()

    message = EmailMessage(
        user_id=user_id,
        thread_id=thread.id,
        gmail_message_id=g_message_id,
        gmail_thread_id=g_thread_id,
        sender=sender,
        recipients="operator@enterprise-mailops.io",
        subject=subject,
        snippet=body[:100],
        body_plain=body,
        body_html=f"<p>{body}</p>",
        received_at=datetime.now(timezone.utc),
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    return thread, message
