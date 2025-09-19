"""User feedback collection system."""

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from loguru import logger


@dataclass
class UserFeedback:
    """User feedback entry."""

    id: str
    query: str
    answer: str
    rating: int  # 1-5 scale
    feedback_text: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: str = ""
    response_time: Optional[float] = None
    sources_count: Optional[int] = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class FeedbackCollector:
    """Collects and manages user feedback."""

    def __init__(self, db_path: Path):
        """Initialize feedback collector with SQLite database."""
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database for feedback storage."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id TEXT PRIMARY KEY,
                query TEXT NOT NULL,
                answer TEXT NOT NULL,
                rating INTEGER NOT NULL,
                feedback_text TEXT,
                session_id TEXT,
                timestamp TEXT NOT NULL,
                response_time REAL,
                sources_count INTEGER
            )
        """)

        conn.commit()
        conn.close()
        logger.info(f"Initialized feedback database at {self.db_path}")

    def collect_feedback(
        self,
        query: str,
        answer: str,
        rating: int,
        feedback_text: Optional[str] = None,
        session_id: Optional[str] = None,
        response_time: Optional[float] = None,
        sources_count: Optional[int] = None,
    ) -> str:
        """Collect user feedback.

        Args:
            query: Original user query
            answer: System answer
            rating: User rating (1-5)
            feedback_text: Optional text feedback
            session_id: Optional session identifier
            response_time: Query response time
            sources_count: Number of sources used

        Returns:
            Feedback ID
        """
        feedback_id = (
            f"fb_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{abs(hash(query))}"
        )

        feedback = UserFeedback(
            id=feedback_id,
            query=query,
            answer=answer,
            rating=rating,
            feedback_text=feedback_text,
            session_id=session_id,
            response_time=response_time,
            sources_count=sources_count,
        )

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO feedback
            (id, query, answer, rating, feedback_text, session_id, timestamp, response_time, sources_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                feedback.id,
                feedback.query,
                feedback.answer,
                feedback.rating,
                feedback.feedback_text,
                feedback.session_id,
                feedback.timestamp,
                feedback.response_time,
                feedback.sources_count,
            ),
        )

        conn.commit()
        conn.close()

        logger.info(f"Collected feedback: {feedback_id} (rating: {rating})")
        return feedback_id

    def get_feedback_stats(self) -> dict[str, Any]:
        """Get feedback statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Basic stats
        cursor.execute(
            "SELECT COUNT(*), AVG(rating), MIN(rating), MAX(rating) FROM feedback"
        )
        count, avg_rating, min_rating, max_rating = cursor.fetchone()

        # Rating distribution
        cursor.execute(
            "SELECT rating, COUNT(*) FROM feedback GROUP BY rating ORDER BY rating"
        )
        rating_dist = dict(cursor.fetchall())

        # Recent feedback (last 7 days)
        week_ago = (datetime.now().timestamp() - 7 * 24 * 3600) * 1000
        cursor.execute(
            "SELECT COUNT(*) FROM feedback WHERE timestamp > ?",
            (datetime.fromtimestamp(week_ago / 1000).isoformat(),),
        )
        recent_count = cursor.fetchone()[0]

        # Average response time
        cursor.execute(
            "SELECT AVG(response_time) FROM feedback WHERE response_time IS NOT NULL"
        )
        avg_response_time = cursor.fetchone()[0]

        conn.close()

        return {
            "total_feedback": count or 0,
            "average_rating": float(avg_rating) if avg_rating else 0,
            "min_rating": min_rating or 0,
            "max_rating": max_rating or 0,
            "rating_distribution": rating_dist,
            "recent_feedback_7days": recent_count or 0,
            "average_response_time": float(avg_response_time)
            if avg_response_time
            else 0,
        }

    def get_recent_feedback(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get recent feedback entries."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM feedback
            ORDER BY timestamp DESC
            LIMIT ?
        """,
            (limit,),
        )

        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        conn.close()

        return [dict(zip(columns, row)) for row in rows]

    def get_low_rated_queries(self, rating_threshold: int = 2) -> list[dict[str, Any]]:
        """Get queries with low ratings for analysis."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM feedback
            WHERE rating <= ?
            ORDER BY timestamp DESC
        """,
            (rating_threshold,),
        )

        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        conn.close()

        return [dict(zip(columns, row)) for row in rows]

    def export_feedback(self, output_path: Path) -> None:
        """Export all feedback to JSON file."""
        feedback_data = self.get_recent_feedback(limit=10000)  # Export all

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(feedback_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Exported {len(feedback_data)} feedback entries to {output_path}")
