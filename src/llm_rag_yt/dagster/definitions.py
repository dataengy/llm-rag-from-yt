"""
Dagster definitions for the YouTube RAG pipeline.
"""

from dagster import DefaultScheduleStatus, Definitions, ScheduleDefinition

from .assets import (
    downloaded_audio_files,
    embedded_content,
    pipeline_metrics,
    system_alerts,
    transcribed_audio_files,
    unprocessed_audio_files,
    youtube_urls_to_process,
)
from .jobs import (
    audio_processing_job,
    cleanup_job,
    health_check_job,
    pipeline_monitoring_job,
    telegram_alert_job,
    youtube_processing_job,
)
from .sensors import (
    audio_file_sensor,
    cleanup_sensor,
    pipeline_health_sensor,
    telegram_alert_sensor,
    youtube_url_sensor,
)

# Define schedules for regular jobs
monitoring_schedule = ScheduleDefinition(
    job=pipeline_monitoring_job,
    cron_schedule="*/10 * * * *",  # Every 10 minutes
    default_status=DefaultScheduleStatus.RUNNING,
)

health_check_schedule = ScheduleDefinition(
    job=health_check_job,
    cron_schedule="*/5 * * * *",  # Every 5 minutes
    default_status=DefaultScheduleStatus.RUNNING,
)

cleanup_schedule = ScheduleDefinition(
    job=cleanup_job,
    cron_schedule="0 2 * * *",  # Daily at 2 AM
    default_status=DefaultScheduleStatus.STOPPED,  # Start manually
)


# Dagster definitions
defs = Definitions(
    # Assets
    assets=[
        youtube_urls_to_process,
        downloaded_audio_files,
        unprocessed_audio_files,
        transcribed_audio_files,
        embedded_content,
        pipeline_metrics,
        system_alerts,
    ],
    # Jobs
    jobs=[
        youtube_processing_job,
        audio_processing_job,
        pipeline_monitoring_job,
        telegram_alert_job,
        cleanup_job,
        health_check_job,
    ],
    # Sensors
    sensors=[
        youtube_url_sensor,
        audio_file_sensor,
        pipeline_health_sensor,
        cleanup_sensor,
        telegram_alert_sensor,
    ],
    # Schedules
    schedules=[monitoring_schedule, health_check_schedule, cleanup_schedule],
)
