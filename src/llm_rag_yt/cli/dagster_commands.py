"""
CLI commands for Dagster pipeline management.
"""

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import requests
import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

console = Console()

app = typer.Typer(name="dagster", help="Dagster pipeline commands")

# Load environment variables
load_dotenv()
load_dotenv(".env.common")
load_dotenv(".env.secrets")


def _setup_environment():
    """Set up environment variables for Dagster."""
    # Get DAGSTER_HOME from environment or default
    dagster_home = os.getenv("DAGSTER_HOME")

    if not dagster_home:
        dagster_home = str(Path.cwd() / "data" / "dagster")

    # Convert to absolute path if it's relative
    dagster_home_path = Path(dagster_home)
    if not dagster_home_path.is_absolute():
        dagster_home_path = Path.cwd() / dagster_home_path
        dagster_home = str(dagster_home_path)

    # Set the absolute path in environment
    os.environ["DAGSTER_HOME"] = dagster_home
    dagster_home_path.mkdir(parents=True, exist_ok=True)

    # Set the Python path to include the src directory
    src_path = Path(__file__).parent.parent.parent
    if "PYTHONPATH" in os.environ:
        os.environ["PYTHONPATH"] = f"{src_path}:{os.environ['PYTHONPATH']}"
    else:
        os.environ["PYTHONPATH"] = str(src_path)

    return dagster_home_path


def _check_url_availability(url: str, timeout: int = 10) -> bool:
    """Check if URL is available."""
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code == 200
    except requests.RequestException:
        return False


def _wait_for_server(host: str, port: int, timeout: int = 30) -> bool:
    """Wait for Dagster server to start."""
    url = f"http://{host}:{port}"
    console.print(f"[yellow]Waiting for server at {url}...[/yellow]")

    start_time = time.time()
    while time.time() - start_time < timeout:
        if _check_url_availability(url):
            console.print(f"[green]✅ Server is ready at {url}[/green]")
            return True
        time.sleep(1)

    return False


