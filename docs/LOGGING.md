# Centralized Logging System

## Overview

The YouTube RAG project uses a centralized logging system built on top of [Loguru](https://loguru.readthedocs.io/) that provides:

- **Unified logging** across all components
- **Short colored format** with emojis for easy reading
- **Multiple log files** organized by component and severity
- **Global `log` instance** for easy access
- **Performance and user action tracking**
- **Telegram integration** for critical alerts

## Quick Start

### Basic Usage

```python
# Import the global log instance
from llm_rag_yt.logging import log

# Use different log levels with emojis
log.debug("🐛 Debug information")
log.info("ℹ️ General information") 
log.success("✅ Operation successful")
log.warning("⚠️ Warning message")
log.error("❌ Error occurred")
log.critical("🚨 Critical system error")
```

### Structured Logging

```python
# Add context to log messages
log.bind(user_id=12345, operation="transcription").info("Started processing")
log.bind(component="telegram_bot", status="healthy").info("Health check passed")

# Log with additional context
log.bind(
    url="https://youtube.com/watch?v=abc123",
    duration=125.5,
    language="ru"
).info("YouTube video processed successfully")
```

## Features

### 🎨 Short Colored Format with Emojis

The console output uses a compact, readable format:

```
19:09:34 ℹ️ I telegram.bot User started video processing
19:09:35 ✅ S dagster.assets Audio transcription completed  
19:09:36 ⚠️ W pipeline.rag Low confidence in answer
19:09:37 ❌ E api.server Rate limit exceeded
```

Format: `{time} {emoji} {level} {component} {message}`

### 📁 Multiple Log Files

Logs are automatically organized into different files:

- **`logs/app.log`** - All application logs (rotated at 10MB)
- **`logs/errors.log`** - Error and critical logs only
- **`logs/telegram_bot.log`** - Telegram bot specific logs  
- **`logs/dagster.log`** - Dagster pipeline logs
- **`logs/rag_processing.log`** - RAG processing component logs

All files are:
- Compressed with gzip when rotated
- Retained for 30 days (14 days for component logs)
- Automatically rotated by size

### 🎯 Specialized Logging Functions

```python
from llm_rag_yt.logging import (
    log_startup,
    log_performance, 
    log_user_action,
    log_system_health,
    log_error_context
)

# Startup logging with configuration
log_startup("Telegram Bot", version="1.0.0", config={
    "debug_mode": True,
    "api_key": "sk-xxx...xxx",  # Automatically masked
    "max_tokens": 1000
})

# Performance tracking
log_performance("Database Query", 0.125, {
    "rows_returned": 42,
    "cache_hit": True
})

# User action tracking
log_user_action(12345, "youtube_url_processed", {
    "url": "https://youtube.com/watch?v=abc123",
    "duration": "10:30"
})

# System health monitoring
log_system_health("vector_store", "healthy", {
    "documents": 1500,
    "memory_usage": "250MB"
})

# Error with context
try:
    result = process_video(url)
except Exception as e:
    log_error_context(e, {
        "user_id": 12345,
        "url": url,
        "operation": "video_processing"
    })
```

## Setup and Configuration

### Automatic Initialization

The logging system is automatically initialized when you import the `log` instance:

```python
from llm_rag_yt.logging import log  # Logging is now ready
```

### Manual Configuration

For custom setup (optional):

```python
from llm_rag_yt.logging import setup_logging

# Setup with custom level and directory
setup_logging(log_level="DEBUG", log_dir=Path("/custom/logs"))
```

### Log Levels

| Level | Emoji | Description |
|-------|-------|-------------|
| `TRACE` | 🔍 | Detailed tracing information |
| `DEBUG` | 🐛 | Debug information for development |
| `INFO` | ℹ️ | General informational messages |
| `SUCCESS` | ✅ | Successful operations |
| `WARNING` | ⚠️ | Warning messages |
| `ERROR` | ❌ | Error conditions |
| `CRITICAL` | 🚨 | Critical system errors |

## Integration Examples

### Telegram Bot Integration

```python
from llm_rag_yt.logging import log, log_user_action

class TelegramBot:
    async def process_youtube_url(self, user_id: int, url: str):
        log.bind(user_id=user_id, url=url).info("Starting YouTube processing")
        
        try:
            result = await self.pipeline.process(url)
            log_user_action(user_id, "youtube_processed", {
                "url": url,
                "duration": result.duration,
                "success": True
            })
            log.bind(user_id=user_id).success("YouTube processing completed")
            
        except Exception as e:
            log.bind(user_id=user_id, url=url).error(f"Processing failed: {e}")
```

### Dagster Assets Integration

```python
from llm_rag_yt.logging import log, log_performance

@asset
def transcribed_audio_files(context, unprocessed_audio_files):
    start_time = time.time()
    log.bind(asset="transcribed_audio_files").info("Starting transcription")
    
    results = []
    for file in unprocessed_audio_files:
        log.bind(file=file.name).debug("Transcribing audio file")
        # ... transcription logic ...
        
    duration = time.time() - start_time
    log_performance("Audio Transcription", duration, {
        "files_processed": len(results),
        "total_duration": sum(r.duration for r in results)
    })
    
    return results
```

### CLI Integration

```python
from llm_rag_yt.logging import log, log_startup

@app.command()
def process(urls: List[str], verbose: bool = False):
    log_startup("CLI Processing", config={
        "urls_count": len(urls),
        "verbose": verbose
    })
    
    for url in urls:
        log.bind(url=url).info("Processing YouTube URL")
        # ... processing logic ...
```

## Telegram Alert Integration

For critical system alerts, the logging system can send messages to Telegram:

```python
from llm_rag_yt.logging.telegram_handler import setup_telegram_logging

# Setup Telegram alerts (requires BOT_TOKEN and TELEGRAM_ADMIN_CHAT_ID)
setup_telegram_logging(level=logging.ERROR)

# Critical errors will now be sent to Telegram
log.critical("🚨 System database connection lost")
log.error("❌ Failed to process 5 consecutive requests")
```

## Performance Considerations

### Async Logging

All logging operations are non-blocking and won't impact application performance.

### Log Filtering

Component-specific logs are filtered automatically:

```python
# These will go to logs/telegram_bot.log
log.bind(component="telegram").info("Bot message")

# These will go to logs/dagster.log  
log.bind(component="dagster").info("Asset materialized")

# These will go to logs/rag_processing.log
log.bind(component="pipeline").info("RAG query processed")
```

### Structured Data

Use structured logging for better querying and analysis:

```python
# Good: Structured data
log.bind(
    operation="youtube_download",
    url="https://youtube.com/watch?v=abc123", 
    file_size_mb=45.2,
    duration_seconds=125
).info("Download completed")

# Avoid: Unstructured strings
log.info("Downloaded https://youtube.com/watch?v=abc123 (45.2MB, 125s)")
```

## Best Practices

### 1. Use Appropriate Log Levels

```python
# DEBUG: Development information
log.debug("🐛 Entering function with params: {params}")

# INFO: Normal operation
log.info("ℹ️ Processing YouTube URL")

# SUCCESS: Successful completion
log.success("✅ Video processing completed")

# WARNING: Potential issues
log.warning("⚠️ Low confidence in transcription quality")

# ERROR: Recoverable errors
log.error("❌ Failed to download video, retrying...")

# CRITICAL: System-threatening issues
log.critical("🚨 Database connection lost")
```

### 2. Include Context

```python
# Always include relevant context
log.bind(
    user_id=user_id,
    operation="transcription",
    file_path=audio_file,
    language=language
).info("Starting audio transcription")
```

### 3. Log User Actions

```python
# Track important user actions for analytics
log_user_action(user_id, "query_submitted", {
    "question": question[:100],  # Truncate long text
    "language": detected_language,
    "response_time_ms": response_time
})
```

### 4. Performance Logging

```python
# Track performance of critical operations
start_time = time.time()
result = expensive_operation()
log_performance("Expensive Operation", time.time() - start_time, {
    "input_size": len(input_data),
    "output_size": len(result),
    "cache_hit": cache_hit
})
```

### 5. Error Context

```python
# Always include context with errors
try:
    result = risky_operation(user_input)
except Exception as e:
    log_error_context(e, {
        "user_id": user_id,
        "input_data": user_input,
        "operation": "risky_operation",
        "retry_count": retry_count
    })
```

## Testing and Development

### Demo Script

Run the logging demo to see all features:

```bash
uv run python examples/logging_demo.py
```

This will demonstrate:
- All log levels with emojis
- Structured logging
- Performance tracking
- User action logging
- Error handling

### Log File Locations

During development, logs are written to:
- `./logs/` directory (created automatically)
- Console output with colors and emojis
- Component-specific files for easy debugging

### Environment Variables

Optional configuration via environment variables:
- `LOG_LEVEL` - Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `LOG_DIR` - Custom log directory path
- `BOT_TOKEN` - For Telegram alert integration
- `TELEGRAM_ADMIN_CHAT_ID` - Admin chat for alerts

## Migration from Standard Logging

### Before (standard logging)

```python
import logging
logger = logging.getLogger(__name__)

logger.info("Processing started")
logger.error("An error occurred")
```

### After (centralized logging)

```python
from llm_rag_yt.logging import log

log.info("ℹ️ Processing started")
log.error("❌ An error occurred")

# Or with context
log.bind(component="processor").info("Processing started")
log.bind(user_id=123, operation="process").error("An error occurred")
```

The centralized logging system provides a much richer, more maintainable logging experience while keeping the API simple and intuitive.