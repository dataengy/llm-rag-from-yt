# Telegram Bot Integration

## Overview

The YouTube RAG system now includes a comprehensive Telegram bot that allows users to:
- Submit YouTube URLs for processing with visual progress tracking
- Ask questions about processed content
- Monitor system status and receive alerts
- Toggle verbose mode for detailed output

## Features

### 🎬 YouTube URL Processing
- **Visual Progress Tracking**: Real-time progress bars showing download → transcribe → embed → ready
- **Verbose Mode**: Optional detailed output showing each processing step
- **Error Handling**: Graceful error reporting with retry options
- **Queue Management**: Handles multiple concurrent requests

### 🤖 RAG Query System
- **Natural Language Queries**: Ask questions in any language
- **Context-Aware Responses**: Intelligent answers based on processed content
- **Source Attribution**: Shows relevant source snippets with relevance scores
- **Feedback Collection**: Rate responses to improve the system

### 📊 System Monitoring
- **Real-time Status**: Check pipeline health and document counts
- **User Sessions**: Track active users and their current tasks
- **Activity Logging**: Comprehensive logging of all user interactions

## Setup

### 1. Create Telegram Bot

1. Contact [@BotFather](https://t.me/BotFather) on Telegram
2. Create a new bot: `/newbot`
3. Follow the prompts to set up your bot
4. Copy the bot token

### 2. Configuration

Add your bot token to the `.env` file:

```bash
# Telegram Bot Configuration
BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_ADMIN_CHAT_ID=your_admin_chat_id_for_alerts
```

To get your chat ID:
1. Send a message to your bot
2. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Look for `"chat":{"id":YOUR_CHAT_ID}`

### 3. Installation

The bot dependencies are included in the main project requirements:

```bash
# Install with telegram support
uv sync

# Or install telegram dependencies manually
pip install python-telegram-bot>=20.0
```

## Usage

### Starting the Bot

```bash
# Method 1: Using the CLI
uv run llm-rag-yt bot start

# Method 2: Using the runner script
python scripts/telegram_bot_runner.py

# Method 3: With custom token
uv run llm-rag-yt bot start --token YOUR_BOT_TOKEN
```

### Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Initialize bot and show welcome message |
| `/help` | Show detailed help and usage instructions |
| `/status` | Display system status and statistics |
| `/verbose` | Toggle verbose mode (detailed processing output) |
| `/cancel` | Cancel current operation |

### Interaction Examples

#### Processing YouTube URLs

```
User: https://youtube.com/watch?v=abc123

Bot: 🎬 Processing YouTube Video
     ━━━━━━━━━━━━━━━━━━━━━
     
     📹 URL: https://youtube.com/watch?v=abc123
     [████████░░] 80%
     🧮 Creating embeddings...
```

#### Asking Questions

```
User: What is the main topic discussed?

Bot: 🤖 Answer
     ━━━━━━━━━━━━━━━━━━━━━
     
     The main topic discussed in the video is machine learning 
     fundamentals, specifically covering neural networks and 
     their applications in natural language processing.
     
     📚 Sources:
     1. 🎯 Relevance: 0.89
     2. ⏱️ Response time: 1.2s
     
     [👍] [👎] [🔍 More details]
```

### Management Commands

```bash
# Check bot status
uv run llm-rag-yt bot status

# Add URL to processing queue
uv run llm-rag-yt bot add-url "https://youtube.com/watch?v=abc123" --user-id 12345

# List active users
uv run llm-rag-yt bot list-users

# View system alerts
uv run llm-rag-yt bot alerts

# Acknowledge an alert
uv run llm-rag-yt bot ack-alert 123

# Clean up old data
uv run llm-rag-yt bot cleanup
```

## Database Schema

The bot uses SQLite database for comprehensive logging and management:

### Tables Created

- **youtube_requests**: Track YouTube URL processing requests
- **audio_files**: Monitor audio file processing pipeline
- **user_queries**: Log all user questions and responses
- **api_log**: Record API calls and performance metrics
- **user_activity**: Track user sessions and actions
- **feedback**: Store user ratings and feedback
- **pipeline_jobs**: Manage background processing jobs
- **system_alerts**: Store system alerts and notifications

### Example Queries

```sql
-- Get user activity stats
SELECT user_id, COUNT(*) as queries, AVG(response_time_ms) as avg_time
FROM user_queries 
WHERE created_at >= datetime('now', '-7 days')
GROUP BY user_id;

-- Check processing pipeline health
SELECT status, COUNT(*) as count 
FROM youtube_requests 
GROUP BY status;
```

## Progress Tracking

The bot provides sophisticated progress tracking:

### Processing Steps

1. **Validating URL** (0%)
2. **Downloading audio** (20%)
3. **Transcribing audio** (50%)
4. **Processing text** (70%)
5. **Creating embeddings** (90%)
6. **Finalizing** (100%)

### Visual Indicators

- **Progress Bars**: `[████████░░] 80%`
- **Status Icons**: 🔄 🎤 📝 🧮 ✅
- **Timestamps**: Verbose mode shows timing information
- **Error Messages**: Clear error reporting with retry options

## Advanced Features

### Feedback System

Users can rate responses to improve the system:
- 👍 Good response
- 👎 Poor response  
- 🔍 Request more details

All feedback is stored and can be analyzed for system improvement.

### Session Management

- **User Sessions**: Track active users and their current tasks
- **Task Cancellation**: Users can cancel long-running operations
- **Context Preservation**: Maintain conversation context
- **Cleanup**: Automatic cleanup of stale sessions

### Alert Integration

The bot can send system alerts to administrators:
- Processing failures
- High error rates
- Resource exhaustion
- Performance degradation

## Monitoring and Analytics

### User Statistics

```bash
# View bot analytics
uv run llm-rag-yt bot status
```

Displays:
- Total users and queries
- Average response times
- Success/failure rates
- Storage usage
- Processing queue status

### System Health

The bot monitors:
- ✅ Database connectivity
- ✅ Vector store health
- ✅ Processing pipeline status
- ✅ Resource usage
- ✅ Error rates

## Integration with Dagster

The Telegram bot integrates seamlessly with the Dagster pipeline:

- **Sensors**: Dagster sensors monitor the database for new requests
- **Assets**: Processing jobs are tracked as Dagster assets
- **Alerts**: System alerts are generated through Dagster monitoring

See [DAGSTER-PIPELINE.md](DAGSTER-PIPELINE.md) for more details.

## Troubleshooting

### Common Issues

**Bot not responding:**
```bash
# Check bot token
curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe

# Check bot status
uv run llm-rag-yt bot status
```

**Database errors:**
```bash
# Clean up database
uv run llm-rag-yt bot cleanup

# Check database integrity
sqlite3 data/telegram_bot.db ".schema"
```

**Permission errors:**
- Ensure bot token has correct permissions
- Check file system permissions for data directory
- Verify OpenAI API key is valid

### Logs

Bot logs are available in:
- Console output (when running manually)
- System logs (when running as service)
- Telegram alerts (for critical errors)

## Production Deployment

### Using systemd (Linux)

Create `/etc/systemd/system/telegram-bot.service`:

```ini
[Unit]
Description=YouTube RAG Telegram Bot
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/llm-rag-from-yt
Environment=BOT_TOKEN=your_token_here
Environment=OPENAI_API_KEY=your_key_here
ExecStart=/path/to/venv/bin/python scripts/telegram_bot_runner.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
sudo systemctl status telegram-bot
```

### Using Docker

```bash
# Build image
docker build -t rag-telegram-bot .

# Run bot
docker run -d \
  --name rag-bot \
  -e BOT_TOKEN=your_token \
  -e OPENAI_API_KEY=your_key \
  -v $(pwd)/data:/app/data \
  rag-telegram-bot \
  python scripts/telegram_bot_runner.py
```

### Environment Variables

Required:
- `BOT_TOKEN`: Telegram bot token
- `OPENAI_API_KEY`: OpenAI API key for RAG queries

Optional:
- `TELEGRAM_ADMIN_CHAT_ID`: Admin chat for system alerts
- `USE_FAKE_ASR`: Use fake transcription for testing
- `VERBOSE_BY_DEFAULT`: Enable verbose mode for all users

## Security Considerations

- **Token Security**: Never commit bot tokens to version control
- **User Validation**: Consider implementing user whitelist for production
- **Rate Limiting**: Bot implements basic rate limiting
- **Data Privacy**: User queries are logged for system improvement
- **Admin Access**: Separate admin commands from user commands

## API Integration

The bot can be integrated with external systems:

```python
from llm_rag_yt.telegram.database import TelegramDatabase

# Add URL programmatically
db = TelegramDatabase()
db.log_youtube_request(
    user_id=12345,
    url="https://youtube.com/watch?v=abc123",
    status="pending"
)
```

This enables integration with webhooks, scheduled jobs, and other automation systems.