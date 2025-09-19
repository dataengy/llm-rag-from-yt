"""
SQLite database for Telegram bot operations and pipeline management.
"""

import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class TelegramDatabase:
    """Database for Telegram bot and pipeline management."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize database connection."""
        if db_path is None:
            db_path = Path("data/telegram_bot.db")
        
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize tables
        self._create_tables()
    
    @contextmanager
    def get_connection(self):
        """Get database connection with context manager."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
        finally:
            conn.close()
    
    def _create_tables(self):
        """Create all required tables."""
        with self.get_connection() as conn:
            # YouTube links processing table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS youtube_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    url TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processing_started_at TIMESTAMP,
                    processing_completed_at TIMESTAMP,
                    error_message TEXT
                )
            """)
            
            # Audio files sensor table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audio_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL UNIQUE,
                    file_size INTEGER,
                    file_hash TEXT,
                    status TEXT NOT NULL DEFAULT 'detected',
                    processing_status TEXT DEFAULT 'pending',
                    transcription_path TEXT,
                    embedding_status TEXT DEFAULT 'pending',
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP
                )
            """)
            
            # User queries log
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_queries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    query_text TEXT NOT NULL,
                    response_text TEXT,
                    response_time_ms INTEGER,
                    relevance_score REAL,
                    sources_count INTEGER,
                    search_method TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # API calls log
            conn.execute("""
                CREATE TABLE IF NOT EXISTS api_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    endpoint TEXT NOT NULL,
                    method TEXT NOT NULL,
                    user_id INTEGER,
                    request_data TEXT,
                    response_data TEXT,
                    status_code INTEGER,
                    response_time_ms INTEGER,
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # User activity and sessions
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT,
                    action TEXT NOT NULL,
                    details TEXT,
                    session_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Feedback and ratings
            conn.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    query_id INTEGER,
                    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
                    feedback_type TEXT,
                    comment TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (query_id) REFERENCES user_queries (id)
                )
            """)
            
            # Pipeline jobs queue
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pipeline_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_type TEXT NOT NULL,
                    job_data TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    priority INTEGER DEFAULT 5,
                    scheduled_at TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    error_message TEXT,
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    worker_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # System alerts and notifications
            conn.execute("""
                CREATE TABLE IF NOT EXISTS system_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    details TEXT,
                    acknowledged BOOLEAN DEFAULT FALSE,
                    resolved BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    acknowledged_at TIMESTAMP,
                    resolved_at TIMESTAMP
                )
            """)
            
            # Create indices for better performance
            self._create_indices(conn)
            
            conn.commit()
            logger.info("Database tables created successfully")
    
    def _create_indices(self, conn):
        """Create database indices for better performance."""
        indices = [
            "CREATE INDEX IF NOT EXISTS idx_youtube_requests_user_id ON youtube_requests(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_youtube_requests_status ON youtube_requests(status)",
            "CREATE INDEX IF NOT EXISTS idx_audio_files_status ON audio_files(status)",
            "CREATE INDEX IF NOT EXISTS idx_user_queries_user_id ON user_queries(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_api_log_endpoint ON api_log(endpoint)",
            "CREATE INDEX IF NOT EXISTS idx_pipeline_jobs_status ON pipeline_jobs(status)",
            "CREATE INDEX IF NOT EXISTS idx_system_alerts_severity ON system_alerts(severity)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON feedback(user_id)",
        ]
        
        for index_sql in indices:
            conn.execute(index_sql)
    
    # YouTube requests methods
    def log_youtube_request(self, user_id: int, url: str, status: str, metadata: Optional[Dict] = None):
        """Log a YouTube processing request."""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO youtube_requests (user_id, url, status, metadata)
                VALUES (?, ?, ?, ?)
            """, (user_id, url, status, json.dumps(metadata) if metadata else None))
            conn.commit()
    
    def update_youtube_request_status(self, request_id: int, status: str, error_message: Optional[str] = None):
        """Update YouTube request status."""
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE youtube_requests 
                SET status = ?, updated_at = CURRENT_TIMESTAMP, error_message = ?
                WHERE id = ?
            """, (status, error_message, request_id))
            conn.commit()
    
    def get_pending_youtube_requests(self) -> List[Dict[str, Any]]:
        """Get all pending YouTube requests."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM youtube_requests 
                WHERE status = 'pending' 
                ORDER BY created_at ASC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    # Audio files methods
    def register_audio_file(self, file_path: str, file_size: int, file_hash: str, metadata: Optional[Dict] = None):
        """Register a new audio file for processing."""
        with self.get_connection() as conn:
            try:
                conn.execute("""
                    INSERT INTO audio_files (file_path, file_size, file_hash, metadata)
                    VALUES (?, ?, ?, ?)
                """, (file_path, file_size, file_hash, json.dumps(metadata) if metadata else None))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                # File already exists
                return False
    
    def update_audio_file_status(self, file_path: str, processing_status: str, 
                                 transcription_path: Optional[str] = None,
                                 embedding_status: Optional[str] = None):
        """Update audio file processing status."""
        with self.get_connection() as conn:
            update_fields = ["processing_status = ?", "updated_at = CURRENT_TIMESTAMP"]
            params = [processing_status]
            
            if transcription_path:
                update_fields.append("transcription_path = ?")
                params.append(transcription_path)
            
            if embedding_status:
                update_fields.append("embedding_status = ?")
                params.append(embedding_status)
            
            params.append(file_path)
            
            conn.execute(f"""
                UPDATE audio_files 
                SET {', '.join(update_fields)}
                WHERE file_path = ?
            """, params)
            conn.commit()
    
    def get_unprocessed_audio_files(self) -> List[Dict[str, Any]]:
        """Get audio files that need processing."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM audio_files 
                WHERE processing_status = 'pending' 
                ORDER BY created_at ASC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    # User queries methods
    def log_user_query(self, user_id: int, query_text: str, response_text: Optional[str] = None,
                       response_time_ms: Optional[int] = None, relevance_score: Optional[float] = None,
                       sources_count: Optional[int] = None, search_method: Optional[str] = None,
                       metadata: Optional[Dict] = None) -> int:
        """Log a user query and return the query ID."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO user_queries 
                (user_id, query_text, response_text, response_time_ms, relevance_score, 
                 sources_count, search_method, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, query_text, response_text, response_time_ms, relevance_score,
                  sources_count, search_method, json.dumps(metadata) if metadata else None))
            conn.commit()
            return cursor.lastrowid
    
    def update_query_response(self, query_id: int, response_text: str, response_time_ms: int,
                             relevance_score: float, sources_count: int, search_method: str):
        """Update query with response details."""
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE user_queries 
                SET response_text = ?, response_time_ms = ?, relevance_score = ?, 
                    sources_count = ?, search_method = ?
                WHERE id = ?
            """, (response_text, response_time_ms, relevance_score, sources_count, search_method, query_id))
            conn.commit()
    
    # API logging methods
    def log_api_call(self, endpoint: str, method: str, user_id: Optional[int] = None,
                     request_data: Optional[Dict] = None, response_data: Optional[Dict] = None,
                     status_code: Optional[int] = None, response_time_ms: Optional[int] = None,
                     ip_address: Optional[str] = None, user_agent: Optional[str] = None):
        """Log an API call."""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO api_log 
                (endpoint, method, user_id, request_data, response_data, status_code, 
                 response_time_ms, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (endpoint, method, user_id, 
                  json.dumps(request_data) if request_data else None,
                  json.dumps(response_data) if response_data else None,
                  status_code, response_time_ms, ip_address, user_agent))
            conn.commit()
    
    # User activity methods
    def log_user_activity(self, user_id: int, username: Optional[str], action: str,
                          details: Optional[Dict] = None, session_id: Optional[str] = None):
        """Log user activity."""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO user_activity (user_id, username, action, details, session_id)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, username, action, json.dumps(details) if details else None, session_id))
            conn.commit()
    
    # Feedback methods
    def log_feedback(self, user_id: int, query_text: str, feedback_type: str,
                     metadata: Optional[Dict] = None, rating: Optional[int] = None,
                     comment: Optional[str] = None, query_id: Optional[int] = None):
        """Log user feedback."""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO feedback (user_id, query_id, rating, feedback_type, comment, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, query_id, rating, feedback_type, comment, 
                  json.dumps(metadata) if metadata else None))
            conn.commit()
    
    # Pipeline jobs methods
    def add_pipeline_job(self, job_type: str, job_data: Dict, priority: int = 5,
                         scheduled_at: Optional[datetime] = None) -> int:
        """Add a new pipeline job."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO pipeline_jobs (job_type, job_data, priority, scheduled_at)
                VALUES (?, ?, ?, ?)
            """, (job_type, json.dumps(job_data), priority, scheduled_at))
            conn.commit()
            return cursor.lastrowid
    
    def get_pending_jobs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get pending pipeline jobs ordered by priority and creation time."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM pipeline_jobs 
                WHERE status = 'pending' AND (scheduled_at IS NULL OR scheduled_at <= CURRENT_TIMESTAMP)
                ORDER BY priority ASC, created_at ASC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def update_job_status(self, job_id: int, status: str, worker_id: Optional[str] = None,
                          error_message: Optional[str] = None):
        """Update job status."""
        with self.get_connection() as conn:
            if status == 'processing':
                conn.execute("""
                    UPDATE pipeline_jobs 
                    SET status = ?, worker_id = ?, started_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (status, worker_id, job_id))
            elif status == 'completed':
                conn.execute("""
                    UPDATE pipeline_jobs 
                    SET status = ?, completed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (status, job_id))
            elif status == 'failed':
                conn.execute("""
                    UPDATE pipeline_jobs 
                    SET status = ?, error_message = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (status, error_message, job_id))
            else:
                conn.execute("""
                    UPDATE pipeline_jobs 
                    SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (status, job_id))
            conn.commit()
    
    # System alerts methods
    def create_alert(self, alert_type: str, severity: str, message: str, details: Optional[Dict] = None):
        """Create a system alert."""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO system_alerts (alert_type, severity, message, details)
                VALUES (?, ?, ?, ?)
            """, (alert_type, severity, message, json.dumps(details) if details else None))
            conn.commit()
    
    def get_unacknowledged_alerts(self) -> List[Dict[str, Any]]:
        """Get unacknowledged alerts."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM system_alerts 
                WHERE acknowledged = FALSE 
                ORDER BY created_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def acknowledge_alert(self, alert_id: int):
        """Acknowledge an alert."""
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE system_alerts 
                SET acknowledged = TRUE, acknowledged_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (alert_id,))
            conn.commit()
    
    # Analytics methods
    def get_user_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get user activity statistics."""
        with self.get_connection() as conn:
            # Total queries
            cursor = conn.execute("""
                SELECT COUNT(*) as total_queries, COUNT(DISTINCT user_id) as unique_users
                FROM user_queries 
                WHERE created_at >= datetime('now', '-{} days')
            """.format(days))
            stats = dict(cursor.fetchone())
            
            # Average response time
            cursor = conn.execute("""
                SELECT AVG(response_time_ms) as avg_response_time
                FROM user_queries 
                WHERE response_time_ms IS NOT NULL AND created_at >= datetime('now', '-{} days')
            """.format(days))
            avg_time = cursor.fetchone()[0]
            stats['avg_response_time_ms'] = avg_time
            
            # Feedback distribution
            cursor = conn.execute("""
                SELECT feedback_type, COUNT(*) as count
                FROM feedback 
                WHERE created_at >= datetime('now', '-{} days')
                GROUP BY feedback_type
            """.format(days))
            stats['feedback'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            return stats
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing pipeline statistics."""
        with self.get_connection() as conn:
            stats = {}
            
            # YouTube requests stats
            cursor = conn.execute("""
                SELECT status, COUNT(*) as count 
                FROM youtube_requests 
                GROUP BY status
            """)
            stats['youtube_requests'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Audio files stats
            cursor = conn.execute("""
                SELECT processing_status, COUNT(*) as count 
                FROM audio_files 
                GROUP BY processing_status
            """)
            stats['audio_files'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Pipeline jobs stats
            cursor = conn.execute("""
                SELECT status, COUNT(*) as count 
                FROM pipeline_jobs 
                GROUP BY status
            """)
            stats['pipeline_jobs'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            return stats