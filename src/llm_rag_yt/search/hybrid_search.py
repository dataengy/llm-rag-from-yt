"""Hybrid search combining text and vector search."""

import re
from typing import List, Dict, Any, Optional
from collections import Counter

import numpy as np
from loguru import logger

from ..embeddings.encoder import EmbeddingEncoder
from ..vectorstore.chroma import ChromaVectorStore


class HybridSearchEngine:
    """Hybrid search engine combining text and vector search."""

    def __init__(self, vector_store: ChromaVectorStore, encoder: EmbeddingEncoder):
        """Initialize hybrid search engine."""
        self.vector_store = vector_store
        self.encoder = encoder
        logger.info("Initialized hybrid search engine")

    def search(
        self,
        query: str,
        top_k: int = 10,
        alpha: float = 0.7,  # Weight for vector search vs text search
        text_weight: float = 0.3,
        vector_weight: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Perform hybrid search combining text and vector search.
        
        Args:
            query: Search query
            top_k: Number of results to return
            alpha: Balance between vector (1.0) and text (0.0) search
            text_weight: Weight for text search component
            vector_weight: Weight for vector search component
            
        Returns:
            Ranked list of documents
        """
        logger.info(f"Hybrid search for: {query[:50]}...")
        
        # 1. Vector search
        query_embedding = self.encoder.embed_query(query)
        vector_results = self.vector_store.query_similar(query_embedding, top_k * 2)
        
        # 2. Text search (simple keyword matching)
        text_results = self._text_search(query, top_k * 2)
        
        # 3. Combine and re-rank results
        combined_results = self._combine_results(
            vector_results, text_results, alpha, text_weight, vector_weight
        )
        
        # 4. Take top k results
        final_results = combined_results[:top_k]
        
        logger.info(f"Hybrid search returned {len(final_results)} results")
        return final_results

    def _text_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Perform text-based keyword search."""
        # Get all documents from vector store for text search
        # This is a simplified implementation - in production, use full-text search DB
        all_docs = self.vector_store.query_similar(
            self.encoder.embed_query(""), max_results * 5
        )
        
        # Extract keywords from query
        keywords = self._extract_keywords(query)
        
        # Score documents based on keyword matches
        scored_docs = []
        for doc in all_docs:
            text = doc.get("text", "").lower()
            score = self._calculate_text_score(text, keywords)
            
            if score > 0:  # Only include docs with keyword matches
                doc_copy = doc.copy()
                doc_copy["text_score"] = score
                scored_docs.append(doc_copy)
        
        # Sort by text score
        scored_docs.sort(key=lambda x: x["text_score"], reverse=True)
        
        return scored_docs[:max_results]

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract keywords from query."""
        # Simple keyword extraction - remove common words, punctuation
        stop_words = {
            "что", "как", "где", "когда", "почему", "кто", "какой", "какая", "какие",
            "what", "how", "where", "when", "why", "who", "which", "the", "is", "are",
            "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with"
        }
        
        # Clean and split query
        clean_query = re.sub(r'[^\w\s]', ' ', query.lower())
        words = clean_query.split()
        
        # Filter stop words and short words
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        
        return keywords

    def _calculate_text_score(self, text: str, keywords: List[str]) -> float:
        """Calculate text relevance score based on keyword matches."""
        if not keywords:
            return 0.0
        
        text_lower = text.lower()
        
        # Count keyword occurrences
        keyword_counts = Counter()
        for keyword in keywords:
            # Exact matches
            exact_count = text_lower.count(keyword)
            keyword_counts[keyword] += exact_count
            
            # Partial matches (substring)
            for word in text_lower.split():
                if keyword in word and len(word) > len(keyword):
                    keyword_counts[keyword] += 0.5
        
        # Calculate score
        total_matches = sum(keyword_counts.values())
        unique_matches = len([k for k, v in keyword_counts.items() if v > 0])
        
        # Score based on match density and coverage
        match_density = total_matches / len(text.split()) if text.split() else 0
        keyword_coverage = unique_matches / len(keywords) if keywords else 0
        
        return match_density * keyword_coverage

    def _combine_results(
        self,
        vector_results: List[Dict[str, Any]],
        text_results: List[Dict[str, Any]],
        alpha: float,
        text_weight: float,
        vector_weight: float
    ) -> List[Dict[str, Any]]:
        """Combine and re-rank vector and text search results."""
        # Create document index
        doc_scores = {}
        
        # Process vector results
        for i, doc in enumerate(vector_results):
            doc_id = doc.get("id", f"doc_{i}")
            vector_score = 1 - doc.get("distance", 1)  # Convert distance to similarity
            
            if doc_id not in doc_scores:
                doc_scores[doc_id] = {
                    "document": doc,
                    "vector_score": vector_score,
                    "text_score": 0.0,
                    "vector_rank": i + 1,
                    "text_rank": float('inf')
                }
            else:
                doc_scores[doc_id]["vector_score"] = max(
                    doc_scores[doc_id]["vector_score"], vector_score
                )

        # Process text results
        for i, doc in enumerate(text_results):
            doc_id = doc.get("id", f"doc_{i}")
            text_score = doc.get("text_score", 0.0)
            
            if doc_id not in doc_scores:
                doc_scores[doc_id] = {
                    "document": doc,
                    "vector_score": 0.0,
                    "text_score": text_score,
                    "vector_rank": float('inf'),
                    "text_rank": i + 1
                }
            else:
                doc_scores[doc_id]["text_score"] = max(
                    doc_scores[doc_id]["text_score"], text_score
                )
                doc_scores[doc_id]["text_rank"] = i + 1

        # Calculate hybrid scores
        combined_docs = []
        for doc_id, scores in doc_scores.items():
            # Normalize scores
            vector_score = scores["vector_score"]
            text_score = scores["text_score"]
            
            # Combine scores
            hybrid_score = (vector_weight * vector_score) + (text_weight * text_score)
            
            # Add rank-based bonus for documents found by both methods
            if scores["vector_rank"] != float('inf') and scores["text_rank"] != float('inf'):
                hybrid_score += 0.1  # Bonus for appearing in both searches
            
            doc = scores["document"].copy()
            doc["hybrid_score"] = hybrid_score
            doc["vector_score"] = vector_score
            doc["text_score"] = text_score
            doc["search_method"] = self._get_search_method(scores)
            
            combined_docs.append(doc)

        # Sort by hybrid score
        combined_docs.sort(key=lambda x: x["hybrid_score"], reverse=True)
        
        return combined_docs

    def _get_search_method(self, scores: Dict[str, Any]) -> str:
        """Determine which search method found the document."""
        has_vector = scores["vector_rank"] != float('inf')
        has_text = scores["text_rank"] != float('inf')
        
        if has_vector and has_text:
            return "both"
        elif has_vector:
            return "vector"
        elif has_text:
            return "text"
        else:
            return "unknown"

    def search_with_reranking(
        self,
        query: str,
        top_k: int = 10,
        rerank_top_n: int = 50
    ) -> List[Dict[str, Any]]:
        """Hybrid search with document re-ranking."""
        # First pass: get more results for re-ranking
        initial_results = self.search(query, top_k=rerank_top_n)
        
        # Re-rank using query-document similarity
        reranked_results = self._rerank_documents(query, initial_results)
        
        # Return top k after re-ranking
        return reranked_results[:top_k]

    def _rerank_documents(
        self, query: str, documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Re-rank documents using cross-encoder or similarity metrics."""
        # Simple re-ranking using query-document semantic similarity
        query_words = set(self._extract_keywords(query))
        
        for doc in documents:
            text = doc.get("text", "")
            doc_words = set(self._extract_keywords(text))
            
            # Calculate word overlap
            word_overlap = len(query_words.intersection(doc_words))
            overlap_score = word_overlap / max(len(query_words), 1)
            
            # Calculate length penalty (prefer medium-length chunks)
            text_length = len(text.split())
            length_penalty = 1.0
            if text_length < 50:  # Too short
                length_penalty = 0.8
            elif text_length > 300:  # Too long
                length_penalty = 0.9
            
            # Combine scores
            rerank_score = (
                doc.get("hybrid_score", 0) * 0.7 +
                overlap_score * 0.2 +
                length_penalty * 0.1
            )
            
            doc["rerank_score"] = rerank_score
        
        # Sort by re-ranking score
        documents.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)
        
        return documents