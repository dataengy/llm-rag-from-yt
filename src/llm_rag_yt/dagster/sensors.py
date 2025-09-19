"""
Dagster sensors for the YouTube RAG pipeline.
"""

from datetime import datetime, timedelta
from pathlib import Path

from dagster import (
    DefaultSensorStatus,
    RunRequest,
    SensorEvaluationContext,
    SensorResult,
    SkipReason,
    sensor,
)

from ..telegram.database import TelegramDatabase


@sensor(
    job_name="youtube_processing_job",
    default_status=DefaultSensorStatus.RUNNING,
    minimum_interval_seconds=30,
    description="Monitors for new YouTube URLs to process",
)
def youtube_url_sensor(context: SensorEvaluationContext) -> SensorResult:
    """Sensor that triggers when new YouTube URLs are added to the database."""
    db = TelegramDatabase()

    try:
        # Get pending YouTube requests
        pending_requests = db.get_pending_youtube_requests()

        if not pending_requests:
            return SkipReason("No pending YouTube requests found")

        # Create run requests for pending URLs
        run_requests = []
        for request in pending_requests[:5]:  # Process max 5 at a time
            run_config = {
                "ops": {
                    "youtube_urls_to_process": {
                        "config": {
                            "urls": [request["url"]],
                            "user_id": request["user_id"],
                        }
                    }
                }
            }

            run_requests.append(
                RunRequest(
                    run_key=f"youtube_processing_{request['id']}",
                    run_config=run_config,
                    tags={
                        "user_id": str(request["user_id"]),
                        "url": request["url"],
                        "request_id": str(request["id"]),
                    },
                )
            )

            context.log.info(f"Triggering processing for YouTube URL: {request['url']}")

        return SensorResult(run_requests=run_requests, skip_reason=None)

    except Exception as e:
        context.log.error(f"Error in youtube_url_sensor: {e}")
        return SkipReason(f"Sensor error: {str(e)}")


@sensor(
    job_name="audio_processing_job",
    default_status=DefaultSensorStatus.RUNNING,
    minimum_interval_seconds=60,
    description="Monitors for new audio files to process",
)
def audio_file_sensor(context: SensorEvaluationContext) -> SensorResult:
    """Sensor that triggers when new audio files are detected."""
    audio_dir = Path("data/audio")

    if not audio_dir.exists():
        return SkipReason("Audio directory does not exist")

    try:
        # Get all MP3 files in the audio directory
        audio_files = list(audio_dir.glob("*.mp3"))

        if not audio_files:
            return SkipReason("No audio files found")

        db = TelegramDatabase()
        new_files = []

        # Check which files are not in the database yet
        for audio_file in audio_files:
            # Calculate basic metadata
            file_stats = audio_file.stat()
            file_size = file_stats.st_size
            file_hash = _calculate_simple_hash(
                str(audio_file), file_size, file_stats.st_mtime
            )

            # Try to register the file (will fail if already exists)
            if db.register_audio_file(
                file_path=str(audio_file),
                file_size=file_size,
                file_hash=file_hash,
                metadata={
                    "detected_by": "audio_file_sensor",
                    "detected_at": datetime.now().isoformat(),
                },
            ):
                new_files.append(str(audio_file))
                context.log.info(f"New audio file detected: {audio_file}")

        if not new_files:
            return SkipReason("No new audio files to process")

        # Create run request for new files
        run_config = {
            "ops": {
                "unprocessed_audio_files": {"config": {"input_directory": "data/audio"}}
            }
        }

        return SensorResult(
            run_requests=[
                RunRequest(
                    run_key=f"audio_processing_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    run_config=run_config,
                    tags={
                        "file_count": str(len(new_files)),
                        "trigger": "audio_file_sensor",
                    },
                )
            ]
        )

    except Exception as e:
        context.log.error(f"Error in audio_file_sensor: {e}")
        return SkipReason(f"Sensor error: {str(e)}")


