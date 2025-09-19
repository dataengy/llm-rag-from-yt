"""
Dagster assets for the YouTube RAG pipeline.
"""

import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from dagster import AssetExecutionContext, Config, MetadataValue, asset

from .._common.config.settings import Config as RAGConfig
from ..audio.downloader import YouTubeDownloader
from ..audio.transcriber import AudioTranscriber
from ..pipeline import RAGPipeline
from ..telegram.database import TelegramDatabase


class YouTubeProcessingConfig(Config):
    """Configuration for YouTube processing assets."""

    urls: list[str]
    language: str = "auto"
    use_fake_asr: bool = False


class AudioProcessingConfig(Config):
    """Configuration for audio processing assets."""

    input_directory: str = "data/audio"
    language: str = "auto"


@asset(group_name="ingestion")
def youtube_urls_to_process(context: AssetExecutionContext) -> pd.DataFrame:
    """Get YouTube URLs that need processing from the database."""
    db = TelegramDatabase()
    pending_requests = db.get_pending_youtube_requests()

    if not pending_requests:
        context.log.info("No pending YouTube requests found")
        return pd.DataFrame(columns=["id", "user_id", "url", "created_at"])

    df = pd.DataFrame(pending_requests)
    context.log.info(f"Found {len(df)} pending YouTube requests")

    context.add_output_metadata(
        {
            "num_requests": len(df),
            "preview": MetadataValue.md(df.head().to_markdown()),
        }
    )

    return df


@asset(group_name="ingestion", deps=[youtube_urls_to_process])
def downloaded_audio_files(
    context: AssetExecutionContext, youtube_urls_to_process: pd.DataFrame
) -> pd.DataFrame:
    """Download audio files from YouTube URLs."""
    downloader = YouTubeDownloader(Path("data/audio"))
    db = TelegramDatabase()
    results = []

    for _, row in youtube_urls_to_process.iterrows():
        try:
            context.log.info(f"Downloading audio from {row['url']}")

            # Update status to processing
            db.update_youtube_request_status(row["id"], "processing")

            # Download audio
            audio_info = downloader.download(row["url"])
            
            if not audio_info:
                raise Exception("Download failed - no audio info returned")

            # Calculate file hash for deduplication
            file_hash = _calculate_file_hash(audio_info["file_path"])

            # Register audio file in database
            db.register_audio_file(
                file_path=audio_info["file_path"],
                file_size=os.path.getsize(audio_info["file_path"]),
                file_hash=file_hash,
                metadata={
                    "youtube_url": row["url"],
                    "title": audio_info.get("title"),
                    "duration": audio_info.get("duration"),
                    "user_id": row["user_id"],
                },
            )

            results.append(
                {
                    "request_id": row["id"],
                    "user_id": row["user_id"],
                    "url": row["url"],
                    "file_path": audio_info["file_path"],
                    "title": audio_info.get("title"),
                    "duration": audio_info.get("duration"),
                    "file_size": os.path.getsize(audio_info["file_path"]),
                    "file_hash": file_hash,
                    "status": "downloaded",
                    "downloaded_at": datetime.now(),
                }
            )

            # Update request status
            db.update_youtube_request_status(row["id"], "downloaded")

        except Exception as e:
            context.log.error(f"Failed to download {row['url']}: {e}")

            # Update request status with error
            db.update_youtube_request_status(row["id"], "failed", str(e))

            results.append(
                {
                    "request_id": row["id"],
                    "user_id": row["user_id"],
                    "url": row["url"],
                    "file_path": None,
                    "status": "failed",
                    "error": str(e),
                    "downloaded_at": datetime.now(),
                }
            )

    df = pd.DataFrame(results)

    context.add_output_metadata(
        {
            "num_files": len(df),
            "successful_downloads": len(df[df["status"] == "downloaded"]),
            "failed_downloads": len(df[df["status"] == "failed"]),
            "total_size_mb": df[df["status"] == "downloaded"]["file_size"].sum()
            / (1024 * 1024),
        }
    )

    return df


@asset(group_name="processing")
def unprocessed_audio_files(context: AssetExecutionContext) -> pd.DataFrame:
    """Get audio files that need transcription processing."""
    db = TelegramDatabase()
    unprocessed_files = db.get_unprocessed_audio_files()

    if not unprocessed_files:
        context.log.info("No unprocessed audio files found")
        return pd.DataFrame(columns=["id", "file_path", "file_size", "created_at"])

    df = pd.DataFrame(unprocessed_files)
    context.log.info(f"Found {len(df)} unprocessed audio files")

    context.add_output_metadata(
        {
            "num_files": len(df),
            "total_size_mb": df["file_size"].sum() / (1024 * 1024),
            "oldest_file": df["created_at"].min(),
        }
    )

    return df


