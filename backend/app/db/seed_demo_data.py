"""
Alias module redirecting to backend.app.scripts.seed_demo_data.
"""

from backend.app.scripts.seed_demo_data import (
    DEMO_USER_AVATAR,
    DEMO_USER_EMAIL,
    DEMO_USER_NAME,
    seed_demo_environment,
)

__all__ = [
    "DEMO_USER_AVATAR",
    "DEMO_USER_EMAIL",
    "DEMO_USER_NAME",
    "seed_demo_environment",
]
