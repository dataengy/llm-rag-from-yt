"""ChromaDB vector storage implementation."""

from pathlib import Path
from typing import Union

import chromadb
from loguru import logger

from ..embeddings.encoder import EmbeddingEncoder


class ChromaVectorStore:
    """Vector storage using ChromaDB."""

    def __init__(self, persist_dir: Union[str, Path], collection_name: str):
        """Initialize ChromaDB client and collection.

        Args:
            persist_dir: Directory for persistent storage
            collection_name: Name of the collection
        """
        self.persist_dir = Path(persist_dir)
        self.collection_name = collection_name
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(path=str(self.persist_dir))
        self.collection = self.client.get_or_create_collection(name=collection_name)

        logger.info(f"Initialized ChromaDB collection: {collection_name}")

    def upsert_chunks(
        self, encoder: EmbeddingEncoder, chunks: list[dict[str, any]]
    ) -> None:
        """Insert or update chunks in the vector store.

        Args:
            encoder: Embedding encoder instance
            chunks: List of chunk dictionaries with id, text, metadata
        """
        if not chunks:
            logger.warning("No chunks to upsert")
            return

        chunk_ids = [chunk["id"] for chunk in chunks]
        texts = [chunk["text"] for chunk in chunks]
        metadatas = [chunk.get("metadata", {}) for chunk in chunks]

        embeddings = encoder.embed_documents(texts)

        self.collection.upsert(
            ids=chunk_ids, embeddings=embeddings, documents=texts, metadatas=metadatas
        )

        logger.info(f"Upserted {len(chunks)} chunks to collection")

    def query_similar(
        self, query_embedding: list[float], top_k: int = 8
    ) -> list[dict[str, any]]:
        """Query for similar documents.

        Args:
            query_embedding: Query embedding vector
            top_k: Number of top results to return

        Returns:
            List of similar documents with metadata
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        documents = []
        for i in range(len(results["ids"][0])):
            doc = {
                "id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
            }
            documents.append(doc)

        logger.debug(f"Retrieved {len(documents)} similar documents")
        return documents

    def get_collection_info(self) -> dict[str, any]:
        """Get information about the collection.

        Returns:
            Collection metadata and count
        """
        count = self.collection.count()
        return {
            "name": self.collection_name,
            "count": count,
            "persist_dir": str(self.persist_dir),
        }
