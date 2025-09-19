"""
Dagster jobs for the YouTube RAG pipeline.
"""

from datetime import datetime
from typing import Any

from dagster import (
    Field,
    In,
    Int,
    Nothing,
    OpExecutionContext,
    Out,
    String,
    job,
    op,
)

from ..telegram.database import TelegramDatabase
# Note: Assets should not be imported into jobs directly
# Assets and jobs operate in different execution contexts in Dagster


@op(
    config_schema={
        "alert_ids": Field([Int], description="List of alert IDs to send"),
        "bot_token": Field(String, is_required=False, description="Telegram bot token"),
    },
    ins={"start": In(Nothing)},
    out=Out(dict[str, Any]),
)
def send_telegram_alerts(context: OpExecutionContext) -> dict[str, Any]:
    """Send system alerts to Telegram bot."""
    config = context.op_config
    db = TelegramDatabase()

    alert_ids = config["alert_ids"]
    bot_token = config.get("bot_token") or context.resources.get("telegram_bot_token")

    if not bot_token:
        context.log.warning("No Telegram bot token configured, skipping alert sending")
        return {"status": "skipped", "reason": "no_bot_token"}

    try:
        results = []

        for alert_id in alert_ids:
            # Get alert details from database
            with db.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM system_alerts WHERE id = ?", (alert_id,)
                )
                alert = cursor.fetchone()

            if not alert:
                context.log.warning(f"Alert {alert_id} not found")
                continue

            # Format alert message
            alert_message = _format_alert_message(dict(alert))

            # TODO: Send to Telegram bot
            # For now, just log the alert
            context.log.error(f"ALERT: {alert_message}")

            # Mark alert as acknowledged
            db.acknowledge_alert(alert_id)

            results.append(
                {"alert_id": alert_id, "status": "sent", "message": alert_message}
            )

        return {"status": "completed", "alerts_sent": len(results), "results": results}

    except Exception as e:
        context.log.error(f"Error sending Telegram alerts: {e}")
        return {"status": "failed", "error": str(e)}


@op(ins={"start": In(Nothing)}, out=Out(dict[str, Any]))
def cleanup_old_files(context: OpExecutionContext) -> dict[str, Any]:
    """Clean up old audio files and database records."""
    import os
    from datetime import datetime, timedelta
    from pathlib import Path

    try:
        audio_dir = Path("data/audio")
        if not audio_dir.exists():
            return {"status": "skipped", "reason": "no_audio_directory"}

        # Get files older than 7 days
        cutoff_date = datetime.now() - timedelta(days=7)
        old_files = []

        for file_path in audio_dir.iterdir():
            if file_path.is_file():
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_mtime < cutoff_date:
                    old_files.append(file_path)

        # Remove old files
        removed_count = 0
        freed_space_mb = 0

        for file_path in old_files:
            try:
                file_size = file_path.stat().st_size
                os.remove(file_path)
                removed_count += 1
                freed_space_mb += file_size / (1024 * 1024)
                context.log.info(f"Removed old file: {file_path}")
            except Exception as e:
                context.log.warning(f"Failed to remove {file_path}: {e}")

        # Clean up old database records
        db = TelegramDatabase()
        with db.get_connection() as conn:
            # Remove old completed jobs
            conn.execute("""
                DELETE FROM pipeline_jobs
                WHERE status = 'completed' AND completed_at < datetime('now', '-7 days')
            """)

            # Remove old acknowledged alerts
            conn.execute("""
                DELETE FROM system_alerts
                WHERE acknowledged = TRUE AND acknowledged_at < datetime('now', '-7 days')
            """)

            conn.commit()

        return {
            "status": "completed",
            "files_removed": removed_count,
            "space_freed_mb": round(freed_space_mb, 2),
            "old_files_count": len(old_files),
        }

    except Exception as e:
        context.log.error(f"Error during cleanup: {e}")
        return {"status": "failed", "error": str(e)}


