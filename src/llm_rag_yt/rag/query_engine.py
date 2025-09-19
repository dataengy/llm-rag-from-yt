"""RAG query engine using OpenAI."""

import os
import time
from typing import Optional

from loguru import logger
from openai import OpenAI

from ..embeddings.encoder import EmbeddingEncoder
from ..search.hybrid_search import HybridSearchEngine
from ..search.query_rewriter import QueryRewriter
from ..vectorstore.chroma import ChromaVectorStore


class RAGQueryEngine:
    """RAG query engine for question answering."""

    def __init__(
        self,
        vector_store: ChromaVectorStore,
        encoder: EmbeddingEncoder,
        model_name: str = "gpt-4o",
        max_tokens: int = 256,
        temperature: float = 0.3,
        enable_hybrid_search: bool = True,
        enable_query_rewriting: bool = True,
        enable_reranking: bool = True,
    ):
        """Initialize RAG query engine.

        Args:
            vector_store: Vector storage instance
            encoder: Embedding encoder instance
            model_name: OpenAI model name
            max_tokens: Maximum tokens for response
            temperature: Temperature for generation
            enable_hybrid_search: Enable hybrid search capabilities
            enable_query_rewriting: Enable query rewriting
            enable_reranking: Enable document re-ranking
        """
        self.vector_store = vector_store
        self.encoder = encoder
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature

        self._validate_openai_key()
        self.client = OpenAI()

        # Initialize advanced search components
        self.hybrid_search = (
            HybridSearchEngine(vector_store, encoder) if enable_hybrid_search else None
        )
        self.query_rewriter = (
            QueryRewriter(model_name="gpt-4o-mini") if enable_query_rewriting else None
        )
        self.enable_reranking = enable_reranking

        logger.info(f"Initialized RAG engine with {model_name}")
        logger.info(
            f"Advanced features - Hybrid: {enable_hybrid_search}, Rewriting: {enable_query_rewriting}, Reranking: {enable_reranking}"
        )

    def _validate_openai_key(self) -> None:
        """Validate OpenAI API key is available."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable required. "
                "Set it in .env file or environment."
            )

    def query(
        self,
        question: str,
        top_k: int = 3,
        system_prompt: Optional[str] = None,
        use_advanced_search: bool = True,
    ) -> dict[str, any]:
        """Query the RAG system with optional advanced features.

        Args:
            question: User question
            top_k: Number of similar documents to retrieve
            system_prompt: Custom system prompt
            use_advanced_search: Whether to use hybrid search and query rewriting

        Returns:
            Dict with answer and sources
        """
        start_time = time.time()

        if system_prompt is None:
            system_prompt = (
                "Отвечай только на основе контекста. "
                "Если ответа нет — скажи, что не знаешь."
            )

        # Use advanced search if enabled
        if use_advanced_search and self.query_rewriter and self.hybrid_search:
            similar_docs = self._advanced_retrieval(question, top_k)
        else:
            # Standard vector search
            query_embedding = self.encoder.embed_query(question)
            similar_docs = self.vector_store.query_similar(query_embedding, top_k)

        context = "\n".join(
            f"{i + 1}. {doc['text']}" for i, doc in enumerate(similar_docs)
        )

        user_prompt = f"Вопрос: {question}\n\nКонтекст:\n{context}"

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            answer = response.choices[0].message.content
            response_time = time.time() - start_time

            logger.info(
                f"Generated answer for question: {question[:50]}... (took {response_time:.2f}s)"
            )

            return {
                "question": question,
                "answer": answer,
                "sources": similar_docs,
                "context": context,
                "response_time": response_time,
                "search_method": "advanced" if use_advanced_search else "standard",
            }

        except Exception as e:
            logger.error(f"Failed to generate answer: {e}")
            raise

    def _advanced_retrieval(self, question: str, top_k: int) -> list[dict[str, any]]:
        """Perform advanced retrieval using hybrid search and query rewriting."""
        if self.query_rewriter:
            # Use query rewriting with result fusion
            similar_docs = self.query_rewriter.search_with_rewritten_queries(
                self.vector_store, self.encoder, question, top_k * 2
            )
        else:
            # Use hybrid search only
            similar_docs = self.hybrid_search.search(question, top_k * 2)

        # Apply re-ranking if enabled
        if self.enable_reranking and self.hybrid_search:
            similar_docs = self.hybrid_search._rerank_documents(question, similar_docs)

        return similar_docs[:top_k]

    def batch_query(self, questions: list[str], top_k: int = 3) -> list[dict[str, any]]:
        """Process multiple questions.

        Args:
            questions: List of questions
            top_k: Number of sources per question

        Returns:
            List of query results
        """
        results = []
        for question in questions:
            try:
                result = self.query(question, top_k)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process question '{question}': {e}")
                results.append(
                    {
                        "question": question,
                        "answer": f"Error: {str(e)}",
                        "sources": [],
                        "context": "",
                    }
                )

        return results
