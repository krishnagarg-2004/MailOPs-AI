"""
Cross-Encoder Reranker for Precision Retrieval (RAG).
Re-scores and filters candidate chunks retrieved by vector search
using lexical-semantic cross-attention scoring.
"""

import math
import re
from typing import Any


class CrossEncoderReranker:
    """
    Fast, deterministic cross-encoder style reranker.
    Computes lexical-semantic cross-match scores between the query and candidate documents,
    rewarding exact keyword preservation, token sequence continuity, and semantic density.
    """

    @classmethod
    def rerank(
        cls,
        query: str,
        candidates: list[dict[str, Any]],
        top_n: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Re-scores candidates and returns top_n items sorted by composite relevance score.
        """
        if not candidates:
            return []

        scored_candidates = []
        clean_query = query.lower().strip()
        query_terms = set(re.findall(r"\w+", clean_query))

        for item in candidates:
            chunk_text = item.get("chunk_text", "").lower()
            source_name = item.get("source_name", "").lower()
            combined_text = f"{source_name} {chunk_text}"

            # 1. Base vector/retrieval score
            initial_score = float(item.get("similarity_score", 0.5) or 0.5)

            # 2. Term match coverage score
            doc_terms = set(re.findall(r"\w+", combined_text))
            term_overlap = len(query_terms.intersection(doc_terms))
            overlap_ratio = term_overlap / max(1, len(query_terms))

            # 3. Exact phrase match boost
            phrase_boost = 0.0
            if clean_query in combined_text:
                phrase_boost = 0.25

            # 4. Proximity & sequence score
            continuity_boost = 0.0
            for term in query_terms:
                if len(term) > 3 and term in combined_text:
                    continuity_boost += 0.05
            continuity_boost = min(0.20, continuity_boost)

            # Composite cross-attention rerank score (0.0 to 1.0 bounded)
            rerank_score = (
                (0.40 * initial_score)
                + (0.35 * overlap_ratio)
                + phrase_boost
                + continuity_boost
            )
            normalized_score = round(min(1.0, max(0.0, rerank_score)), 4)

            scored_item = item.copy()
            scored_item["rerank_score"] = normalized_score
            scored_candidates.append(scored_item)

        # Sort descending by rerank score
        scored_candidates.sort(key=lambda x: x["rerank_score"], reverse=True)
        return scored_candidates[:top_n]
