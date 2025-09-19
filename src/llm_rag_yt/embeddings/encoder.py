"""Text embedding using sentence-transformers."""

from typing import Optional

import numpy as np
from loguru import logger

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None  # For type hints when not available
    logger.warning("sentence_transformers not available, using fallback embeddings")


class EmbeddingEncoder:
    """Encodes text into embeddings using sentence-transformers."""

    def __init__(self, model_name: str = "intfloat/multilingual-e5-large-instruct"):
        """Initialize encoder with model name."""
        self.model_name = model_name
        self._model: Optional[SentenceTransformer] = None if SENTENCE_TRANSFORMERS_AVAILABLE else None

    @property
    def model(self):
        """Lazy load embedding model."""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError("sentence_transformers not available")
        if self._model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def _encode_texts(self, texts: list[str]) -> np.ndarray:
        """Encode texts with normalization."""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            # Fallback to simple hash-based embeddings for testing
            logger.warning("Using fallback hash-based embeddings")
            embeddings = []
            for text in texts:
                # Simple hash-based embedding (384 dimensions to match e5-large)
                hash_val = hash(text.encode('utf-8')) % (2**32)
                embedding = np.random.RandomState(hash_val).normal(0, 0.1, 384)
                # Normalize
                embedding = embedding / np.linalg.norm(embedding)
                embeddings.append(embedding)
            return np.array(embeddings)
        
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
