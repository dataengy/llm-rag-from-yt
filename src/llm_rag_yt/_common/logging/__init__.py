"""
Centralized logging for the YouTube RAG project.
"""

from .logger import (
    ProjectLogger,
    get_log,
    get_logger,
    log_error_context,
    log_performance,
    log_startup,
    log_system_health,
    log_user_action,
    setup_logging,
)


# Initialize global log instance
def _init_log():
    """Initialize the global log instance."""
    setup_logging()
    return get_log()


# Global log instance
log = _init_log()

__all__ = [
    "log",
    "get_logger",
    "get_log",
    "setup_logging",
    "log_startup",
    "log_performance",
    "log_user_action",
    "log_system_health",
    "log_error_context",
    "ProjectLogger",
]
