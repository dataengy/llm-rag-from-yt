"""Query rewriting for improved retrieval."""

import re
from typing import List, Dict, Any, Optional, TYPE_CHECKING

from loguru import logger
from openai import OpenAI

if TYPE_CHECKING:
    from ..storage.chroma_store import ChromaVectorStore
    from ..embeddings.encoder import EmbeddingEncoder


class QueryRewriter:
    """Rewrites user queries for better retrieval performance."""

    def __init__(self, model_name: str = "gpt-4o-mini"):
        """Initialize query rewriter."""
        self.model_name = model_name
        self.client = OpenAI()
        logger.info(f"Initialized query rewriter with {model_name}")

    def rewrite_query(
        self, 
        original_query: str, 
        context_domain: str = "YouTube audio content",
        num_variants: int = 3
    ) -> Dict[str, Any]:
        """Rewrite query for better retrieval.
        
        Args:
            original_query: Original user query
            context_domain: Domain context for rewriting
            num_variants: Number of query variants to generate
            
        Returns:
            Dictionary with original query and variants
        """
        logger.info(f"Rewriting query: {original_query[:50]}...")
        
        # Generate rewritten variants using LLM
        llm_variants = self._generate_llm_variants(original_query, context_domain, num_variants)
        
        # Generate rule-based variants
        rule_variants = self._generate_rule_based_variants(original_query)
        
        # Combine all variants
        all_variants = [original_query] + llm_variants + rule_variants
        
        # Remove duplicates and empty queries
        unique_variants = []
        seen = set()
        for variant in all_variants:
            variant_clean = variant.strip().lower()
            if variant_clean and variant_clean not in seen:
                unique_variants.append(variant.strip())
                seen.add(variant_clean)
        
        result = {
            "original_query": original_query,
            "rewritten_queries": unique_variants[1:],  # Exclude original
            "all_queries": unique_variants,
            "rewriting_strategy": "hybrid_llm_rules"
        }
        
        logger.info(f"Generated {len(result['rewritten_queries'])} query variants")
        return result

    def _generate_llm_variants(
        self, query: str, context_domain: str, num_variants: int
    ) -> List[str]:
        """Generate query variants using LLM."""
        try:
            system_prompt = f"""You are a query expansion expert for {context_domain}.
            Your task is to rewrite the user's query to improve information retrieval.
            
            Generate {num_variants} different variants of the query that:
            1. Preserve the original intent
            2. Use different keywords or phrasing
            3. Add relevant context or specificity
            4. Consider different ways to ask the same question
            
            Return only the rewritten queries, one per line, without numbering or extra text."""
            
            user_prompt = f"Original query: {query}\n\nGenerate {num_variants} improved variants:"
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            content = response.choices[0].message.content
            variants = [line.strip() for line in content.split('\n') if line.strip()]
            
            return variants[:num_variants]
            
        except Exception as e:
            logger.error(f"LLM query rewriting failed: {e}")
            return []

    def _generate_rule_based_variants(self, query: str) -> List[str]:
        """Generate query variants using rule-based methods."""
        variants = []
        
        # 1. Add question words if missing
        variants.extend(self._add_question_words(query))
        
        # 2. Expand with synonyms/related terms
        variants.extend(self._expand_with_synonyms(query))
        
        # 3. Extract key terms
        variants.extend(self._extract_key_terms(query))
        
        # 4. Add domain-specific expansions
        variants.extend(self._add_domain_expansions(query))
        
        return variants[:5]  # Limit rule-based variants

    def _add_question_words(self, query: str) -> List[str]:
        """Add question words to improve specificity."""
        variants = []
        query_lower = query.lower()
        
        # Map of question types to question words
        question_patterns = {
            r'\b(about|про|о)\b': ["What is discussed about", "Tell me about"],
            r'\b(how|как)\b': ["How exactly", "In what way"],
            r'\b(why|почему|зачем)\b': ["What is the reason", "Why specifically"],
            r'\b(when|когда)\b': ["At what time", "When exactly"],
            r'\b(who|кто)\b': ["Which person", "Who specifically"]
        }
        
        for pattern, expansions in question_patterns.items():
            if re.search(pattern, query_lower):
                for expansion in expansions:
                    if not query_lower.startswith(expansion.lower()):
                        variants.append(f"{expansion} {query}")
        
        return variants

    def _expand_with_synonyms(self, query: str) -> List[str]:
        """Expand query with synonyms and related terms."""
        synonyms = {
            "говорить": ["обсуждать", "рассказывать", "упоминать"],
            "видео": ["контент", "запись", "материал"],
            "тема": ["вопрос", "проблема", "аспект"],
            "discuss": ["talk about", "mention", "cover"],
            "video": ["content", "recording", "material"],
            "topic": ["subject", "theme", "issue"]
        }
        
        variants = []
        for original, synonyms_list in synonyms.items():
            if original in query.lower():
                for synonym in synonyms_list:
                    variant = re.sub(
                        r'\b' + re.escape(original) + r'\b',
                        synonym,
                        query,
                        flags=re.IGNORECASE
                    )
                    if variant != query:
                        variants.append(variant)
        
        return variants

    def _extract_key_terms(self, query: str) -> List[str]:
        """Extract key terms from query."""
        # Remove question words and extract key terms
        question_words = r'\b(что|как|где|когда|почему|кто|какой|what|how|where|when|why|who|which)\b'
        
        key_terms = re.sub(question_words, '', query, flags=re.IGNORECASE)
        key_terms = re.sub(r'[^\w\s]', ' ', key_terms)
        key_terms = ' '.join(key_terms.split())
        
        if key_terms.strip() and key_terms.strip() != query.strip():
            return [key_terms.strip()]
        
        return []

    def _add_domain_expansions(self, query: str) -> List[str]:
        """Add domain-specific expansions."""
        expansions = []
        
        # YouTube/video specific terms
        if not any(term in query.lower() for term in ["видео", "видеозапись", "video", "recording"]):
            expansions.append(f"{query} в видео")
            expansions.append(f"в записи {query}")
        
        # Audio content specific
        if not any(term in query.lower() for term in ["говорят", "обсуждают", "mention", "discuss"]):
            expansions.append(f"что говорят про {query}")
            expansions.append(f"обсуждение {query}")
        
        return expansions

    def search_with_rewritten_queries(
        self,
        vector_store: "ChromaVectorStore",
        encoder: "EmbeddingEncoder", 
        original_query: str,
        top_k: int = 10,
        fusion_method: str = "rrf"  # reciprocal rank fusion
    ) -> List[Dict[str, Any]]:
        """Search using rewritten queries and fuse results.
        
        Args:
            vector_store: Vector store instance
            encoder: Embedding encoder
            original_query: Original user query
            top_k: Number of final results
            fusion_method: Method to fuse results ('rrf' or 'weighted')
            
        Returns:
            Fused search results
        """
        # Rewrite query
        rewrite_result = self.rewrite_query(original_query)
        all_queries = rewrite_result["all_queries"]
        
        # Search with each query variant
        all_results = {}
        for i, query_variant in enumerate(all_queries):
            try:
                query_embedding = encoder.embed_query(query_variant)
                results = vector_store.query_similar(query_embedding, top_k * 2)
                all_results[f"query_{i}"] = results
            except Exception as e:
                logger.error(f"Search failed for variant '{query_variant}': {e}")
        
        # Fuse results
        if fusion_method == "rrf":
            fused_results = self._reciprocal_rank_fusion(all_results)
        else:
            fused_results = self._weighted_fusion(all_results)
        
        return fused_results[:top_k]

    def _reciprocal_rank_fusion(
        self, results_dict: Dict[str, List[Dict[str, Any]]], k: int = 60
    ) -> List[Dict[str, Any]]:
        """Fuse results using Reciprocal Rank Fusion."""
        doc_scores = {}
        
        for query_name, results in results_dict.items():
            for rank, doc in enumerate(results, 1):
                doc_id = doc.get("id", f"doc_{rank}")
                rrf_score = 1 / (k + rank)
                
                if doc_id not in doc_scores:
                    doc_scores[doc_id] = {
                        "document": doc,
                        "rrf_score": rrf_score,
                        "appearances": 1
                    }
                else:
                    doc_scores[doc_id]["rrf_score"] += rrf_score
                    doc_scores[doc_id]["appearances"] += 1
        
        # Sort by RRF score
        fused_docs = []
        for doc_id, data in doc_scores.items():
            doc = data["document"].copy()
            doc["rrf_score"] = data["rrf_score"]
            doc["query_appearances"] = data["appearances"]
            fused_docs.append(doc)
        
        fused_docs.sort(key=lambda x: x["rrf_score"], reverse=True)
        return fused_docs

    def _weighted_fusion(
        self, results_dict: Dict[str, List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """Fuse results using weighted averaging."""
        doc_scores = {}
        
        for query_name, results in results_dict.items():
            weight = 1.0 / len(results_dict)  # Equal weight for all queries
            
            for doc in results:
                doc_id = doc.get("id", "unknown")
                similarity = 1 - doc.get("distance", 1)
                
                if doc_id not in doc_scores:
                    doc_scores[doc_id] = {
                        "document": doc,
                        "weighted_score": weight * similarity,
                        "appearances": 1
                    }
                else:
                    doc_scores[doc_id]["weighted_score"] += weight * similarity
                    doc_scores[doc_id]["appearances"] += 1
        
        # Sort by weighted score
        fused_docs = []
        for doc_id, data in doc_scores.items():
            doc = data["document"].copy()
            doc["weighted_score"] = data["weighted_score"]
            doc["query_appearances"] = data["appearances"]
            fused_docs.append(doc)
        
        fused_docs.sort(key=lambda x: x["weighted_score"], reverse=True)
        return fused_docs