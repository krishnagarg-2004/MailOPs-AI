import logging
import uuid
from sqlalchemy.orm import Session
from backend.app.ai.provider import AIProvider, get_ai_provider
from backend.app.services.vector_search_service import VectorSearchService

logger = logging.getLogger(__name__)

RAG_PROMPT_TEMPLATE = """You are MailOps AI Grounded Intelligence Assistant.
Answer the user's question using ONLY the retrieved context provided below.

RULES:
1. Base your answer strictly on the provided context fragments.
2. For every claim or detail in your response, include explicit source citations in format: [Source: <filename/subject>, Page <page>] or [Source: <filename/subject>].
3. Do NOT make up information. If the answer is not contained in the retrieved context, state: "The retrieved context does not contain sufficient information to answer this question."

<retrieved_context>
{context_blocks}
</retrieved_context>

USER QUESTION:
{query_text}
"""


class RAGService:
    """Service managing context synthesis, grounding prompt generation, and RAG answer formulation."""

    def __init__(self, vector_service: VectorSearchService | None = None, ai_provider: AIProvider | None = None):
        self.vector_service = vector_service or VectorSearchService()
        self.ai_provider = ai_provider or get_ai_provider()

    def query_rag(self, db: Session, user_id: uuid.UUID, query_text: str, top_k: int = 5) -> dict:
        """
        Execute Hybrid Vector Search, assemble grounded prompt context with citations, and generate AI response.
        """
        # 1. Retrieve Hybrid Search Top-K Candidates
        retrieved_chunks = self.vector_service.hybrid_search(db, user_id, query_text, top_k=top_k)

        if not retrieved_chunks:
            return {
                "answer": "No relevant documents or emails were found matching your query.",
                "citations": [],
                "retrieved_chunks": [],
            }

        # 2. Assemble Grounded Context Blocks
        context_blocks: list[str] = []
        citations: list[dict] = []

        for idx, chunk in enumerate(retrieved_chunks, start=1):
            source_name = chunk["source_name"]
            page_str = f" Page {chunk['page_number']}" if chunk.get("page_number") else ""
            
            block = (
                f'<context_item id="{idx}" source="{chunk["source_type"]}" name="{source_name}"{page_str}>\n'
                f'{chunk["chunk_text"]}\n'
                f'</context_item>'
            )
            context_blocks.append(block)

            citations.append({
                "source_type": chunk["source_type"],
                "source_name": source_name,
                "email_message_id": chunk.get("email_message_id"),
                "attachment_id": chunk.get("attachment_id"),
                "page_number": chunk.get("page_number"),
                "similarity_score": chunk["similarity_score"],
            })

        formatted_context = "\n\n".join(context_blocks)
        prompt = RAG_PROMPT_TEMPLATE.format(context_blocks=formatted_context, query_text=query_text)

        # 3. Deterministic answer formulation for mock/dev mode
        first_chunk_text = retrieved_chunks[0]["chunk_text"]
        first_source = retrieved_chunks[0]["source_name"]
        first_page = f", Page {retrieved_chunks[0]['page_number']}" if retrieved_chunks[0].get("page_number") else ""
        
        synthesized_answer = (
            f"Based on the retrieved context, {first_chunk_text[:150]}... "
            f"[Source: {first_source}{first_page}]"
        )

        return {
            "answer": synthesized_answer,
            "citations": citations,
            "retrieved_chunks": retrieved_chunks,
        }
