"""Text processing utilities for normalization and chunking."""

import re

from loguru import logger


class TextProcessor:
    """Handles text normalization and chunking."""

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize text by cleaning whitespace and capitalizing first letter.

        Args:
            text: Raw text to normalize

        Returns:
            Normalized text
        """
        if not text:
            return ""

        normalized = re.sub(r"\s+", " ", text).strip()

        if normalized and not normalized[0].isupper():
            normalized = normalized[0].upper() + normalized[1:]

        return normalized

    @staticmethod
    def split_into_chunks(
        text: str, chunk_size: int = 250, overlap: int = 50
    ) -> list[str]:
        """Split text into overlapping chunks by words.

        Args:
            text: Text to split
            chunk_size: Number of words per chunk
            overlap: Number of overlapping words between chunks

        Returns:
            List of text chunks
        """
        if not text:
            return []

        words = text.split()
        if chunk_size <= 0:
            return [text]

        step = max(1, chunk_size - overlap)
        chunks = []

        for i in range(0, len(words), step):
            chunk_words = words[i : i + chunk_size]
            if chunk_words:
                chunks.append(" ".join(chunk_words))

        logger.debug(
            f"Split text into {len(chunks)} chunks (size={chunk_size}, overlap={overlap})"
        )
        return chunks

    def process_transcriptions(
        self, transcriptions: dict[str, dict], chunk_size: int = 250, overlap: int = 50
    ) -> dict[str, str]:
        """Process and normalize transcriptions.

        Args:
            transcriptions: Dict of transcription results
            chunk_size: Chunk size for splitting
            overlap: Overlap between chunks

        Returns:
            Dict mapping file_id to normalized text
        """
        normalized_texts = {}

        for file_id, transcription in transcriptions.items():
            full_text = transcription.get("full_text", "")
            normalized = self.normalize_text(full_text)
            normalized_texts[file_id] = normalized

            logger.info(f"Normalized text for {file_id}: {len(normalized)} chars")

        return normalized_texts

    def create_chunks(
        self, normalized_texts: dict[str, str], chunk_size: int = 250, overlap: int = 50
    ) -> list[dict[str, any]]:
        """Create chunks from normalized texts.

        Args:
            normalized_texts: Dict of normalized texts
            chunk_size: Words per chunk
            overlap: Overlapping words

        Returns:
            List of chunk dictionaries
        """
        all_chunks = []

        for file_id, text in normalized_texts.items():
            chunks = self.split_into_chunks(text, chunk_size, overlap)

            for i, chunk in enumerate(chunks):
                chunk_data = {
                    "id": f"{file_id}::chunk::{i}",
                    "text": chunk,
                    "metadata": {"source_id": file_id, "chunk_index": i},
                }
                all_chunks.append(chunk_data)

        logger.info(f"Created {len(all_chunks)} chunks total")
        return all_chunks
