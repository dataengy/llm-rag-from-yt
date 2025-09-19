# Dagster Pipeline Management

## Overview

The YouTube RAG system includes a comprehensive Dagster pipeline for managing data processing workflows, monitoring system health, and automating operations. The pipeline provides:

- **Asset-based Architecture**: Data assets for each processing stage
- **Sensor-driven Processing**: Automatic detection and processing of new content
- **Comprehensive Monitoring**: Health checks, metrics, and alerting
- **Scheduled Operations**: Automated cleanup and maintenance
- **Web Interface**: Visual pipeline monitoring and management

## Architecture

### Assets

The pipeline is organized into logical asset groups:

#### Ingestion Assets
- **youtube_urls_to_process**: Fetches pending YouTube URLs from database
- **downloaded_audio_files**: Downloads audio from YouTube URLs

#### Processing Assets  
- **unprocessed_audio_files**: Identifies audio files needing transcription
- **transcribed_audio_files**: Transcribes audio to text using Whisper
- **embedded_content**: Creates embeddings and stores in vector database

#### Monitoring Assets
- **pipeline_metrics**: Collects system performance metrics
- **system_alerts**: Generates alerts based on metrics and thresholds

### Sensors

Automated sensors monitor for changes and trigger processing:

| Sensor | Interval | Purpose |
|--------|----------|---------|
| `youtube_url_sensor` | 30s | Detects new YouTube URLs in database |
| `audio_file_sensor` | 60s | Monitors filesystem for new audio files |
| `pipeline_health_sensor` | 5m | Checks system health and generates alerts |
| `cleanup_sensor` | 1h | Triggers cleanup when storage thresholds exceeded |
| `telegram_alert_sensor` | 2m | Sends critical alerts to Telegram |

### Jobs

Orchestrated workflows for different operations:

- **youtube_processing_job**: Complete YouTube URL → audio → transcription pipeline
- **audio_processing_job**: Audio file → transcription → embeddings
- **pipeline_monitoring_job**: Health checks and metrics collection
- **telegram_alert_job**: Alert distribution via Telegram
- **cleanup_job**: File and database cleanup
- **health_check_job**: System health validation

## Setup

### 1. Installation

Dagster dependencies are included in the main project:

```bash
# Install all dependencies including Dagster
uv sync

# Or install Dagster separately
pip install dagster>=1.5.0 dagster-webserver>=1.5.0
```

### 2. Configuration

Dagster uses environment variables and configuration files:

```bash
# Set Dagster home directory
export DAGSTER_HOME=/path/to/project/data/dagster

# Ensure Python path includes src
export PYTHONPATH=/path/to/project/src:$PYTHONPATH
```

### 3. Database Setup

The pipeline uses the same SQLite database as the Telegram bot:

```sql
-- Automatically created tables:
-- pipeline_jobs: Job queue and status tracking
-- system_alerts: System alerts and notifications
-- (plus all Telegram bot tables)
```

## Usage

### Starting Dagster

#### Development Server

```bash
# Method 1: Using CLI command
uv run llm-rag-yt dagster dev

# Method 2: Using runner script  
python scripts/dagster_dev.py

# Method 3: Direct dagster command
export DAGSTER_HOME=data/dagster
dagster dev -f src/llm_rag_yt/dagster/definitions.py --port 3000
```

The web interface will be available at: http://localhost:3000

#### Production Deployment

```bash
# Start Dagster daemon for sensor processing
dagster-daemon run

# Start web server
dagster-webserver -h 0.0.0.0 -p 3000
```

### Managing Jobs

```bash
# List available jobs
uv run llm-rag-yt dagster list-jobs

# Run a specific job
uv run llm-rag-yt dagster run-job youtube_processing_job

# Run with configuration
uv run llm-rag-yt dagster run-job audio_processing_job --config config.yaml
```

### Managing Assets

```bash
# List available assets
uv run llm-rag-yt dagster list-assets

# Materialize specific asset
uv run llm-rag-yt dagster materialize-asset pipeline_metrics

# View sensor status
uv run llm-rag-yt dagster sensor-status
```

## Pipeline Workflows

### YouTube URL Processing

