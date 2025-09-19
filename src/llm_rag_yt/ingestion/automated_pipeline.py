"""Automated ingestion pipeline for continuous YouTube content processing."""

import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from loguru import logger

from .._common.config.settings import Config
from ..pipeline import RAGPipeline


@dataclass
class IngestionJob:
    """Represents an ingestion job."""

    id: str
    urls: list[str]
    status: str = "pending"  # pending, running, completed, failed
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    results: Optional[dict[str, Any]] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class AutomatedIngestionPipeline:
    """Automated ingestion pipeline for processing YouTube content."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize automated pipeline."""
        self.config = config or Config()
        self.pipeline = RAGPipeline(self.config)
        self.jobs_file = self.config.artifacts_dir / "ingestion_jobs.json"
        self.jobs: dict[str, IngestionJob] = self._load_jobs()

        logger.info("Initialized automated ingestion pipeline")

    def _load_jobs(self) -> dict[str, IngestionJob]:
        """Load existing jobs from disk."""
        if not self.jobs_file.exists():
            return {}

        try:
            with open(self.jobs_file, encoding="utf-8") as f:
                jobs_data = json.load(f)

            jobs = {}
            for job_id, job_data in jobs_data.items():
                jobs[job_id] = IngestionJob(**job_data)

            logger.info(f"Loaded {len(jobs)} existing jobs")
            return jobs

        except Exception as e:
            logger.error(f"Failed to load jobs: {e}")
            return {}

    def _save_jobs(self):
        """Save jobs to disk."""
        try:
            self.jobs_file.parent.mkdir(parents=True, exist_ok=True)

            jobs_data = {}
            for job_id, job in self.jobs.items():
                jobs_data[job_id] = asdict(job)

            with open(self.jobs_file, "w", encoding="utf-8") as f:
                json.dump(jobs_data, f, ensure_ascii=False, indent=2)

            logger.debug("Saved jobs to disk")

        except Exception as e:
            logger.error(f"Failed to save jobs: {e}")

    def add_job(self, urls: list[str]) -> str:
        """Add a new ingestion job.

        Args:
            urls: List of YouTube URLs to process

        Returns:
            Job ID
        """
        job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.jobs)}"

        job = IngestionJob(id=job_id, urls=urls)

        self.jobs[job_id] = job
        self._save_jobs()

        logger.info(f"Added ingestion job {job_id} with {len(urls)} URLs")
        return job_id

    def run_job(self, job_id: str) -> dict[str, Any]:
        """Run a specific ingestion job.

        Args:
            job_id: Job ID to run

        Returns:
            Job execution results
        """
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")

        job = self.jobs[job_id]

        if job.status == "running":
            logger.warning(f"Job {job_id} is already running")
            return {"status": "already_running"}

        try:
            # Mark job as running
            job.status = "running"
            job.started_at = datetime.now().isoformat()
            self._save_jobs()

            logger.info(f"Starting ingestion job {job_id}")

            # Run the pipeline
            results = self.pipeline.download_and_process(job.urls)

            # Mark job as completed
            job.status = "completed"
            job.completed_at = datetime.now().isoformat()
            job.results = results
            self._save_jobs()

            logger.info(f"Completed ingestion job {job_id}")
            return {"status": "completed", "results": results}

        except Exception as e:
            # Mark job as failed
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.now().isoformat()
            self._save_jobs()

            logger.error(f"Failed ingestion job {job_id}: {e}")
            return {"status": "failed", "error": str(e)}

    def run_pending_jobs(self) -> dict[str, Any]:
        """Run all pending jobs."""
        pending_jobs = [job for job in self.jobs.values() if job.status == "pending"]

        if not pending_jobs:
            logger.info("No pending jobs to run")
            return {"processed": 0, "results": []}

        logger.info(f"Running {len(pending_jobs)} pending jobs")

        results = []
        for job in pending_jobs:
            result = self.run_job(job.id)
            results.append({"job_id": job.id, "result": result})

        return {"processed": len(pending_jobs), "results": results}

    def schedule_periodic_ingestion(
        self, url_file: Path, check_interval_hours: int = 24
    ) -> None:
        """Schedule periodic ingestion from a URL file.

        Args:
            url_file: File containing YouTube URLs (one per line)
            check_interval_hours: Hours between checks
        """
        logger.info(f"Starting periodic ingestion from {url_file}")

        last_check = datetime.now() - timedelta(hours=check_interval_hours)

        while True:
            try:
                current_time = datetime.now()

                if current_time - last_check >= timedelta(hours=check_interval_hours):
                    logger.info("Checking for new URLs to process")

                    if url_file.exists():
                        with open(url_file, encoding="utf-8") as f:
                            urls = [line.strip() for line in f if line.strip()]

                        if urls:
                            job_id = self.add_job(urls)
                            self.run_job(job_id)

                            # Clear the file after processing
                            url_file.write_text("")

                    last_check = current_time

                # Sleep for 1 hour before next check
                time.sleep(3600)

            except KeyboardInterrupt:
                logger.info("Stopping periodic ingestion")
                break
            except Exception as e:
                logger.error(f"Error in periodic ingestion: {e}")
                time.sleep(300)  # Wait 5 minutes before retry

    def get_job_status(self, job_id: str) -> dict[str, Any]:
        """Get status of a specific job."""
        if job_id not in self.jobs:
            return {"error": f"Job {job_id} not found"}

        job = self.jobs[job_id]
        return asdict(job)

    def list_jobs(self, status_filter: Optional[str] = None) -> list[dict[str, Any]]:
        """List all jobs with optional status filter."""
        jobs = list(self.jobs.values())

        if status_filter:
            jobs = [job for job in jobs if job.status == status_filter]

        return [asdict(job) for job in jobs]

    def cleanup_old_jobs(self, days_old: int = 7) -> int:
        """Clean up jobs older than specified days.

        Args:
            days_old: Remove jobs older than this many days

        Returns:
            Number of jobs removed
        """
        cutoff_date = datetime.now() - timedelta(days=days_old)

        jobs_to_remove = []
        for job_id, job in self.jobs.items():
            job_date = datetime.fromisoformat(job.created_at.replace("Z", "+00:00"))
            if job_date < cutoff_date and job.status in ["completed", "failed"]:
                jobs_to_remove.append(job_id)

        for job_id in jobs_to_remove:
            del self.jobs[job_id]

        if jobs_to_remove:
            self._save_jobs()
            logger.info(f"Cleaned up {len(jobs_to_remove)} old jobs")

        return len(jobs_to_remove)

    def get_pipeline_stats(self) -> dict[str, Any]:
        """Get overall pipeline statistics."""
        total_jobs = len(self.jobs)
        completed_jobs = len([j for j in self.jobs.values() if j.status == "completed"])
        failed_jobs = len([j for j in self.jobs.values() if j.status == "failed"])
        pending_jobs = len([j for j in self.jobs.values() if j.status == "pending"])

        total_urls = sum(len(job.urls) for job in self.jobs.values())

        return {
            "total_jobs": total_jobs,
            "completed_jobs": completed_jobs,
            "failed_jobs": failed_jobs,
            "pending_jobs": pending_jobs,
            "success_rate": completed_jobs / total_jobs if total_jobs > 0 else 0,
            "total_urls_processed": total_urls,
            "collection_size": self.pipeline.vector_store.get_collection_info()[
                "count"
            ],
        }
