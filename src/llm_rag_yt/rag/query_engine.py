"""RAG query engine using OpenAI."""

import os
from typing import Optional

from loguru import logger
from openai import OpenAI

from ..embeddings.encoder import EmbeddingEncoder
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
    ):
        """Initialize RAG query engine.

        Args:
            vector_store: Vector storage instance
            encoder: Embedding encoder instance
            model_name: OpenAI model name
            max_tokens: Maximum tokens for response
            temperature: Temperature for generation
        """
        self.vector_store = vector_store
        self.encoder = encoder
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature

        self._validate_openai_key()
        self.client = OpenAI()

        logger.info(f"Initialized RAG engine with {model_name}")

    def _validate_openai_key(self) -> None:
        """Validate OpenAI API key is available."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable required. "
                "Set it in .env file or environment."
            )

    def query(
        self, question: str, top_k: int = 3, system_prompt: Optional[str] = None
    ) -> dict[str, any]:
        """Query the RAG system.

        Args:
            question: User question
            top_k: Number of similar documents to retrieve
            system_prompt: Custom system prompt

        Returns:
            Dict with answer and sources
        """
        if system_prompt is None:
            system_prompt = (
                "Отвечай только на основе контекста. "
                "Если ответа нет — скажи, что не знаешь."
            )

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

            logger.info(f"Generated answer for question: {question[:50]}...")

            return {
                "question": question,
                "answer": answer,
                "sources": similar_docs,
                "context": context,
            }

        except Exception as e:
            logger.error(f"Failed to generate answer: {e}")
            raise

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
