"""
Tests for Dagster pipeline functionality.
"""

from unittest.mock import Mock, patch

import pandas as pd
import pytest
from dagster import build_asset_context

from llm_rag_yt.dagster.assets import (
    pipeline_metrics,
    system_alerts,
    unprocessed_audio_files,
    youtube_urls_to_process,
)
from llm_rag_yt.dagster.jobs import (
    cleanup_old_files,
    health_check,
    pipeline_metrics_op,
    send_telegram_alerts,
    system_alerts_op,
)
from llm_rag_yt.dagster.sensors import (
    audio_file_sensor,
    pipeline_health_sensor,
    youtube_url_sensor,
)
from llm_rag_yt.telegram.database import TelegramDatabase


@pytest.fixture
def mock_database():
    """Mock TelegramDatabase for testing."""
    db = Mock(spec=TelegramDatabase)
    return db


@pytest.fixture
def sample_youtube_requests():
    """Sample YouTube requests data."""
    return [
        {
            "id": 1,
            "user_id": 12345,
            "url": "https://youtube.com/watch?v=abc123",
            "status": "pending",
            "created_at": "2025-01-19T10:00:00",
        },
        {
            "id": 2,
            "user_id": 67890,
            "url": "https://youtube.com/watch?v=def456",
            "status": "pending",
            "created_at": "2025-01-19T10:05:00",
        },
    ]


@pytest.fixture
def sample_audio_files():
    """Sample audio files data."""
    return [
        {
            "id": 1,
            "file_path": "/data/audio/file1.mp3",
            "file_size": 1024,
            "processing_status": "pending",
            "created_at": "2025-01-19T10:00:00",
        },
        {
            "id": 2,
            "file_path": "/data/audio/file2.mp3",
            "file_size": 2048,
            "processing_status": "pending",
            "created_at": "2025-01-19T10:05:00",
        },
    ]


class TestDagsterAssets:
    """Test Dagster assets functionality."""

    @patch("llm_rag_yt.dagster.assets.TelegramDatabase")
    def test_youtube_urls_to_process_asset(
        self, mock_db_class, sample_youtube_requests
    ):
        """Test youtube_urls_to_process asset."""
        # Setup mock
        mock_db = Mock()
        mock_db.get_pending_youtube_requests.return_value = sample_youtube_requests
        mock_db_class.return_value = mock_db

        # Build context and materialize asset
        context = build_asset_context()
        result = youtube_urls_to_process(context)

        # Verify result
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert "id" in result.columns
        assert "user_id" in result.columns
        assert "url" in result.columns

        # Verify mock was called
        mock_db.get_pending_youtube_requests.assert_called_once()

    @patch("llm_rag_yt.dagster.assets.TelegramDatabase")
    def test_youtube_urls_to_process_empty(self, mock_db_class):
        """Test youtube_urls_to_process asset with no pending requests."""
        # Setup mock
        mock_db = Mock()
        mock_db.get_pending_youtube_requests.return_value = []
        mock_db_class.return_value = mock_db

        # Build context and materialize asset
        context = build_asset_context()
        result = youtube_urls_to_process(context)

        # Verify empty result
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0
        assert list(result.columns) == ["id", "user_id", "url", "created_at"]

    @patch("llm_rag_yt.dagster.assets.TelegramDatabase")
    def test_unprocessed_audio_files_asset(self, mock_db_class, sample_audio_files):
        """Test unprocessed_audio_files asset."""
        # Setup mock
        mock_db = Mock()
        mock_db.get_unprocessed_audio_files.return_value = sample_audio_files
        mock_db_class.return_value = mock_db

        # Build context and materialize asset
        context = build_asset_context()
        result = unprocessed_audio_files(context)

        # Verify result
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert "file_path" in result.columns
        assert "file_size" in result.columns

        # Verify mock was called
        mock_db.get_unprocessed_audio_files.assert_called_once()

    @patch("llm_rag_yt.dagster.assets.TelegramDatabase")
    def test_pipeline_metrics_asset(self, mock_db_class):
        """Test pipeline_metrics asset."""
        # Setup mocks
        mock_db = Mock()
        mock_db.get_processing_stats.return_value = {
            "youtube_requests": {"pending": 5, "completed": 10},
            "audio_files": {"pending": 3, "completed": 8},
        }
        mock_db.get_user_stats.return_value = {
            "total_queries": 100,
            "unique_users": 15,
            "avg_response_time_ms": 500,
        }
        mock_db_class.return_value = mock_db

        # Mock filesystem
        with patch("llm_rag_yt.dagster.assets.Path") as mock_path:
            mock_audio_dir = Mock()
            mock_audio_dir.exists.return_value = True
            mock_audio_dir.glob.return_value = [Mock() for _ in range(5)]  # 5 files
            mock_path.return_value = mock_audio_dir

            # Build context and materialize asset
            context = build_asset_context()
            result = pipeline_metrics(context)

            # Verify result
            assert isinstance(result, dict)
            assert "timestamp" in result
            assert "processing_stats" in result
            assert "user_stats" in result
            assert "filesystem" in result

    @patch("llm_rag_yt.dagster.assets.TelegramDatabase")
    def test_system_alerts_asset(self, mock_db_class):
        """Test system_alerts asset."""
        # Setup mock pipeline metrics
        pipeline_metrics_data = {
            "processing_stats": {
                "youtube_requests": {"failed": 10},  # Above threshold
                "audio_files": {"failed": 5},  # Above threshold
                "pipeline_jobs": {"pending": 15},  # Above threshold
            }
        }

        # Setup mock database
        mock_db = Mock()
        mock_db_class.return_value = mock_db

        # Build context and materialize asset
        context = build_asset_context()
        result = system_alerts(context, pipeline_metrics_data)

        # Verify result
        assert isinstance(result, pd.DataFrame)

        # Verify alerts were created (should be 3 alerts based on thresholds)
        assert len(result) >= 1  # At least one alert should be generated

        if len(result) > 0:
            assert "type" in result.columns
            assert "severity" in result.columns
            assert "message" in result.columns


