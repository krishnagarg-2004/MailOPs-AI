"""
Unit tests for Phase 10: Demo Seeding, Power-User Features, and Polish.
"""

import uuid
from unittest.mock import MagicMock, patch
import pytest
from backend.app.api.v1.auth import seed_user_demo
from backend.app.models.user import User


@pytest.mark.asyncio
async def test_seed_user_demo_endpoint():
    """Verify POST /api/v1/auth/seed-demo triggers demo seeder with target user."""
    user = User(
        id=uuid.uuid4(),
        email="auditor@enterprise.corp",
        full_name="Compliance Auditor",
    )

    mock_db = MagicMock()

    with patch("backend.app.scripts.seed_demo_data.seed_demo_environment") as mock_seeder:
        mock_seeder.return_value = {
            "demo_user": "auditor@enterprise.corp",
            "threads_created": 5,
            "actions_created": 8,
            "embeddings_created": 12,
        }

        res = await seed_user_demo(current_user=user, db=mock_db)

        assert res["status"] == "success"
        assert "Loaded enterprise demo threads" in res["message"]
        assert res["details"]["threads_created"] == 5
        mock_seeder.assert_called_once_with(db=mock_db, target_user=user)