@op(ins={"start": In(Nothing)}, out=Out(dict[str, Any]))
def health_check(context: OpExecutionContext) -> dict[str, Any]:
    """Perform system health check."""
    from pathlib import Path

    import psutil

    try:
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "status": "healthy",
            "checks": {},
        }

        # Check disk space
        audio_dir = Path("data/audio")
        if audio_dir.exists():
            disk_usage = psutil.disk_usage(str(audio_dir))
            free_space_gb = disk_usage.free / (1024**3)
            health_status["checks"]["disk_space"] = {
                "free_gb": round(free_space_gb, 2),
                "status": "ok" if free_space_gb > 1 else "warning",
            }

        # Check database connectivity
        try:
            db = TelegramDatabase()
            stats = db.get_processing_stats()
            health_status["checks"]["database"] = {"status": "ok", "stats": stats}
        except Exception as e:
            health_status["checks"]["database"] = {"status": "error", "error": str(e)}
            health_status["status"] = "unhealthy"

        # Check vector store
        try:
            from .._common.config.settings import Config
            from ..vectorstore.chroma import ChromaVectorStore

            config = Config()
            vector_store = ChromaVectorStore(config)
            doc_count = vector_store.get_collection_size()
            health_status["checks"]["vector_store"] = {
                "status": "ok",
                "document_count": doc_count,
            }
        except Exception as e:
            health_status["checks"]["vector_store"] = {
                "status": "warning",
                "error": str(e),
            }

        return health_status

    except Exception as e:
        context.log.error(f"Error during health check: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


# Note: YouTube and audio processing are handled by assets
# These jobs are commented out as they incorrectly mixed assets and ops
# Use asset-based execution instead for YouTube and audio processing workflows

# @job
# def youtube_processing_job():
#     """Job for processing YouTube URLs - use assets instead."""
#     pass

# @job
# def audio_processing_job():
#     """Job for processing audio files - use assets instead."""
#     pass


@op(out=Out(dict[str, Any]))
def pipeline_metrics_op(context: OpExecutionContext) -> dict[str, Any]:
    """Collect pipeline performance metrics."""
    from ..telegram.database import TelegramDatabase
    from pathlib import Path
    
    db = TelegramDatabase()

    # Get processing stats
    processing_stats = db.get_processing_stats()

    # Get user stats for last 7 days
    user_stats = db.get_user_stats(days=7)

    # Get file counts from filesystem
    audio_dir = Path("data/audio")
    audio_files = list(audio_dir.glob("*.mp3")) if audio_dir.exists() else []
    transcript_files = list(audio_dir.glob("*.txt")) if audio_dir.exists() else []

    metrics = {
        "timestamp": datetime.now().isoformat(),
        "processing_stats": processing_stats,
        "user_stats": user_stats,
        "filesystem": {
            "audio_files_count": len(audio_files),
            "transcript_files_count": len(transcript_files),
            "audio_total_size_mb": sum(f.stat().st_size for f in audio_files)
            / (1024 * 1024),
        },
    }

    context.log.info(f"Collected pipeline metrics: {metrics}")
    return metrics


@op(ins={"metrics": In(dict)}, out=Out(dict[str, Any]))
def system_alerts_op(context: OpExecutionContext, metrics: dict[str, Any]) -> dict[str, Any]:
    """Generate system alerts based on metrics."""
    from ..telegram.database import TelegramDatabase
    
    db = TelegramDatabase()
    alerts = []

    processing_stats = metrics["processing_stats"]

    # Check for failed YouTube requests
    failed_requests = processing_stats.get("youtube_requests", {}).get("failed", 0)
    if failed_requests > 5:
        db.create_alert(
            "processing_failures",
            "warning",
            f"High number of failed YouTube requests: {failed_requests}",
            {"count": failed_requests, "threshold": 5},
        )
        alerts.append(
            {
                "type": "processing_failures",
                "severity": "warning",
                "message": f"High number of failed YouTube requests: {failed_requests}",
                "created_at": datetime.now(),
            }
        )

    # Check for stale audio files
    failed_audio = processing_stats.get("audio_files", {}).get("failed", 0)
    if failed_audio > 3:
        db.create_alert(
            "audio_processing_failures",
            "error",
            f"High number of failed audio processing: {failed_audio}",
            {"count": failed_audio, "threshold": 3},
        )
        alerts.append(
            {
                "type": "audio_processing_failures",
                "severity": "error",
                "message": f"High number of failed audio processing: {failed_audio}",
                "created_at": datetime.now(),
            }
        )

    # Check for pending jobs backlog
    pending_jobs = processing_stats.get("pipeline_jobs", {}).get("pending", 0)
    if pending_jobs > 10:
        db.create_alert(
            "job_backlog",
            "warning",
            f"High number of pending pipeline jobs: {pending_jobs}",
            {"count": pending_jobs, "threshold": 10},
        )
        alerts.append(
            {
                "type": "job_backlog",
                "severity": "warning",
                "message": f"High number of pending pipeline jobs: {pending_jobs}",
                "created_at": datetime.now(),
            }
        )

    context.log.info(f"Generated {len(alerts)} alerts")
    return {"alerts": alerts, "total_count": len(alerts)}


@job
def pipeline_monitoring_job():
    """Job for monitoring pipeline health and generating alerts."""
    metrics = pipeline_metrics_op()
    system_alerts_op(metrics)


@job
def telegram_alert_job():
    """Job for sending alerts to Telegram."""
    send_telegram_alerts()


@job
def cleanup_job():
    """Job for cleaning up old files and data."""
    cleanup_old_files()


@job
def health_check_job():
    """Job for performing system health checks."""
    health_check()


def _format_alert_message(alert: dict[str, Any]) -> str:
    """Format an alert for Telegram message."""
    severity_emoji = {"info": "i️", "warning": "⚠️", "error": "❌", "critical": "🚨"}

    emoji = severity_emoji.get(alert["severity"], "📢")

    message = f"""
{emoji} **System Alert**

**Type:** {alert["alert_type"]}
**Severity:** {alert["severity"].upper()}
**Message:** {alert["message"]}
**Time:** {alert["created_at"]}
    """

    if alert.get("details"):
        message += f"\n**Details:** {alert['details']}"

    return message.strip()