class TestDagsterSensors:
    """Test Dagster sensors functionality."""

    @patch("llm_rag_yt.dagster.sensors.TelegramDatabase")
    def test_youtube_url_sensor_with_requests(
        self, mock_db_class, sample_youtube_requests
    ):
        """Test YouTube URL sensor with pending requests."""
        # Setup mock
        mock_db = Mock()
        mock_db.get_pending_youtube_requests.return_value = sample_youtube_requests
        mock_db_class.return_value = mock_db

        # Create sensor context
        context = Mock()
        context.log = Mock()

        # Run sensor
        result = youtube_url_sensor(context)

        # Verify sensor result
        assert hasattr(result, "run_requests")
        assert len(result.run_requests) == 2  # Should create run requests for both URLs

        # Verify run request details
        for i, run_request in enumerate(result.run_requests):
            expected_url = sample_youtube_requests[i]["url"]
            assert expected_url in str(run_request.tags)

    @patch("llm_rag_yt.dagster.sensors.TelegramDatabase")
    def test_youtube_url_sensor_no_requests(self, mock_db_class):
        """Test YouTube URL sensor with no pending requests."""
        # Setup mock
        mock_db = Mock()
        mock_db.get_pending_youtube_requests.return_value = []
        mock_db_class.return_value = mock_db

        # Create sensor context
        context = Mock()
        context.log = Mock()

        # Run sensor
        result = youtube_url_sensor(context)

        # Verify sensor skips
        assert hasattr(result, "skip_reason")
        assert "No pending YouTube requests found" in str(result.skip_reason)

    @patch("llm_rag_yt.dagster.sensors.Path")
    @patch("llm_rag_yt.dagster.sensors.TelegramDatabase")
    def test_audio_file_sensor_with_files(self, mock_db_class, mock_path):
        """Test audio file sensor with new files."""
        # Setup filesystem mock
        mock_audio_dir = Mock()
        mock_audio_dir.exists.return_value = True

        # Create mock audio files
        mock_file1 = Mock()
        mock_file1.stat.return_value.st_size = 1024
        mock_file1.stat.return_value.st_mtime = 1642592400.0
        mock_file1.__str__ = lambda: "/data/audio/file1.mp3"

        mock_file2 = Mock()
        mock_file2.stat.return_value.st_size = 2048
        mock_file2.stat.return_value.st_mtime = 1642592500.0
        mock_file2.__str__ = lambda: "/data/audio/file2.mp3"

        mock_audio_dir.glob.return_value = [mock_file1, mock_file2]
        mock_path.return_value = mock_audio_dir

        # Setup database mock
        mock_db = Mock()
        mock_db.register_audio_file.return_value = True  # New file registered
        mock_db_class.return_value = mock_db

        # Create sensor context
        context = Mock()
        context.log = Mock()

        # Run sensor
        result = audio_file_sensor(context)

        # Verify sensor result
        assert hasattr(result, "run_requests")
        assert len(result.run_requests) == 1  # Should create one run request

        # Verify database calls
        assert mock_db.register_audio_file.call_count == 2

    @patch("llm_rag_yt.dagster.sensors.TelegramDatabase")
    def test_pipeline_health_sensor_healthy(self, mock_db_class):
        """Test pipeline health sensor with healthy system."""
        # Setup mock
        mock_db = Mock()
        mock_db.get_unacknowledged_alerts.return_value = []
        mock_db.get_processing_stats.return_value = {
            "pipeline_jobs": {"failed": 2}  # Below threshold
        }
        mock_db.get_pending_youtube_requests.return_value = []
        mock_db_class.return_value = mock_db

        # Create sensor context
        context = Mock()
        context.log = Mock()

        # Run sensor
        result = pipeline_health_sensor(context)

        # Verify sensor skips (system is healthy)
        assert hasattr(result, "skip_reason")
        assert "Pipeline health is good" in str(result.skip_reason)

    @patch("llm_rag_yt.dagster.sensors.TelegramDatabase")
    def test_pipeline_health_sensor_unhealthy(self, mock_db_class):
        """Test pipeline health sensor with unhealthy system."""
        # Setup mock with high failure count
        mock_db = Mock()
        mock_db.get_unacknowledged_alerts.return_value = []
        mock_db.get_processing_stats.return_value = {
            "pipeline_jobs": {"failed": 10}  # Above threshold
        }
        mock_db.get_pending_youtube_requests.return_value = []
        mock_db_class.return_value = mock_db

        # Create sensor context
        context = Mock()
        context.log = Mock()

        # Run sensor
        result = pipeline_health_sensor(context)

        # Verify sensor triggers monitoring
        assert hasattr(result, "run_requests")
        assert len(result.run_requests) == 1


