import logging
import uuid
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.app.ai.embedding_provider import EmbeddingProvider, get_embedding_provider
from backend.app.core.config import settings
from backend.app.models.attachment import Attachment
from backend.app.models.document_extraction import DocumentExtraction
from backend.app.models.email_message import EmailMessage
from backend.app.models.vector_embedding import VectorEmbedding
from backend.app.utils.chunker import TextChunker

logger = logging.getLogger(__name__)


class VectorSearchService:
    """Service managing text chunking, embedding generation, pgvector storage, and hybrid retrieval."""

    def __init__(self, embedding_provider: EmbeddingProvider | None = None):
        self.provider = embedding_provider or get_embedding_provider()

    def index_email_message(self, db: Session, user_id: uuid.UUID, message_id: uuid.UUID) -> int:
        """Chunk email message body, generate 768-d embeddings with dimension validation, and persist to pgvector."""
        msg = db.query(EmailMessage).filter(EmailMessage.id == message_id, EmailMessage.user_id == user_id).first()
        if not msg or not msg.body_plain:
            return 0

        # Delete existing chunks for this message to prevent duplicates
        db.query(VectorEmbedding).filter(
            VectorEmbedding.email_message_id == message_id,
            VectorEmbedding.user_id == user_id,
        ).delete()

        chunks = TextChunker.chunk_email_message(msg.body_plain)
        if not chunks:
            return 0

        embeddings = self.provider.generate_embeddings(chunks)

        for idx, (chunk_text, vec) in enumerate(zip(chunks, embeddings)):
            db_vec = VectorEmbedding(
                user_id=user_id,
                source_type="EMAIL",
                email_message_id=message_id,
                chunk_index=idx,
                chunk_text=chunk_text,
                embedding=vec,
                embedding_model=settings.EMBEDDING_MODEL,
            )
            db.add(db_vec)

        db.commit()
        return len(chunks)

    def index_document_extraction(self, db: Session, user_id: uuid.UUID, attachment_id: uuid.UUID) -> int:
        """Chunk document extraction, preserve page provenance, generate 768-d embeddings, and persist."""
        extraction = (
            db.query(DocumentExtraction)
            .filter(DocumentExtraction.attachment_id == attachment_id, DocumentExtraction.user_id == user_id)
            .first()
        )
        if not extraction or not extraction.extracted_text:
            return 0

        # Delete existing vector embeddings for this attachment
        db.query(VectorEmbedding).filter(
            VectorEmbedding.attachment_id == attachment_id,
            VectorEmbedding.user_id == user_id,
        ).delete()

        chunks_with_page = TextChunker.chunk_document_extraction(extraction.extracted_text)
        if not chunks_with_page:
            return 0

        texts = [c[0] for c in chunks_with_page]
        embeddings = self.provider.generate_embeddings(texts)

        for idx, ((chunk_text, page_num), vec) in enumerate(zip(chunks_with_page, embeddings)):
            db_vec = VectorEmbedding(
                user_id=user_id,
                source_type="DOCUMENT",
                attachment_id=attachment_id,
                document_extraction_id=extraction.id,
                email_message_id=extraction.email_message_id,
                chunk_index=idx,
                chunk_text=chunk_text,
                page_number=page_num,
                embedding=vec,
                embedding_model=settings.EMBEDDING_MODEL,
            )
            db.add(db_vec)

        db.commit()
        return len(chunks_with_page)

    def semantic_search(
        self,
        db: Session,
        user_id: uuid.UUID,
        query_text: str,
        top_k: int = 5,
        source_type: str | None = None,
    ) -> list[dict]:
        """Perform vector cosine similarity search (<=>) strictly isolated by user_id."""
        query_vec = self.provider.embed_query(query_text)

        # SQLAlchemy pgvector cosine distance operator
        query = db.query(
            VectorEmbedding,
            VectorEmbedding.embedding.cosine_distance(query_vec).label("distance"),
        ).filter(VectorEmbedding.user_id == user_id)

        if source_type:
            query = query.filter(VectorEmbedding.source_type == source_type)

        results = query.order_by(text("distance ASC")).limit(top_k).all()

        formatted_results = []
        for vec_obj, dist in results:
            similarity = max(0.0, 1.0 - float(dist)) if dist is not None else 0.0
            
            # Resolve source metadata
            source_name = "Email"
            if vec_obj.source_type == "DOCUMENT" and vec_obj.attachment:
                source_name = vec_obj.attachment.filename
            elif vec_obj.source_type == "EMAIL" and vec_obj.message:
                source_name = f"Subject: {vec_obj.message.subject or 'No Subject'}"

            formatted_results.append({
                "id": str(vec_obj.id),
                "source_type": vec_obj.source_type,
                "source_name": source_name,
                "email_message_id": str(vec_obj.email_message_id) if vec_obj.email_message_id else None,
                "attachment_id": str(vec_obj.attachment_id) if vec_obj.attachment_id else None,
                "page_number": vec_obj.page_number,
                "chunk_text": vec_obj.chunk_text,
                "similarity_score": round(similarity, 4),
            })

        return formatted_results

    def hybrid_search(
        self,
        db: Session,
        user_id: uuid.UUID,
        query_text: str,
        top_k: int = 5,
    ) -> list[dict]:
        """Perform Hybrid Search using Reciprocal Rank Fusion (RRF) combining vector similarity and keyword search."""
        # 1. Vector Search Candidates
        vector_candidates = self.semantic_search(db, user_id, query_text, top_k=top_k * 2)

        # 2. Simple Keyword / SQL ILIKE Candidates for full text match
        keyword_matches = (
            db.query(VectorEmbedding)
            .filter(
                VectorEmbedding.user_id == user_id,
                VectorEmbedding.chunk_text.ilike(f"%{query_text}%"),
            )
            .limit(top_k * 2)
            .all()
        )

        keyword_candidates = []
        for vec_obj in keyword_matches:
            source_name = "Email"
            if vec_obj.source_type == "DOCUMENT" and vec_obj.attachment:
                source_name = vec_obj.attachment.filename
            elif vec_obj.source_type == "EMAIL" and vec_obj.message:
                source_name = f"Subject: {vec_obj.message.subject or 'No Subject'}"

            keyword_candidates.append({
                "id": str(vec_obj.id),
                "source_type": vec_obj.source_type,
                "source_name": source_name,
                "email_message_id": str(vec_obj.email_message_id) if vec_obj.email_message_id else None,
                "attachment_id": str(vec_obj.attachment_id) if vec_obj.attachment_id else None,
                "page_number": vec_obj.page_number,
                "chunk_text": vec_obj.chunk_text,
                "similarity_score": 0.85,
            })

        # 3. Reciprocal Rank Fusion (RRF) Score Calculation
        rrf_scores: dict[str, float] = {}
        candidate_map: dict[str, dict] = {}
        c_param = 60  # Standard RRF constant

        for rank, item in enumerate(vector_candidates, start=1):
            cid = item["id"]
            candidate_map[cid] = item
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (c_param + rank))

        for rank, item in enumerate(keyword_candidates, start=1):
            cid = item["id"]
            candidate_map[cid] = item
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (c_param + rank))

        # Sort by RRF score descending
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)[:top_k]

        return [candidate_map[cid] for cid in sorted_ids]
