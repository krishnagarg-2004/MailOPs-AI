from backend.app.utils.mime_parser import MIMEParser, decode_base64url, parse_rfc2822_date, strip_quoted_replies
from backend.tests.fixtures.gmail_fixtures import MOCK_MESSAGE_101_PAYLOAD


def test_decode_base64url():
    """Verify base64url string decoding with and without padding."""
    # "Hello World" in base64url is "SGVsbG8gV29ybGQ"
    assert decode_base64url("SGVsbG8gV29ybGQ") == "Hello World"
    assert decode_base64url("") == ""
    assert decode_base64url(None) == ""


def test_parse_rfc2822_date():
    """Verify parsing RFC 2822 date strings into UTC datetimes."""
    dt = parse_rfc2822_date("Mon, 16 Mar 2026 10:00:00 +0000")
    assert dt is not None
    assert dt.year == 2026
    assert dt.month == 3
    assert dt.day == 16
    assert dt.hour == 10

    assert parse_rfc2822_date(None) is None
    assert parse_rfc2822_date("invalid_date_string") is None


def test_strip_quoted_replies():
    """Verify stripping quoted reply headers and > quotation marks."""
    text_with_quote = "Hello Alice, please review.\n\nOn Mon, 16 Mar wrote:\n> Quoted text line 1\n> Quoted text line 2"
    clean = strip_quoted_replies(text_with_quote)
    assert clean == "Hello Alice, please review."

    text_no_quote = "Simple message without replies."
    assert strip_quoted_replies(text_no_quote) == "Simple message without replies."


def test_mime_parser_extracts_headers_and_body():
    """Verify MIMEParser extracts sender, recipients, subject, plain body, HTML body, and attachment metadata."""
    headers_data = MIMEParser.parse_headers(MOCK_MESSAGE_101_PAYLOAD["payload"]["headers"])
    payload_data = MIMEParser.parse_payload(MOCK_MESSAGE_101_PAYLOAD["payload"])

    assert headers_data["sender"] == "Alice Smith <alice@vendor.com>"
    assert headers_data["subject"] == "Vendor Contract Review - Action Required"
    assert "testuser@enterprise.com" in headers_data["recipients"]


    assert payload_data["body_plain"] is not None
    assert "Hello Alice" in payload_data["body_plain"]
    assert payload_data["body_html"] is not None

    attachments = payload_data["attachments"]
    assert len(attachments) == 1
    assert attachments[0]["filename"] == "vendor_contract.pdf"
    assert attachments[0]["mime_type"] == "application/pdf"
    assert attachments[0]["size_bytes"] == 10240