```mermaid
graph TD
    A[YouTube URL Added to DB] --> B[youtube_url_sensor triggers]
    B --> C[youtube_processing_job starts]
    C --> D[youtube_urls_to_process asset]
    D --> E[downloaded_audio_files asset]
    E --> F[Audio file saved to filesystem]
    F --> G[audio_file_sensor triggers]
    G --> H[audio_processing_job starts]
    H --> I[transcribed_audio_files asset]
    I --> J[embedded_content asset]
    J --> K[Content available for queries]
```

### Monitoring Workflow

```mermaid
graph TD
    A[pipeline_health_sensor] --> B[Collect metrics]
    B --> C{Check thresholds}
    C -->|Normal| D[Update metrics asset]
    C -->|Alert needed| E[Create system alert]
    E --> F[telegram_alert_sensor]
    F --> G[Send to Telegram]
    G --> H[Mark alert as sent]
```

## Monitoring and Alerts

### System Metrics

The pipeline collects comprehensive metrics:

```python
{
    "timestamp": "2025-01-19T10:30:00",
    "processing_stats": {
        "youtube_requests": {"pending": 5, "completed": 123, "failed": 2},
        "audio_files": {"pending": 3, "completed": 98, "failed": 1},
        "pipeline_jobs": {"pending": 2, "running": 1, "completed": 245}
    },
    "user_stats": {
        "total_queries": 456,
        "unique_users": 23,
        "avg_response_time_ms": 850
    },
    "filesystem": {
        "audio_files_count": 101,
        "transcript_files_count": 99,
        "audio_total_size_mb": 1024.5
    }
}
```

### Alert Thresholds

Automatic alerts are generated when:

- **Failed YouTube requests** > 5
- **Failed audio processing** > 3  
- **Pending jobs backlog** > 10
- **Old pending requests** > 1 hour
- **Storage usage** > 1GB
- **High error rate** > 10%

### Alert Types

| Type | Severity | Description |
|------|----------|-------------|
| `processing_failures` | warning | High failure rate in processing |
| `audio_processing_failures` | error | Audio transcription issues |
| `job_backlog` | warning | Processing queue backup |
| `storage_full` | error | Storage space exhausted |
| `system_error` | critical | System component failure |

## Configuration

### Job Configuration

Create `config.yaml` for job parameters:

```yaml
ops:
  youtube_urls_to_process:
    config:
      urls: ["https://youtube.com/watch?v=abc123"]
      user_id: 12345
  
  unprocessed_audio_files:
    config:
      input_directory: "data/audio"
      language: "auto"
```

### Asset Configuration

Assets can be configured through the Config classes:

```python
from llm_rag_yt.dagster.assets import YouTubeProcessingConfig

config = YouTubeProcessingConfig(
    urls=["https://youtube.com/watch?v=abc123"],
    language="ru",
    use_fake_asr=False
)
```

### Sensor Configuration

Sensors can be enabled/disabled and configured:

```python
# In definitions.py
youtube_url_sensor = sensor(
    job_name="youtube_processing_job",
    default_status=DefaultSensorStatus.RUNNING,  # or STOPPED
    minimum_interval_seconds=30
)
```

## Data Lineage

Dagster provides automatic data lineage tracking:

```
youtube_urls_to_process 
    ↓
downloaded_audio_files
    ↓
unprocessed_audio_files
    ↓  
transcribed_audio_files
    ↓
embedded_content
    ↓
[Vector Database Updated]
```

Each asset tracks:
- **Dependencies**: Which assets it depends on
- **Metadata**: Processing statistics, file counts, sizes
- **Materialization History**: When and how assets were created
- **Performance Metrics**: Processing time, success rates

## Web Interface

The Dagster web interface provides:

### Asset Catalog
- Visual asset dependency graph
- Asset materialization history
- Metadata and statistics for each asset

### Job Execution
- Job run history and status
- Execution logs and error details
- Performance metrics and timing

### Sensor Management
- Sensor status and configuration
- Trigger history and evaluation logs
- Manual sensor triggering

### System Overview
- Overall pipeline health
- Resource utilization
- Alert status and history

## Scheduling

### Built-in Schedules

