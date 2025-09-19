"""Tests for monitoring components."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from llm_rag_yt.monitoring.dashboard import MonitoringDashboard
from llm_rag_yt.monitoring.feedback_collector import FeedbackCollector, UserFeedback


class TestFeedbackCollector:
    """Test feedback collection functionality."""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir) / "test_feedback.db"

    def test_collector_initialization(self, temp_db_path):
        """Test feedback collector initialization."""
        FeedbackCollector(temp_db_path)
        assert temp_db_path.exists()

    def test_feedback_collection(self, temp_db_path):
        """Test feedback collection."""
        collector = FeedbackCollector(temp_db_path)

        feedback_id = collector.collect_feedback(
            query="Test query", answer="Test answer", rating=5, feedback_text="Great!"
        )

        assert feedback_id.startswith("fb_")

        # Test stats
        stats = collector.get_feedback_stats()
        assert stats["total_feedback"] == 1
        assert stats["average_rating"] == 5.0

    def test_feedback_stats(self, temp_db_path):
        """Test feedback statistics."""
        collector = FeedbackCollector(temp_db_path)

        # Add multiple feedback entries
        for i in range(3):
            collector.collect_feedback(
                query=f"Query {i}",
                answer=f"Answer {i}",
                rating=i + 3,  # Ratings: 3, 4, 5
            )

        stats = collector.get_feedback_stats()
        assert stats["total_feedback"] == 3
        assert stats["average_rating"] == 4.0
        assert stats["min_rating"] == 3
        assert stats["max_rating"] == 5

    def test_low_rated_queries(self, temp_db_path):
        """Test low-rated query retrieval."""
        collector = FeedbackCollector(temp_db_path)

        # Add mixed ratings
        collector.collect_feedback("Good query", "Good answer", 5)
        collector.collect_feedback("Bad query", "Bad answer", 1)
        collector.collect_feedback("Poor query", "Poor answer", 2)

        low_rated = collector.get_low_rated_queries(rating_threshold=2)
        assert len(low_rated) == 2
        assert all(feedback["rating"] <= 2 for feedback in low_rated)


class TestUserFeedback:
    """Test UserFeedback dataclass."""

    def test_feedback_creation(self):
        """Test feedback object creation."""
        feedback = UserFeedback(
            id="test_id", query="Test query", answer="Test answer", rating=4
        )

        assert feedback.id == "test_id"
        assert feedback.query == "Test query"
        assert feedback.answer == "Test answer"
        assert feedback.rating == 4
        assert feedback.timestamp  # Should be auto-generated

    def test_feedback_with_optional_fields(self):
        """Test feedback with optional fields."""
        feedback = UserFeedback(
            id="test_id",
            query="Test query",
            answer="Test answer",
            rating=3,
            feedback_text="Could be better",
            session_id="session_123",
            response_time=1.5,
            sources_count=5,
        )

        assert feedback.feedback_text == "Could be better"
        assert feedback.session_id == "session_123"
        assert feedback.response_time == 1.5
        assert feedback.sources_count == 5


class TestMonitoringDashboard:
    """Test dashboard generation."""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir) / "test_feedback.db"

    def test_dashboard_initialization(self, temp_db_path):
        """Test dashboard initialization."""
        dashboard = MonitoringDashboard(temp_db_path)
        assert dashboard.feedback_collector is not None

    @patch("llm_rag_yt.monitoring.dashboard.px")
    @patch("llm_rag_yt.monitoring.dashboard.go")
    def test_dashboard_generation(self, mock_go, mock_px, temp_db_path):
        """Test dashboard HTML generation."""
        # Setup mock feedback data
        collector = FeedbackCollector(temp_db_path)
        collector.collect_feedback("Test query", "Test answer", 5)

        dashboard = MonitoringDashboard(temp_db_path)

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "dashboard.html"

            # Mock plotly figures
            mock_fig = Mock()
            mock_fig.to_html.return_value = "<div>Chart</div>"
            mock_px.pie.return_value = mock_fig
            mock_px.histogram.return_value = mock_fig
            mock_px.scatter.return_value = mock_fig
            mock_px.imshow.return_value = mock_fig
            mock_go.Figure.return_value = mock_fig

            result_path = dashboard.generate_dashboard_html(output_path)

            assert output_path.exists()
            assert "dashboard.html" in result_path

            # Check HTML content
            content = output_path.read_text()
            assert "LLM RAG YouTube - Monitoring Dashboard" in content
            assert "Chart" in content  # Mock chart content