class TestDagsterJobs:
    """Test Dagster job operations."""

    @patch("llm_rag_yt.dagster.jobs.TelegramDatabase")
    def test_pipeline_metrics_op(self, mock_db_class):
        """Test pipeline_metrics_op operation."""
        # Setup mocks
        mock_db = Mock()
        mock_db.get_processing_stats.return_value = {
            "youtube_requests": {"pending": 5, "completed": 10},
            "audio_files": {"pending": 3, "completed": 8},
        }
        mock_db.get_user_stats.return_value = {
            "total_queries": 100,
            "unique_users": 15,
        }
        mock_db_class.return_value = mock_db

        # Mock filesystem
        with patch("llm_rag_yt.dagster.jobs.Path") as mock_path:
            mock_audio_dir = Mock()
            mock_audio_dir.exists.return_value = True
            mock_audio_dir.glob.return_value = [Mock() for _ in range(3)]
            mock_path.return_value = mock_audio_dir

            # Mock context
            context = Mock()
            context.log = Mock()

            # Run operation
            result = pipeline_metrics_op(context)

            # Verify result
            assert isinstance(result, dict)
            assert "timestamp" in result
            assert "processing_stats" in result
            assert "user_stats" in result
            assert "filesystem" in result

    @patch("llm_rag_yt.dagster.jobs.TelegramDatabase")
    def test_system_alerts_op(self, mock_db_class):
        """Test system_alerts_op operation."""
        # Setup mock
        mock_db = Mock()
        mock_db_class.return_value = mock_db

        # Mock context
        context = Mock()
        context.log = Mock()

        # Test with high failure counts to trigger alerts
        metrics = {
            "processing_stats": {
                "youtube_requests": {"failed": 10},  # Above threshold
                "audio_files": {"failed": 5},  # Above threshold
                "pipeline_jobs": {"pending": 15},  # Above threshold
            }
        }

        # Run operation
        result = system_alerts_op(context, metrics)

        # Verify result
        assert isinstance(result, dict)
        assert "alerts" in result
        assert "total_count" in result
        assert len(result["alerts"]) >= 1

    @patch("llm_rag_yt.dagster.jobs.TelegramDatabase")
    def test_health_check_op(self, mock_db_class):
        """Test health_check operation."""
        # Setup mocks
        mock_db = Mock()
        mock_db.get_processing_stats.return_value = {"status": "healthy"}
        mock_db_class.return_value = mock_db

        # Mock context
        context = Mock()
        context.log = Mock()

        # Mock filesystem and other dependencies
        with patch("llm_rag_yt.dagster.jobs.Path") as mock_path, \
             patch("llm_rag_yt.dagster.jobs.psutil") as mock_psutil:
            
            mock_audio_dir = Mock()
            mock_audio_dir.exists.return_value = True
            mock_path.return_value = mock_audio_dir

            mock_disk_usage = Mock()
            mock_disk_usage.free = 5 * 1024**3  # 5GB free
            mock_psutil.disk_usage.return_value = mock_disk_usage

            # Run operation
            result = health_check(context)

            # Verify result
            assert isinstance(result, dict)
            assert "timestamp" in result
            assert "status" in result
            assert "checks" in result

    @patch("llm_rag_yt.dagster.jobs.TelegramDatabase")
    def test_cleanup_old_files_op(self, mock_db_class):
        """Test cleanup_old_files operation."""
        # Setup mocks
        mock_db = Mock()
        mock_db.get_connection.return_value.__enter__ = Mock()
        mock_db.get_connection.return_value.__exit__ = Mock()
        mock_db_class.return_value = mock_db

        # Mock context
        context = Mock()
        context.log = Mock()

        # Mock filesystem
        with patch("llm_rag_yt.dagster.jobs.Path") as mock_path, \
             patch("llm_rag_yt.dagster.jobs.os") as mock_os, \
             patch("llm_rag_yt.dagster.jobs.datetime") as mock_datetime:
            
            mock_audio_dir = Mock()
            mock_audio_dir.exists.return_value = True
            
            # Create mock old files
            from datetime import datetime, timedelta
            old_time = datetime.now() - timedelta(days=10)
            
            mock_file = Mock()
            mock_file.is_file.return_value = True
            mock_file.stat.return_value.st_mtime = old_time.timestamp()
            mock_file.stat.return_value.st_size = 1024
            
            mock_audio_dir.iterdir.return_value = [mock_file]
            mock_path.return_value = mock_audio_dir
            
            mock_datetime.now.return_value = datetime.now()
            mock_datetime.fromtimestamp.return_value = old_time

            # Run operation
            result = cleanup_old_files(context)

            # Verify result
            assert isinstance(result, dict)
            assert "status" in result

    @patch("llm_rag_yt.dagster.jobs.TelegramDatabase")
    def test_send_telegram_alerts_op(self, mock_db_class):
        """Test send_telegram_alerts operation."""
        # Setup mocks
        mock_db = Mock()
        mock_connection = Mock()
        mock_cursor = Mock()
        
        # Mock alert data
        alert_data = {
            "id": 1,
            "alert_type": "test",
            "severity": "warning",
            "message": "Test alert",
            "created_at": "2025-01-19T10:00:00",
        }
        
        mock_cursor.fetchone.return_value = alert_data
        mock_connection.execute.return_value = mock_cursor
        mock_db.get_connection.return_value.__enter__ = lambda self: mock_connection
        mock_db.get_connection.return_value.__exit__ = Mock()
        mock_db_class.return_value = mock_db

        # Mock context with config
        context = Mock()
        context.log = Mock()
        context.op_config = {
            "alert_ids": [1],
            "bot_token": "test_token"
        }
        context.resources = {}

        # Run operation
        result = send_telegram_alerts(context)

        # Verify result
        assert isinstance(result, dict)
        assert "status" in result
        
        # Verify database interaction
        mock_db.acknowledge_alert.assert_called_once_with(1)


