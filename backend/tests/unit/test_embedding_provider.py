import math
import pytest
from backend.app.ai.embedding_provider import GeminiEmbeddingProvider, MockEmbeddingProvider
from backend.app.core.config import settings


def test_mock_embedding_provider_dimension_and_normalization():
    provider = MockEmbeddingProvider()
    texts = ["Sample text chunk 1", "Sample text chunk 2"]
    embeddings = provider.generate_embeddings(texts)

    assert len(embeddings) == 2
    for vec in embeddings:
        assert len(vec) == settings.EMBEDDING_DIMENSION  # Exactly 768 dimensions
        # Assert unit vector length (L2 norm = 1.0)
        norm = math.sqrt(sum(v * v for v in vec))
        assert abs(norm - 1.0) < 1e-4


def test_embedding_provider_runtime_dimension_validation():
    # Verify strict validation exception when vector dimension is wrong
    invalid_vec = [0.1] * 500  # 500 dims instead of 768
    with pytest.raises(ValueError) as exc_info:
        GeminiEmbeddingProvider._validate_dimension(invalid_vec)
    assert "Embedding dimension mismatch: expected 768, got 500" in str(exc_info.value)
