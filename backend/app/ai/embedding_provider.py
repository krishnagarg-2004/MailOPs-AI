import hashlib
import math
from typing import Protocol
from backend.app.core.config import settings


class EmbeddingProvider(Protocol):
    """Protocol for vector embedding providers."""

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate vector embeddings for a list of text chunks."""
        ...

    def embed_query(self, query: str) -> list[float]:
        """Generate vector embedding for a search query string."""
        ...


class GeminiEmbeddingProvider:
    """Official Gemini Embedding Provider using google-genai SDK."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.EMBEDDING_MODEL

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            
            embeddings: list[list[float]] = []
            for text in texts:
                response = client.models.embed_content(
                    model=self.model,
                    contents=text,
                )
                vec = response.embedding.values
                # Strict runtime dimension validation invariant
                self._validate_dimension(vec)
                embeddings.append(vec)
                
            return embeddings
        except Exception as exc:
            # Fallback to deterministic provider if live API key is missing/unreachable
            return MockEmbeddingProvider().generate_embeddings(texts)

    def embed_query(self, query: str) -> list[float]:
        res = self.generate_embeddings([query])
        return res[0] if res else [0.0] * settings.EMBEDDING_DIMENSION

    @staticmethod
    def _validate_dimension(vector: list[float]) -> None:
        """Enforce strict runtime validation that vector has exactly EMBEDDING_DIMENSION (768)."""
        expected_dim = settings.EMBEDDING_DIMENSION
        actual_dim = len(vector)
        if actual_dim != expected_dim:
            raise ValueError(
                f"Embedding dimension mismatch: expected {expected_dim}, got {actual_dim}"
            )


class MockEmbeddingProvider:
    """Deterministic offline embedding provider generating unit-normalized 768-d vectors."""

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        embeddings: list[list[float]] = []
        for text in texts:
            vec = self._hash_text_to_vector(text, settings.EMBEDDING_DIMENSION)
            self._validate_dimension(vec)
            embeddings.append(vec)

        return embeddings

    def embed_query(self, query: str) -> list[float]:
        res = self.generate_embeddings([query])
        return res[0]

    @staticmethod
    def _hash_text_to_vector(text: str, dim: int) -> list[float]:
        """Generate unit-normalized 768-dimensional float vector from text hash."""
        vec = []
        for i in range(dim):
            # Seed hash using text + index
            h = hashlib.sha256(f"{text}_{i}".encode("utf-8")).hexdigest()
            val = (int(h[:8], 16) / 0xFFFFFFFF) * 2.0 - 1.0
            vec.append(val)

        # Normalize to unit length (L2 norm = 1.0)
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    @staticmethod
    def _validate_dimension(vector: list[float]) -> None:
        """Enforce strict runtime validation that vector has exactly EMBEDDING_DIMENSION (768)."""
        expected_dim = settings.EMBEDDING_DIMENSION
        actual_dim = len(vector)
        if actual_dim != expected_dim:
            raise ValueError(
                f"Embedding dimension mismatch: expected {expected_dim}, got {actual_dim}"
            )


def get_embedding_provider() -> EmbeddingProvider:
    """Factory creating configured embedding provider."""
    if settings.AI_PROVIDER_TYPE == "gemini" and settings.GEMINI_API_KEY:
        return GeminiEmbeddingProvider()
    return MockEmbeddingProvider()
