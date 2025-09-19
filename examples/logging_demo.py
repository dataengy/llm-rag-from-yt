#!/usr/bin/env python3
"""
Demo of the centralized logging system.
"""

import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from llm_rag_yt._common.logging import log, setup_logging, log_startup, log_performance, log_user_action


def demo_logging():
    """Demonstrate the logging system."""
    
    # Setup logging (already done by import, but showing explicitly)
    setup_logging(log_level="DEBUG")
    
    # Startup logging
    log_startup("Logging Demo", version="1.0.0", config={
        "debug_mode": True,
        "api_key": "sk-xxx...xxx",  # Will be masked
        "max_tokens": 1000
    })
    
    # Different log levels with emojis
    log.trace("🔍 This is a trace message")
    log.debug("🐛 This is a debug message")
    log.info("ℹ️ This is an info message")
    log.success("✅ This is a success message")
    log.warning("⚠️ This is a warning message")
    log.error("❌ This is an error message")
    log.critical("🚨 This is a critical message")
    
    # Performance logging
    log_performance("Database Query", 0.125, {
        "rows_returned": 42,
        "cache_hit": True
    })
    
    # User action logging
    log_user_action(12345, "youtube_url_processed", {
        "url": "https://youtube.com/watch?v=abc123",
        "duration": "10:30",
        "language": "ru"
    })
    
    # Structured logging
    log.bind(user_id=67890, operation="transcription").info("Started audio transcription")
    log.bind(component="telegram_bot", status="healthy").info("Bot health check passed")
    
    # Error with context
    try:
        result = 1 / 0
    except ZeroDivisionError as e:
        log.bind(operation="calculation", input_value=1).error(f"Division error: {e}")


if __name__ == "__main__":
    demo_logging()