@app.command()
def dev(
    port: int = typer.Option(None, "--port", "-p", help="Port for Dagster web UI"),
    host: str = typer.Option(
        "localhost", "--host", "-h", help="Host for Dagster web UI"
    ),
    check_health: bool = typer.Option(
        True,
        "--check-health/--no-check-health",
        help="Check server health after startup",
    ),
):
    """Start Dagster development server."""
    # Use port from environment if not specified
    if port is None:
        dagster_port = os.getenv("DAGSTER_PORT")
        if not dagster_port:
            raise ValueError("DAGSTER_PORT environment variable is required")
        port = int(dagster_port)

    console.print(
        f"[green]Starting Dagster development server on {host}:{port}[/green]"
    )

    try:
        # Set up environment
        dagster_home = _setup_environment()
        console.print(f"[cyan]DAGSTER_HOME: {dagster_home}[/cyan]")

        # Start Dagster dev server using module import
        cmd = [
            sys.executable,
            "-m",
            "dagster",
            "dev",
            "-m",
            "llm_rag_yt.dagster.definitions",
            "--port",
            str(port),
            "--host",
            host,
        ]

        console.print(f"[cyan]Running: {' '.join(cmd)}[/cyan]")

        # Start server in background if health check is enabled
        if check_health:
            process = subprocess.Popen(cmd)

            # Wait for server to start
            if _wait_for_server(host, port):
                console.print(
                    f"[green]🚀 Dagster UI available at: http://{host}:{port}[/green]"
                )
                console.print("[yellow]Press Ctrl+C to stop the server[/yellow]")

                # Wait for process to complete or be interrupted
                try:
                    process.wait()
                except KeyboardInterrupt:
                    console.print("\n[yellow]Stopping Dagster server...[/yellow]")
                    process.terminate()
                    process.wait()
            else:
                console.print("[red]❌ Server failed to start within timeout[/red]")
                process.terminate()
                raise typer.Exit(1)
        else:
            subprocess.run(cmd, check=True)

    except KeyboardInterrupt:
        console.print("\n[yellow]Dagster server stopped by user[/yellow]")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error starting Dagster server: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def run_job(
    job_name: str = typer.Argument(..., help="Name of the job to run"),
    config_file: Optional[str] = typer.Option(
        None, "--config", "-c", help="Path to config file"
    ),
):
    """Run a specific Dagster job."""
    console.print(f"[green]Running Dagster job: {job_name}[/green]")

    try:
        # Set up environment
        _setup_environment()

        # Build command
        cmd = [
            sys.executable,
            "-m",
            "dagster",
            "job",
            "execute",
            "-m",
            "llm_rag_yt.dagster.definitions",
            "-j",
            job_name,
        ]

        if config_file:
            cmd.extend(["-c", config_file])

        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        console.print("[green]✅ Job completed successfully[/green]")
        console.print(result.stdout)

    except subprocess.CalledProcessError as e:
        console.print(f"[red]❌ Job failed: {e}[/red]")
        if e.stdout:
            console.print("STDOUT:", e.stdout)
        if e.stderr:
            console.print("STDERR:", e.stderr)
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def list_jobs():
    """List all available Dagster jobs."""
    try:
        # Set up environment
        src_path = Path(__file__).parent.parent.parent
        if "PYTHONPATH" in os.environ:
            os.environ["PYTHONPATH"] = f"{src_path}:{os.environ['PYTHONPATH']}"
        else:
            os.environ["PYTHONPATH"] = str(src_path)

        # Import definitions to get job list

        table = Table(title="Available Dagster Jobs")
        table.add_column("Job Name", style="cyan")
        table.add_column("Description", style="green")

        jobs = [
            ("youtube_processing_job", "Process YouTube URLs to audio files"),
            ("audio_processing_job", "Transcribe and embed audio files"),
            ("pipeline_monitoring_job", "Monitor pipeline health and metrics"),
            ("telegram_alert_job", "Send alerts to Telegram"),
            ("cleanup_job", "Clean up old files and database records"),
            ("health_check_job", "Perform system health checks"),
        ]

        for job_name, description in jobs:
            table.add_row(job_name, description)

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error listing jobs: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def list_assets():
    """List all available Dagster assets."""
    try:
        table = Table(title="Available Dagster Assets")
        table.add_column("Asset Name", style="cyan")
        table.add_column("Group", style="yellow")
        table.add_column("Description", style="green")

        assets = [
            ("youtube_urls_to_process", "ingestion", "YouTube URLs from database"),
            ("downloaded_audio_files", "ingestion", "Downloaded audio files"),
            (
                "unprocessed_audio_files",
                "processing",
                "Audio files awaiting transcription",
            ),
            ("transcribed_audio_files", "processing", "Transcribed audio files"),
            ("embedded_content", "processing", "Content with embeddings"),
            ("pipeline_metrics", "monitoring", "Pipeline performance metrics"),
            ("system_alerts", "monitoring", "System alerts and notifications"),
        ]

        for asset_name, group, description in assets:
            table.add_row(asset_name, group, description)

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error listing assets: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def materialize_asset(
    asset_name: str = typer.Argument(..., help="Name of the asset to materialize"),
):
    """Materialize a specific Dagster asset."""
    console.print(f"[green]Materializing asset: {asset_name}[/green]")

    try:
        # Set up environment
        _setup_environment()

        # Run asset materialization
        cmd = [
            sys.executable,
            "-m",
            "dagster",
            "asset",
            "materialize",
            "-m",
            "llm_rag_yt.dagster.definitions",
            "-s",
            asset_name,
        ]

        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        console.print("[green]✅ Asset materialized successfully[/green]")
        console.print(result.stdout)

    except subprocess.CalledProcessError as e:
        console.print(f"[red]❌ Asset materialization failed: {e}[/red]")
        if e.stdout:
            console.print("STDOUT:", e.stdout)
        if e.stderr:
            console.print("STDERR:", e.stderr)
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def sensor_status():
    """Show status of all Dagster sensors."""
    try:
        table = Table(title="Dagster Sensors Status")
        table.add_column("Sensor Name", style="cyan")
        table.add_column("Default Status", style="yellow")
        table.add_column("Interval", style="green")
        table.add_column("Description", style="white")

        sensors = [
            ("youtube_url_sensor", "RUNNING", "30s", "Monitors for new YouTube URLs"),
            ("audio_file_sensor", "RUNNING", "60s", "Monitors for new audio files"),
            ("pipeline_health_sensor", "RUNNING", "5m", "Monitors pipeline health"),
            ("cleanup_sensor", "STOPPED", "1h", "Cleans up old files"),
            ("telegram_alert_sensor", "RUNNING", "2m", "Sends alerts to Telegram"),
        ]

        for sensor_name, status, interval, description in sensors:
            status_style = "green" if status == "RUNNING" else "red"
            table.add_row(
                sensor_name,
                f"[{status_style}]{status}[/{status_style}]",
                interval,
                description,
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error getting sensor status: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def logs(
    job_name: Optional[str] = typer.Option(
        None, "--job", "-j", help="Filter logs by job name"
    ),
    limit: int = typer.Option(
        50, "--limit", "-l", help="Number of log entries to show"
    ),
):
    """Show recent Dagster logs."""
    console.print(f"[green]Showing last {limit} Dagster log entries[/green]")

    if job_name:
        console.print(f"Filtered by job: {job_name}")

    try:
        # For now, just show a placeholder since we'd need to integrate with Dagster's logging system
        console.print("[yellow]Dagster logs would be displayed here[/yellow]")
        console.print("Use 'dagster dev' to access the web UI for detailed logs")

    except Exception as e:
        console.print(f"[red]Error getting logs: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
