import uuid
from pydantic import BaseModel, ConfigDict, Field


class SemanticSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Natural language search query")
    top_k: int = Field(default=5, ge=1, le=50, description="Max candidates to return")
    source_type: str | None = Field(default=None, description="Optional filter: EMAIL or DOCUMENT")


class SearchResultItem(BaseModel):
    id: str
    source_type: str
    source_name: str
    email_message_id: str | None = None
    attachment_id: str | None = None
    page_number: int | None = None
    chunk_text: str
    similarity_score: float

    model_config = ConfigDict(from_attributes=True)


class RAGQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Question for grounded RAG synthesis")
    top_k: int = Field(default=5, ge=1, le=20, description="Max context chunks to retrieve")


class CitationItem(BaseModel):
    source_type: str
    source_name: str
    email_message_id: str | None = None
    attachment_id: str | None = None
    page_number: int | None = None
    similarity_score: float


class RAGQueryResponse(BaseModel):
    answer: str
    citations: list[CitationItem]
    retrieved_chunks: list[SearchResultItem]


class ReindexResponse(BaseModel):
    indexed_emails: int
    indexed_documents: int
    total_chunks: int
