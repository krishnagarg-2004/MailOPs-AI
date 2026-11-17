"""
Tier 2 — Boundary & Corner Cases: Older Email Loading (+50)
Tests boundaries: out-of-range counts, empty mailbox offsets, non-existent pages,
and parameter validation.
"""

from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_boundary_pagination_count_zero(
    client: TestClient,
    auth_user: dict,
):
    """Verify POST /api/v1/gmail/sync-older?count=0 is rejected with HTTP 422 (min 10)."""
    response = client.post(
        "/api/v1/gmail/sync-older?count=0",
        cookies=auth_user["cookies"],
    )
    assert response.status_code == 422


def test_boundary_pagination_count_negative(
    client: TestClient,
    auth_user: dict,
):
    """Verify POST /api/v1/gmail/sync-older?count=-50 is rejected with HTTP 422."""
    response = client.post(
        "/api/v1/gmail/sync-older?count=-50",
        cookies=auth_user["cookies"],
    )
    assert response.status_code == 422


def test_boundary_pagination_count_exceeds_max(
    client: TestClient,
    auth_user: dict,
):
    """Verify POST /api/v1/gmail/sync-older?count=500 is rejected with HTTP 422 (max 100)."""
    response = client.post(
        "/api/v1/gmail/sync-older?count=500",
        cookies=auth_user["cookies"],
    )
    assert response.status_code == 422


def test_boundary_threads_page_out_of_bounds(
    client: TestClient,
    auth_user: dict,
):
    """Verify GET /api/v1/gmail/threads?page=9999 returns empty list [] without error."""
    response = client.get(
        "/api/v1/gmail/threads?page=9999&limit=50",
        cookies=auth_user["cookies"],
    )
    assert response.status_code == 200
    assert response.json() == []


def test_boundary_threads_limit_bounds(
    client: TestClient,
    auth_user: dict,
):
    """Verify GET /api/v1/gmail/threads rejects limit=0 or limit>200 with 422."""
    res_zero = client.get(
        "/api/v1/gmail/threads?limit=0",
        cookies=auth_user["cookies"],
    )
    assert res_zero.status_code == 422

    res_huge = client.get(
        "/api/v1/gmail/threads?limit=500",
        cookies=auth_user["cookies"],
    )
    assert res_huge.status_code == 422
