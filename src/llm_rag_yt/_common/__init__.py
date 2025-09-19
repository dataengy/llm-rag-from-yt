"""
Common utilities, logging, and configuration for the YouTube RAG project.
"""

from .config.settings import Config, get_config
from .logging import (
    log,
    log_error_context,
    log_performance,
    log_startup,
    log_system_health,
    log_user_action,
    setup_logging,
)
from .utils import (
    create_rag_metadata,
    generate_simple_answer,
    load_transcription_text,
    setup_logger,
    simple_search,
)

__all__ = [
    # Logging
    "log",
    "setup_logging",
    "log_startup",
    "log_performance",
    "log_user_action",
    "log_system_health",
    "log_error_context",
    # Configuration
    "Config",
    "get_config",
    # Utilities
    "setup_logger",
    "load_transcription_text",
    "simple_search",
    "generate_simple_answer",
    "create_rag_metadata",
]
