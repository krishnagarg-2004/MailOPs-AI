import uuid
import pytest
from backend.app.core.config import settings


def test_graph_config_max_traversal_depth():
    assert settings.GRAPH_MAX_TRAVERSAL_DEPTH == 10
