from fastapi import APIRouter, Depends, HTTPException, status
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


@router.post("/semantic", response_model=list[SearchResultItem])
async def semantic_search(
    req: SemanticSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Execute vector cosine similarity search across user emails and document extractions."""
    service = VectorSearchService()
    try:
        results = service.semantic_search(
            db=db,
            user_id=current_user.id,
            query_text=req.query,
            top_k=req.top_k,
            source_type=req.source_type,
        )
        return results
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Semantic search failed: {exc}",
        )


@router.post("/hybrid", response_model=list[SearchResultItem])
async def hybrid_search(
    req: SemanticSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Execute Hybrid Search combining keyword full-text matching and vector similarity via RRF."""
    service = VectorSearchService()
    try:
        results = service.hybrid_search(
            db=db,
            user_id=current_user.id,
            query_text=req.query,
            top_k=req.top_k,
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
    service = RAGService()
    try:
        res = service.query_rag(
            db=db,
            user_id=current_user.id,
            query_text=req.query,
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
