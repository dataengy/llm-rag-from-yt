"""Text embedding using sentence-transformers."""

from typing import Optional

import numpy as np
from loguru import logger
from sentence_transformers import SentenceTransformer


class EmbeddingEncoder:
    """Encodes text into embeddings using sentence-transformers."""

    def __init__(self, model_name: str = "intfloat/multilingual-e5-large-instruct"):
        """Initialize encoder with model name."""
        self.model_name = model_name
        self._model: Optional[SentenceTransformer] = None

    @property
    def model(self) -> SentenceTransformer:
        """Lazy load embedding model."""
        if self._model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def _encode_texts(self, texts: list[str]) -> np.ndarray:
        """Encode texts with normalization."""
        return self.model.encode(
            texts, normalize_embeddings=True, show_progress_bar=False
        )

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed documents with passage prefix.

        Args:
            texts: List of document texts

        Returns:
            List of embedding vectors
        """
        prefixed_texts = [f"passage: {text}" for text in texts]
        embeddings = self._encode_texts(prefixed_texts)

        logger.debug(f"Embedded {len(texts)} documents")
        return embeddings.tolist()

    def embed_query(self, query: str) -> list[float]:
        """Embed query with query prefix.

        Args:
            query: Query text

        Returns:
            Query embedding vector
        """
        prefixed_query = f"query: {query}"
        embedding = self._encode_texts([prefixed_query])[0]

        logger.debug(f"Embedded query: {query[:50]}...")
        return embedding.tolist()
