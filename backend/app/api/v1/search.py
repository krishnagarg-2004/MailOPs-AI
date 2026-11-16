from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.api.v1.auth import get_current_user
from backend.app.db.session import get_db
from backend.app.models.document_extraction import DocumentExtraction
from backend.app.models.email_message import EmailMessage
from backend.app.models.user import User
from backend.app.schemas.search import (
    RAGQueryRequest,
    RAGQueryResponse,
    ReindexResponse,
    SearchResultItem,
    SemanticSearchRequest,
)
from backend.app.services.rag_service import RAGService
from backend.app.services.vector_search_service import VectorSearchService

router = APIRouter(prefix="/search", tags=["Semantic Search & RAG"])


@router.api_route("/semantic", methods=["GET", "POST"], response_model=list[SearchResultItem])
async def semantic_search(
    req: SemanticSearchRequest | None = None,
    q: str | None = Query(default=None, description="Natural language search query via GET"),
    top_k: int = Query(default=5, ge=1, le=50),
    source_type: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Execute vector cosine similarity search across user emails and document extractions."""
    service = VectorSearchService()
    query_text = (req.query if req else None) or q or ""
    if not query_text:
        return []

    resolved_top_k = (req.top_k if req else None) or top_k
    resolved_source = (req.source_type if req else None) or source_type

    try:
        results = service.semantic_search(
            db=db,
            user_id=current_user.id,
            query_text=query_text,
            top_k=resolved_top_k,
            source_type=resolved_source,
        )
        return results
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Semantic search failed: {exc}",
        )


@router.api_route("/hybrid", methods=["GET", "POST"], response_model=list[SearchResultItem])
async def hybrid_search(
    req: SemanticSearchRequest | None = None,
    q: str | None = Query(default=None, description="Natural language query via GET"),
    top_k: int = Query(default=5, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Execute Hybrid Search combining keyword full-text matching and vector similarity via RRF."""
    service = VectorSearchService()
    query_text = (req.query if req else None) or q or ""
    if not query_text:
        return []

    resolved_top_k = (req.top_k if req else None) or top_k

    try:
        results = service.hybrid_search(
            db=db,
            user_id=current_user.id,
            query_text=query_text,
            top_k=resolved_top_k,
        )
        return results
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Hybrid search failed: {exc}",
        )


@router.post("/rag-query", response_model=RAGQueryResponse)
async def rag_query(
    req: RAGQueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Execute Grounded RAG Query synthesizing AI answer with explicit source and page citations."""
    query_text = req.effective_query
    if not query_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A query or question string must be provided for RAG analysis.",
        )

    service = RAGService()
    try:
        res = service.query_rag(
            db=db,
            user_id=current_user.id,
            query_text=query_text,
            top_k=req.top_k,
        )
        return res
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG query failed: {exc}",
        )


@router.post("/reindex", response_model=ReindexResponse)
async def reindex_all_user_content(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Bulk chunk and re-index all user emails and document extractions into pgvector."""
    service = VectorSearchService()

    messages = db.query(EmailMessage).filter(EmailMessage.user_id == current_user.id).all()
    extractions = db.query(DocumentExtraction).filter(DocumentExtraction.user_id == current_user.id).all()

    indexed_emails = 0
    total_email_chunks = 0
    for msg in messages:
        chunks_count = service.index_email_message(db, current_user.id, msg.id)
        if chunks_count > 0:
            indexed_emails += 1
            total_email_chunks += chunks_count

    indexed_docs = 0
    total_doc_chunks = 0
    for ext in extractions:
        chunks_count = service.index_document_extraction(db, current_user.id, ext.attachment_id)
        if chunks_count > 0:
            indexed_docs += 1
            total_doc_chunks += chunks_count

    return ReindexResponse(
        indexed_emails=indexed_emails,
        indexed_documents=indexed_docs,
        total_chunks=total_email_chunks + total_doc_chunks,
    )
