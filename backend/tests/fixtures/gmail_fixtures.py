from typing import Any

MOCK_GMAIL_PROFILE = {
    "emailAddress": "testuser@enterprise.com",
    "messagesTotal": 105,
    "threadsTotal": 42,
    "historyId": "1000500",
}

MOCK_GMAIL_MESSAGE_LIST_PAGE_1 = {
    "messages": [
        {"id": "msg_101", "threadId": "thread_001"},
        {"id": "msg_102", "threadId": "thread_001"},
        {"id": "msg_103", "threadId": "thread_002"},
    ],
    "resultSizeEstimate": 3,
    "nextPageToken": "page_2_token",
}

MOCK_GMAIL_MESSAGE_LIST_PAGE_2 = {
    "messages": [
        {"id": "msg_104", "threadId": "thread_003"},
    ],
    "resultSizeEstimate": 1,
}

MOCK_MESSAGE_101_PAYLOAD: dict[str, Any] = {
    "id": "msg_101",
    "threadId": "thread_001",
    "labelIds": ["INBOX", "UNREAD"],
    "snippet": "Hello, please review the attached contract document.",
    "historyId": "1000100",
    "internalDate": "1773715200000",  # Mar 2026 UTC
    "payload": {
        "mimeType": "multipart/mixed",
        "headers": [
            {"name": "From", "value": "Alice Smith <alice@vendor.com>"},
            {"name": "To", "value": "testuser@enterprise.com"},
            {"name": "Subject", "value": "Vendor Contract Review - Action Required"},
            {"name": "Date", "value": "Mon, 16 Mar 2026 10:00:00 +0000"},
        ],
        "parts": [
            {
                "mimeType": "text/plain",
                "body": {
                    # "Hello Alice, please review the contract.\n\nOn Mon wrote:\n> Old thread"
                    "data": "SGVsbG8gQWxpY2UsIHBsZWFzZSByZXZpZXcgdGhlIGNvbnRyYWN0LgoK"
                },
            },
            {
                "mimeType": "text/html",
                "body": {
                    "data": "PHA+SGVsbG8gQWxpY2UsIHBsZWFzZSByZXZpZXcgdGhlIGNvbnRyYWN0LjwvcD4="
                },
            },
            {
                "mimeType": "application/pdf",
                "filename": "vendor_contract.pdf",
                "body": {
                    "attachmentId": "att_pdf_101",
                    "size": 10240,
                },
            },
        ],
    },
}

MOCK_MESSAGE_102_PAYLOAD: dict[str, Any] = {
    "id": "msg_102",
    "threadId": "thread_001",
    "labelIds": ["INBOX", "IMPORTANT"],
    "snippet": "Thanks for sending. Reverting with comments.",
    "historyId": "1000200",
    "internalDate": "1773718800000",
    "payload": {
        "mimeType": "text/plain",
        "headers": [
            {"name": "From", "value": "testuser@enterprise.com"},
            {"name": "To", "value": "alice@vendor.com"},
            {"name": "Subject", "value": "Re: Vendor Contract Review - Action Required"},
            {"name": "Date", "value": "Mon, 16 Mar 2026 11:00:00 +0000"},
        ],
        "body": {
            "data": "VGhhbmtzIGZvciBzZW5kaW5nLiBSZXZlcnRpbmcgd2l0aCBjb21tZW50cy4="
        },
    },
}

MOCK_GMAIL_HISTORY_INCREMENTAL: dict[str, Any] = {
    "history": [
        {
            "id": "1000600",
            "messagesAdded": [
                {
                    "message": {
                        "id": "msg_105",
                        "threadId": "thread_004",
                        "labelIds": ["INBOX"],
                    }
                }
            ],
        },
        {
            "id": "1000601",
            "labelsAdded": [
                {
                    "message": {
                        "id": "msg_101",
                        "threadId": "thread_001",
                        "labelIds": ["INBOX", "UNREAD", "STARRED"],
                    },
                    "labelIds": ["STARRED"],
                }
            ],
        },
        {
            "id": "1000602",
            "messagesDeleted": [
                {
                    "message": {
                        "id": "msg_103",
                        "threadId": "thread_002",
                    }
                }
            ],
        },
    ],
    "historyId": "1000602",
}