class TestDagsterIntegration:
    """Integration tests for Dagster pipeline."""

    def test_asset_dependencies(self):
        """Test that asset dependencies are correctly defined."""
        from llm_rag_yt.dagster.definitions import defs

        # Get asset definitions
        assets = defs.get_assets_defs()

        # Verify we have the expected assets
        asset_names = [asset.key.to_user_string() for asset in assets]

        expected_assets = [
            "youtube_urls_to_process",
            "downloaded_audio_files",
            "unprocessed_audio_files",
            "transcribed_audio_files",
            "embedded_content",
            "pipeline_metrics",
            "system_alerts",
        ]

        for expected_asset in expected_assets:
            assert expected_asset in asset_names

    def test_job_definitions(self):
        """Test that jobs are correctly defined."""
        from llm_rag_yt.dagster.definitions import defs

        # Get job definitions
        jobs = defs.get_job_defs()

        # Verify we have the expected jobs
        job_names = [job.name for job in jobs]

        expected_jobs = [
            "pipeline_monitoring_job",
            "telegram_alert_job", 
            "cleanup_job",
            "health_check_job",
        ]

        for expected_job in expected_jobs:
            assert expected_job in job_names
            
        # Note: youtube_processing_job and audio_processing_job are commented out
        # as they incorrectly mixed assets and ops - use assets directly instead

    def test_sensor_definitions(self):
        """Test that sensors are correctly defined."""
        from llm_rag_yt.dagster.definitions import defs

        # Get sensor definitions
        sensors = defs.get_sensor_defs()

        # Verify we have the expected sensors
        sensor_names = [sensor.name for sensor in sensors]

        expected_sensors = [
            "youtube_url_sensor",
            "audio_file_sensor",
            "pipeline_health_sensor",
            "cleanup_sensor",
            "telegram_alert_sensor",
        ]

        for expected_sensor in expected_sensors:
            assert expected_sensor in sensor_names


def test_file_hash_calculation():
    """Test file hash calculation utility."""
    import os
    import tempfile

    from llm_rag_yt.dagster.assets import _calculate_file_hash

    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(b"test content")
        tmp_file_path = tmp_file.name

    try:
        # Calculate hash
        hash1 = _calculate_file_hash(tmp_file_path)
        hash2 = _calculate_file_hash(tmp_file_path)

        # Hash should be consistent
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hash length

    finally:
        # Clean up
        os.unlink(tmp_file_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
