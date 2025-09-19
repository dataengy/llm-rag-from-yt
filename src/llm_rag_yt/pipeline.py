"""Main RAG pipeline orchestrator."""

import json
from typing import Optional

from ._common.config.settings import Config, get_config
from ._common.logging import log
from .audio.downloader import YouTubeDownloader
from .audio.transcriber import AudioTranscriber
from .embeddings.encoder import EmbeddingEncoder
from .rag.query_engine import RAGQueryEngine
from .text.processor import TextProcessor
from .vectorstore.chroma import ChromaVectorStore


class RAGPipeline:
    """Main RAG pipeline orchestrator."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize pipeline with configuration."""
        self.config = config or get_config()

        self.downloader = YouTubeDownloader(self.config.input_dir)
        self.transcriber = AudioTranscriber(
            model_name=self.config.asr_model,
            device=self.config.device,
            compute_type=self.config.whisper_precision,
        )
        self.text_processor = TextProcessor()
        self.encoder = EmbeddingEncoder(self.config.embedding_model)
        self.vector_store = ChromaVectorStore(
            self.config.persist_dir, self.config.collection_name
        )
        self.query_engine = RAGQueryEngine(
            self.vector_store,
            self.encoder,
            model_name=self.config.openai_model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
        )

        log.bind(component="pipeline").info("ℹ️ Initialized RAG pipeline")

    def download_and_process(self, urls: list[str]) -> dict[str, dict]:
        """Download YouTube videos and process through full pipeline.

        Args:
            urls: List of YouTube URLs

        Returns:
            Processing results
        """
        log.bind(component="pipeline", urls_count=len(urls)).info(
            f"🚀 Starting pipeline for {len(urls)} URLs"
        )

        download_results = self.downloader.download_multiple(urls)
        if not download_results:
            logger.warning("No successful downloads")
            return {}

        transcription_results = self.transcriber.transcribe_directory(
            self.config.input_dir,
            language="ru",
            beam_size=self.config.beam_size,
            use_vad=self.config.use_vad,
            use_fake=self.config.use_fake_asr,
        )

        self._save_artifacts("asr", transcription_results)

        normalized_texts = self.text_processor.process_transcriptions(
            transcription_results, self.config.chunk_size, self.config.chunk_overlap
        )

        self._save_artifacts("normalized", {"normalized_texts": normalized_texts})

        chunks = self.text_processor.create_chunks(
            normalized_texts, self.config.chunk_size, self.config.chunk_overlap
        )

        self.vector_store.upsert_chunks(self.encoder, chunks)

        logger.info("Pipeline processing completed")
        return {
            "downloads": download_results,
            "transcriptions": transcription_results,
            "normalized_texts": normalized_texts,
            "chunks": len(chunks),
        }

    def query(self, question: str, top_k: Optional[int] = None) -> dict[str, any]:
        """Query the RAG system.

        Args:
            question: User question
            top_k: Number of top results (defaults to config)

        Returns:
            Query result with answer and sources
        """
        top_k = top_k or self.config.top_k
        return self.query_engine.query(question, top_k)

    def _save_artifacts(self, artifact_type: str, data: dict) -> None:
        """Save processing artifacts to disk.

        Args:
            artifact_type: Type of artifact (asr, normalized, etc.)
            data: Data to save
        """
        artifact_dir = self.config.artifacts_dir / artifact_type
        artifact_dir.mkdir(parents=True, exist_ok=True)

        if artifact_type == "asr":
            for file_id, payload in data.items():
                file_path = artifact_dir / f"{file_id}.json"
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(payload, f, ensure_ascii=False, indent=2)
        else:
            file_path = artifact_dir / f"{artifact_type}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        logger.debug(f"Saved {artifact_type} artifacts")

    def get_status(self) -> dict[str, any]:
        """Get pipeline status information.

        Returns:
            Status information
        """
        collection_info = self.vector_store.get_collection_info()

        return {
            "config": self.config,
            "collection": collection_info,
            "artifacts_dir": str(self.config.artifacts_dir),
            "input_dir": str(self.config.input_dir),
        }
