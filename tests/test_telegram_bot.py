"""
Tests for Telegram bot functionality.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from llm_rag_yt._common.config.settings import get_config
from llm_rag_yt.telegram.bot import TelegramBot
from llm_rag_yt.telegram.database import TelegramDatabase
from llm_rag_yt.telegram.progress_tracker import ProgressTracker


@pytest.fixture
def temp_db_path(tmp_path):
    """Create temporary database for testing."""
    return tmp_path / "test_telegram.db"


@pytest.fixture
def telegram_db(temp_db_path):
    """Create TelegramDatabase instance with temporary database."""
    return TelegramDatabase(temp_db_path)


@pytest.fixture
def config():
    """Create test configuration."""
    return get_config()


@pytest.fixture
def bot_token():
    """Test bot token."""
    return "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"


@pytest.fixture
def telegram_bot(bot_token, config):
    """Create TelegramBot instance for testing."""
    return TelegramBot(bot_token, config)


class TestTelegramDatabase:
    """Test TelegramDatabase functionality."""

    def test_database_initialization(self, telegram_db):
        """Test database tables are created correctly."""
        with telegram_db.get_connection() as conn:
            # Check that tables exist
            cursor = conn.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            tables = [row[0] for row in cursor.fetchall()]

            expected_tables = [
                "youtube_requests",
                "audio_files",
                "user_queries",
                "api_log",
                "user_activity",
                "feedback",
                "pipeline_jobs",
                "system_alerts",
            ]

            for table in expected_tables:
                assert table in tables

    def test_log_youtube_request(self, telegram_db):
        """Test logging YouTube requests."""
        user_id = 12345
        url = "https://youtube.com/watch?v=abc123"

        telegram_db.log_youtube_request(user_id, url, "pending")

        # Verify request was logged
        with telegram_db.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT user_id, url, status FROM youtube_requests
                WHERE user_id = ? AND url = ?
            """,
                (user_id, url),
            )
            result = cursor.fetchone()

            assert result is not None
            assert result[0] == user_id
            assert result[1] == url
            assert result[2] == "pending"

    def test_log_user_query(self, telegram_db):
        """Test logging user queries."""
        user_id = 12345
        query_text = "What is this video about?"

        query_id = telegram_db.log_user_query(user_id, query_text)

        assert query_id is not None

        # Verify query was logged
        with telegram_db.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT user_id, query_text FROM user_queries WHERE id = ?
            """,
                (query_id,),
            )
            result = cursor.fetchone()

            assert result is not None
            assert result[0] == user_id
            assert result[1] == query_text

    def test_register_audio_file(self, telegram_db):
        """Test registering audio files."""
        file_path = "/path/to/audio.mp3"
        file_size = 1024
        file_hash = "abc123"

        # First registration should succeed
        result = telegram_db.register_audio_file(file_path, file_size, file_hash)
        assert result is True

        # Duplicate registration should fail
        result = telegram_db.register_audio_file(file_path, file_size, file_hash)
        assert result is False

    def test_get_processing_stats(self, telegram_db):
        """Test getting processing statistics."""
        # Add some test data
        telegram_db.log_youtube_request(1, "url1", "pending")
        telegram_db.log_youtube_request(2, "url2", "completed")
        telegram_db.register_audio_file("/path/1.mp3", 1024, "hash1")

        stats = telegram_db.get_processing_stats()

        assert "youtube_requests" in stats
        assert "audio_files" in stats
        assert stats["youtube_requests"]["pending"] == 1
        assert stats["youtube_requests"]["completed"] == 1


class TestProgressTracker:
    """Test ProgressTracker functionality."""

    def test_start_task(self):
        """Test starting a new task."""
        tracker = ProgressTracker()
        user_id = 12345

        task_id = tracker.start_task(user_id, "url_processing")

        assert task_id is not None
        assert tracker.has_active_task(user_id)

        progress = tracker.get_progress(user_id)
        assert progress is not None
        assert progress["task_type"] == "url_processing"
        assert progress["status"] == "running"

    def test_update_progress(self):
        """Test updating task progress."""
        tracker = ProgressTracker()
        user_id = 12345

        tracker.start_task(user_id, "url_processing")

        # Update progress
        success = tracker.update_progress(user_id, "Downloading", percentage=25.0)
        assert success is True

        progress = tracker.get_progress(user_id)
        assert progress["current_step"] == "Downloading"
        assert progress["percentage"] == 25.0

    def test_complete_task(self):
        """Test completing a task."""
        tracker = ProgressTracker()
        user_id = 12345

        tracker.start_task(user_id, "url_processing")
        tracker.complete_task(user_id, success=True)

        assert not tracker.has_active_task(user_id)
        progress = tracker.get_progress(user_id)
        assert progress is None

    def test_cancel_task(self):
        """Test cancelling a task."""
        tracker = ProgressTracker()
        user_id = 12345

        tracker.start_task(user_id, "url_processing")
        tracker.cancel_task(user_id)

        assert not tracker.has_active_task(user_id)


class TestTelegramBot:
    """Test TelegramBot functionality."""

    @pytest.mark.asyncio
    async def test_bot_initialization(self, telegram_bot):
        """Test bot initializes correctly."""
        assert telegram_bot.token is not None
        assert telegram_bot.config is not None
        assert telegram_bot.pipeline is not None
        assert telegram_bot.db is not None
        assert telegram_bot.progress_tracker is not None

    def test_valid_youtube_url(self, telegram_bot):
        """Test YouTube URL validation."""
        valid_urls = [
            "https://youtube.com/watch?v=abc123",
            "https://www.youtube.com/watch?v=abc123",
            "https://youtu.be/abc123",
            "http://youtube.com/watch?v=abc123",
        ]

        for url in valid_urls:
            assert telegram_bot._is_valid_youtube_url(url)

        invalid_urls = [
            "https://example.com",
            "not a url",
            "https://youtube.com",
            "https://vimeo.com/123456",
        ]

        for url in invalid_urls:
            assert not telegram_bot._is_valid_youtube_url(url)

    def test_progress_bar_creation(self, telegram_bot):
        """Test progress bar visualization."""
        # Test different percentages
        assert telegram_bot._create_progress_bar(0) == "[░░░░░░░░░░]"
        assert telegram_bot._create_progress_bar(50) == "[█████░░░░░]"
        assert telegram_bot._create_progress_bar(100) == "[██████████]"

        # Test custom length
        assert telegram_bot._create_progress_bar(50, length=4) == "[██░░]"


@pytest.mark.asyncio
class TestTelegramBotIntegration:
    """Integration tests for Telegram bot with mocked Telegram API."""

    async def test_start_command_flow(self, telegram_bot):
        """Test /start command flow."""
        # Mock Update and Context
        update = Mock()
        update.effective_user.id = 12345
        update.effective_user.username = "testuser"
        update.message.reply_text = AsyncMock()

        context = Mock()

        # Execute start command
        await telegram_bot.start_command(update, context)

        # Verify user session was created
        assert 12345 in telegram_bot.user_sessions
        assert telegram_bot.user_sessions[12345]["verbose"] is False

        # Verify reply was sent
        update.message.reply_text.assert_called_once()
        call_args = update.message.reply_text.call_args[0]
        assert "YouTube RAG Bot" in call_args[0]

    async def test_status_command(self, telegram_bot):
        """Test /status command."""
        # Mock Update and Context
        update = Mock()
        update.effective_user.id = 12345
        update.message.reply_text = AsyncMock()

        context = Mock()

        # Mock pipeline status
        with patch.object(telegram_bot.pipeline, "get_status") as mock_status:
            mock_status.return_value = {
                "ready": True,
                "vectorstore_docs": 10,
                "last_update": "2025-01-19",
            }

            await telegram_bot.status_command(update, context)

            # Verify reply was sent with status info
            update.message.reply_text.assert_called_once()
            call_args = update.message.reply_text.call_args[0]
            assert "System Status" in call_args[0]
            assert "Ready" in call_args[0]

    async def test_toggle_verbose(self, telegram_bot):
        """Test verbose mode toggle."""
        # Mock Update and Context
        update = Mock()
        update.effective_user.id = 12345
        update.message.reply_text = AsyncMock()

        context = Mock()

        # First toggle - enable verbose
        await telegram_bot.toggle_verbose(update, context)

        assert telegram_bot.user_sessions[12345]["verbose"] is True

        # Second toggle - disable verbose
        await telegram_bot.toggle_verbose(update, context)

        assert telegram_bot.user_sessions[12345]["verbose"] is False


def test_youtube_processing_steps():
    """Test YouTube processing step definitions."""
    from llm_rag_yt.telegram.progress_tracker import YouTubeProcessingSteps

    # Test step count
    assert len(YouTubeProcessingSteps.STEPS) == 7

    # Test step percentages
    assert YouTubeProcessingSteps.get_step_percentage("Validating URL") == 0.0
    assert YouTubeProcessingSteps.get_step_percentage("Downloading audio") > 0.0
    assert YouTubeProcessingSteps.get_step_percentage("Invalid step") == 0.0

    # Test total steps
    assert YouTubeProcessingSteps.get_total_steps() == 7


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
