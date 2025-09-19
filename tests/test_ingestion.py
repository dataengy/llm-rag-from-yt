"""Tests for ingestion pipeline."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from llm_rag_yt.ingestion.automated_pipeline import (
    AutomatedIngestionPipeline,
    IngestionJob,
)


class TestIngestionJob:
    """Test ingestion job dataclass."""

    def test_job_creation(self):
        """Test job creation with defaults."""
        urls = [
            "https://youtube.com/watch?v=test1",
            "https://youtube.com/watch?v=test2",
        ]
        job = IngestionJob(id="test_job", urls=urls)

        assert job.id == "test_job"
        assert job.urls == urls
        assert job.status == "pending"
        assert job.created_at  # Should be auto-generated

    def test_job_with_custom_fields(self):
        """Test job with custom timestamp and status."""
        job = IngestionJob(
            id="test_job",
            urls=["https://youtube.com/watch?v=test"],
            status="running",
            created_at="2025-01-19T10:00:00",
        )

        assert job.status == "running"
        assert job.created_at == "2025-01-19T10:00:00"


class TestAutomatedIngestionPipeline:
    """Test automated ingestion pipeline."""

    @pytest.fixture
    def temp_config(self):
        """Create temporary config."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_config = Mock()
            mock_config.artifacts_dir = Path(temp_dir)
            yield mock_config

    @patch("llm_rag_yt.ingestion.automated_pipeline.RAGPipeline")
    def test_pipeline_initialization(self, mock_rag_pipeline, temp_config):
        """Test pipeline initialization."""
        pipeline = AutomatedIngestionPipeline(temp_config)
        assert pipeline.config == temp_config
        assert pipeline.jobs == {}

    @patch("llm_rag_yt.ingestion.automated_pipeline.RAGPipeline")
    def test_add_job(self, mock_rag_pipeline, temp_config):
        """Test adding ingestion job."""
        pipeline = AutomatedIngestionPipeline(temp_config)

        urls = [
            "https://youtube.com/watch?v=test1",
            "https://youtube.com/watch?v=test2",
        ]
        job_id = pipeline.add_job(urls)

        assert job_id.startswith("job_")
        assert job_id in pipeline.jobs
        assert pipeline.jobs[job_id].urls == urls
        assert pipeline.jobs[job_id].status == "pending"

    @patch("llm_rag_yt.ingestion.automated_pipeline.RAGPipeline")
    def test_pipeline_stats(self, mock_rag_pipeline, temp_config):
        """Test pipeline statistics."""
        # Mock vector store
        mock_rag_pipeline.return_value.vector_store.get_collection_info.return_value = {
            "count": 100
        }

        pipeline = AutomatedIngestionPipeline(temp_config)

        # Add some test jobs
        pipeline.add_job(["url1", "url2"])
        job_id2 = pipeline.add_job(["url3"])

        # Simulate job completion
        pipeline.jobs[job_id2].status = "completed"

        stats = pipeline.get_pipeline_stats()

        assert stats["total_jobs"] == 2
        assert stats["completed_jobs"] == 1
        assert stats["pending_jobs"] == 1
        assert stats["total_urls_processed"] == 3
        assert stats["collection_size"] == 100

    @patch("llm_rag_yt.ingestion.automated_pipeline.RAGPipeline")
    def test_job_execution_success(self, mock_rag_pipeline, temp_config):
        """Test successful job execution."""
        # Mock successful pipeline execution
        mock_pipeline_instance = mock_rag_pipeline.return_value
        mock_pipeline_instance.download_and_process.return_value = {
            "downloads": {"url1": "success"},
            "transcriptions": {"url1": "transcript"},
            "chunks": 10,
        }

        pipeline = AutomatedIngestionPipeline(temp_config)
        job_id = pipeline.add_job(["https://youtube.com/watch?v=test"])

        result = pipeline.run_job(job_id)

        assert result["status"] == "completed"
        assert "results" in result
        assert pipeline.jobs[job_id].status == "completed"
        assert pipeline.jobs[job_id].completed_at is not None

    @patch("llm_rag_yt.ingestion.automated_pipeline.RAGPipeline")
    def test_job_execution_failure(self, mock_rag_pipeline, temp_config):
        """Test job execution failure handling."""
        # Mock pipeline failure
        mock_pipeline_instance = mock_rag_pipeline.return_value
        mock_pipeline_instance.download_and_process.side_effect = Exception(
            "Test error"
        )

        pipeline = AutomatedIngestionPipeline(temp_config)
        job_id = pipeline.add_job(["https://youtube.com/watch?v=test"])

        result = pipeline.run_job(job_id)

        assert result["status"] == "failed"
        assert "error" in result
        assert pipeline.jobs[job_id].status == "failed"
        assert pipeline.jobs[job_id].error_message == "Test error"