```python
# Monitor every 10 minutes
monitoring_schedule = ScheduleDefinition(
    job=pipeline_monitoring_job,
    cron_schedule="*/10 * * * *",
    default_status=DefaultScheduleStatus.RUNNING
)

# Health check every 5 minutes
health_check_schedule = ScheduleDefinition(
    job=health_check_job,
    cron_schedule="*/5 * * * *",
    default_status=DefaultScheduleStatus.RUNNING
)

# Daily cleanup at 2 AM
cleanup_schedule = ScheduleDefinition(
    job=cleanup_job,
    cron_schedule="0 2 * * *",
    default_status=DefaultScheduleStatus.STOPPED
)
```

### Custom Schedules

Create custom schedules for specific operations:

```python
from dagster import ScheduleDefinition

daily_report_schedule = ScheduleDefinition(
    job=generate_daily_report_job,
    cron_schedule="0 9 * * *",  # 9 AM daily
    default_status=DefaultScheduleStatus.RUNNING
)
```

## Integration Points

### Telegram Bot Integration

The pipeline integrates seamlessly with the Telegram bot:

1. **User Request**: User sends YouTube URL to bot
2. **Database Insert**: Bot adds request to database
3. **Sensor Trigger**: `youtube_url_sensor` detects new request
4. **Job Execution**: Processing job runs automatically
5. **Status Updates**: Bot receives status updates through database
6. **Alert Notification**: Critical alerts sent to Telegram

### API Integration

External systems can interact with the pipeline:

```python
from llm_rag_yt.telegram.database import TelegramDatabase

db = TelegramDatabase()

# Add job to queue
job_id = db.add_pipeline_job(
    job_type="youtube_processing",
    job_data={"url": "https://youtube.com/watch?v=abc123"},
    priority=5
)

# Check job status
jobs = db.get_pending_jobs(limit=10)
```

## Troubleshooting

### Common Issues

**Dagster not starting:**
```bash
# Check environment variables
echo $DAGSTER_HOME
echo $PYTHONPATH

# Check asset definitions
dagster asset list -f src/llm_rag_yt/dagster/definitions.py
```

**Sensors not triggering:**
```bash
# Check sensor status
dagster sensor list

# Start sensor manually
dagster sensor start youtube_url_sensor
```

**Job failures:**
```bash
# Check job logs
dagster job logs -j youtube_processing_job

# Re-run failed job
dagster job execute -j youtube_processing_job
```

### Performance Tuning

**Asset Materialization:**
- Use selective asset materialization for faster development
- Configure asset partitioning for large datasets
- Implement incremental asset updates

**Sensor Optimization:**
- Adjust sensor intervals based on workload
- Use sensor context to avoid unnecessary processing
- Implement sensor result caching

**Resource Management:**
- Configure resource limits for jobs
- Use resource tagging for different environments
- Monitor resource utilization through metrics

## Production Deployment

### Docker Deployment

```dockerfile
# Dockerfile for Dagster services
FROM python:3.11

WORKDIR /app
COPY . .
RUN pip install -e .

# Dagster daemon
CMD ["dagster-daemon", "run"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  dagster-daemon:
    build: .
    command: dagster-daemon run
    environment:
      - DAGSTER_HOME=/app/data/dagster
    volumes:
      - ./data:/app/data
  
  dagster-webserver:
    build: .
    command: dagster-webserver -h 0.0.0.0 -p 3000
    ports:
      - "3000:3000"
    environment:
      - DAGSTER_HOME=/app/data/dagster
    volumes:
      - ./data:/app/data
```

### Environment Configuration

Production environment variables:

```bash
# Dagster configuration
export DAGSTER_HOME=/var/lib/dagster
export DAGSTER_LOG_LEVEL=INFO

# Database configuration
export DATABASE_URL=postgresql://user:pass@localhost/dagster

# Resource limits
export DAGSTER_MAX_CONCURRENT_RUNS=5
export DAGSTER_RUN_TIMEOUT=3600
```

### Monitoring

Set up monitoring for production:

- **Health Checks**: HTTP endpoints for load balancer health checks
- **Metrics Export**: Prometheus metrics for monitoring
- **Log Aggregation**: Centralized logging with ELK stack
- **Alert Integration**: PagerDuty/Slack integration for critical alerts

This Dagster pipeline provides a robust, scalable foundation for managing the YouTube RAG processing workflow with comprehensive monitoring, alerting, and automation capabilities.