@asset(group_name="processing", deps=[unprocessed_audio_files])
def transcribed_audio_files(
    context: AssetExecutionContext, unprocessed_audio_files: pd.DataFrame
) -> pd.DataFrame:
    """Transcribe audio files to text."""
    config = RAGConfig()
    transcriber = AudioTranscriber(config)
    db = TelegramDatabase()
    results = []

    for _, row in unprocessed_audio_files.iterrows():
        try:
            context.log.info(f"Transcribing {row['file_path']}")

            # Update status to processing
            db.update_audio_file_status(row["file_path"], "transcribing")

            # Transcribe audio
            transcript = transcriber.transcribe_audio(row["file_path"], language="auto")

            # Save transcript to file
            transcript_path = row["file_path"].replace(".mp3", ".txt")
            with open(transcript_path, "w", encoding="utf-8") as f:
                f.write(transcript)

            # Update database
            db.update_audio_file_status(
                row["file_path"], "transcribed", transcription_path=transcript_path
            )

            results.append(
                {
                    "file_path": row["file_path"],
                    "transcript_path": transcript_path,
                    "transcript_length": len(transcript),
                    "word_count": len(transcript.split()),
                    "status": "transcribed",
                    "transcribed_at": datetime.now(),
                }
            )

        except Exception as e:
            context.log.error(f"Failed to transcribe {row['file_path']}: {e}")

            # Update status with error
            db.update_audio_file_status(row["file_path"], "failed")

            results.append(
                {
                    "file_path": row["file_path"],
                    "status": "failed",
                    "error": str(e),
                    "transcribed_at": datetime.now(),
                }
            )

    df = pd.DataFrame(results)

    context.add_output_metadata(
        {
            "num_files": len(df),
            "successful_transcriptions": len(df[df["status"] == "transcribed"]),
            "failed_transcriptions": len(df[df["status"] == "failed"]),
            "total_words": df[df["status"] == "transcribed"]["word_count"].sum(),
            "avg_transcript_length": df[df["status"] == "transcribed"][
                "transcript_length"
            ].mean(),
        }
    )

    return df


@asset(group_name="processing", deps=[transcribed_audio_files])
def embedded_content(
    context: AssetExecutionContext, transcribed_audio_files: pd.DataFrame
) -> pd.DataFrame:
    """Create embeddings and store in vector database."""
    config = RAGConfig()
    pipeline = RAGPipeline(config)
    db = TelegramDatabase()
    results = []

    for _, row in transcribed_audio_files.iterrows():
        if row["status"] != "transcribed":
            continue

        try:
            context.log.info(f"Creating embeddings for {row['file_path']}")

            # Update status
            db.update_audio_file_status(
                row["file_path"], "transcribed", embedding_status="processing"
            )

            # Read transcript
            with open(row["transcript_path"], encoding="utf-8") as f:
                transcript = f.read()

            # Process and store in vector database
            pipeline.process_text(transcript, source_file=row["file_path"])

            # Update database
            db.update_audio_file_status(
                row["file_path"], "completed", embedding_status="completed"
            )

            results.append(
                {
                    "file_path": row["file_path"],
                    "transcript_path": row["transcript_path"],
                    "status": "embedded",
                    "embedded_at": datetime.now(),
                }
            )

        except Exception as e:
            context.log.error(
                f"Failed to create embeddings for {row['file_path']}: {e}"
            )

            # Update status with error
            db.update_audio_file_status(
                row["file_path"], "transcribed", embedding_status="failed"
            )

            results.append(
                {
                    "file_path": row["file_path"],
                    "status": "failed",
                    "error": str(e),
                    "embedded_at": datetime.now(),
                }
            )

    df = pd.DataFrame(results)

    context.add_output_metadata(
        {
            "num_files": len(df),
            "successful_embeddings": len(df[df["status"] == "embedded"]),
            "failed_embeddings": len(df[df["status"] == "failed"]),
        }
    )

    return df


@asset(group_name="monitoring")
def pipeline_metrics(context: AssetExecutionContext) -> dict[str, Any]:
    """Collect pipeline performance metrics."""
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

    context.add_output_metadata(
        {
            "youtube_requests": MetadataValue.json(
                processing_stats.get("youtube_requests", {})
            ),
            "audio_files": MetadataValue.json(processing_stats.get("audio_files", {})),
            "pipeline_jobs": MetadataValue.json(
                processing_stats.get("pipeline_jobs", {})
            ),
            "user_activity": MetadataValue.json(user_stats),
        }
    )

    return metrics


@asset(group_name="monitoring", deps=[pipeline_metrics])
def system_alerts(
    context: AssetExecutionContext, pipeline_metrics: dict[str, Any]
) -> pd.DataFrame:
    """Generate system alerts based on metrics."""
    db = TelegramDatabase()
    alerts = []

    processing_stats = pipeline_metrics["processing_stats"]

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

    df = pd.DataFrame(alerts)

    context.add_output_metadata(
        {
            "num_alerts": len(alerts),
            "alert_types": list(df["type"].unique()) if len(df) > 0 else [],
        }
    )

    return df


def _calculate_file_hash(file_path: str) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()