@sensor(
    job_name="pipeline_monitoring_job",
    default_status=DefaultSensorStatus.RUNNING,
    minimum_interval_seconds=300,  # Run every 5 minutes
    description="Monitors pipeline health and generates alerts",
)
def pipeline_health_sensor(context: SensorEvaluationContext) -> SensorResult:
    """Sensor that monitors pipeline health and triggers alerting."""
    try:
        db = TelegramDatabase()

        # Check for unacknowledged alerts
        alerts = db.get_unacknowledged_alerts()

        # Check for old processing jobs that might be stuck
        processing_stats = db.get_processing_stats()

        should_run_monitoring = False
        run_tags = {}

        # Trigger if there are unacknowledged alerts
        if alerts:
            should_run_monitoring = True
            run_tags["unacknowledged_alerts"] = str(len(alerts))
            context.log.warning(f"Found {len(alerts)} unacknowledged alerts")

        # Trigger if there are too many failed jobs
        failed_jobs = processing_stats.get("pipeline_jobs", {}).get("failed", 0)
        if failed_jobs > 5:
            should_run_monitoring = True
            run_tags["failed_jobs"] = str(failed_jobs)
            context.log.warning(f"High number of failed jobs: {failed_jobs}")

        # Trigger if there are old pending requests (older than 1 hour)
        pending_requests = db.get_pending_youtube_requests()
        old_requests = [
            r
            for r in pending_requests
            if datetime.fromisoformat(r["created_at"])
            < datetime.now() - timedelta(hours=1)
        ]

        if old_requests:
            should_run_monitoring = True
            run_tags["old_pending_requests"] = str(len(old_requests))
            context.log.warning(f"Found {len(old_requests)} old pending requests")

        if not should_run_monitoring:
            return SkipReason("Pipeline health is good")

        return SensorResult(
            run_requests=[
                RunRequest(
                    run_key=f"pipeline_monitoring_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    tags=run_tags,
                )
            ]
        )

    except Exception as e:
        context.log.error(f"Error in pipeline_health_sensor: {e}")
        return SkipReason(f"Sensor error: {str(e)}")


@sensor(
    job_name="cleanup_job",
    default_status=DefaultSensorStatus.STOPPED,  # Manual start
    minimum_interval_seconds=3600,  # Run every hour when enabled
    description="Cleans up old files and database records",
)
def cleanup_sensor(context: SensorEvaluationContext) -> SensorResult:
    """Sensor for periodic cleanup tasks."""
    try:
        # Check if cleanup is needed
        audio_dir = Path("data/audio")
        if not audio_dir.exists():
            return SkipReason("Audio directory does not exist")

        # Count files
        audio_files = list(audio_dir.glob("*.mp3"))
        transcript_files = list(audio_dir.glob("*.txt"))

        # Calculate total size
        total_size_mb = sum(
            f.stat().st_size for f in audio_files + transcript_files
        ) / (1024 * 1024)

        # Trigger cleanup if total size exceeds threshold (e.g., 1GB)
        if total_size_mb > 1024:
            context.log.info(
                f"Audio directory size ({total_size_mb:.1f} MB) exceeds threshold, triggering cleanup"
            )

            return SensorResult(
                run_requests=[
                    RunRequest(
                        run_key=f"cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        tags={
                            "total_size_mb": str(int(total_size_mb)),
                            "file_count": str(len(audio_files) + len(transcript_files)),
                        },
                    )
                ]
            )

        return SkipReason(f"No cleanup needed (size: {total_size_mb:.1f} MB)")

    except Exception as e:
        context.log.error(f"Error in cleanup_sensor: {e}")
        return SkipReason(f"Sensor error: {str(e)}")


@sensor(
    job_name="telegram_alert_job",
    default_status=DefaultSensorStatus.RUNNING,
    minimum_interval_seconds=120,  # Check every 2 minutes
    description="Sends alerts to Telegram bot",
)
def telegram_alert_sensor(context: SensorEvaluationContext) -> SensorResult:
    """Sensor that sends system alerts to Telegram."""
    try:
        db = TelegramDatabase()

        # Get high-severity unacknowledged alerts
        alerts = db.get_unacknowledged_alerts()
        critical_alerts = [a for a in alerts if a["severity"] in ["error", "critical"]]

        if not critical_alerts:
            return SkipReason("No critical alerts to send")

        # Create run request to send alerts
        run_config = {
            "ops": {
                "send_telegram_alerts": {
                    "config": {"alert_ids": [a["id"] for a in critical_alerts]}
                }
            }
        }

        context.log.warning(
            f"Triggering Telegram alerts for {len(critical_alerts)} critical alerts"
        )

        return SensorResult(
            run_requests=[
                RunRequest(
                    run_key=f"telegram_alerts_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    run_config=run_config,
                    tags={
                        "alert_count": str(len(critical_alerts)),
                        "severity": "critical",
                    },
                )
            ]
        )

    except Exception as e:
        context.log.error(f"Error in telegram_alert_sensor: {e}")
        return SkipReason(f"Sensor error: {str(e)}")


def _calculate_simple_hash(file_path: str, file_size: int, mtime: float) -> str:
    """Calculate a simple hash based on file metadata."""
    import hashlib

    content = f"{file_path}_{file_size}_{mtime}"
    return hashlib.md5(content.encode()).hexdigest()
