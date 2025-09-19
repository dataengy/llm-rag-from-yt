"""
CLI commands for the Telegram bot.
"""

import asyncio
import logging
import os
from typing import Optional

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

# Load environment variables
load_dotenv()
load_dotenv(".env.common")
load_dotenv(".env.secrets")

from .._common.config.settings import get_config
from ..telegram.bot import TelegramBot
from ..telegram.database import TelegramDatabase

logger = logging.getLogger(__name__)
console = Console()

app = typer.Typer(name="bot", help="Telegram bot commands")


@app.command()
def start(
    token: Optional[str] = typer.Option(
        None, "--token", "-t", help="Telegram bot token (or use BOT_TOKEN env var)"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging"
    ),
):
    """Start the Telegram bot."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Get token from parameter or environment
    bot_token = token or os.getenv("BOT_TOKEN")
    if not bot_token:
        console.print("[red]Error: Telegram bot token is required[/red]")
        console.print("Set BOT_TOKEN environment variable or use --token parameter")
        raise typer.Exit(1)

    console.print("[green]Starting Telegram bot...[/green]")

    try:
        config = get_config()
        bot = TelegramBot(bot_token, config)

        # Run the bot
        asyncio.run(bot.run())

    except KeyboardInterrupt:
        console.print("\n[yellow]Bot stopped by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Error starting bot: {e}[/red]")
        logger.error(f"Bot startup error: {e}", exc_info=True)
        raise typer.Exit(1)


@app.command()
def status():
    """Show Telegram bot status and statistics."""
    try:
        db = TelegramDatabase()

        # Get processing stats
        processing_stats = db.get_processing_stats()
        user_stats = db.get_user_stats(days=7)

        console.print("\n[bold blue]📊 Telegram Bot Status[/bold blue]")
        console.print("=" * 50)

        # YouTube requests table
        youtube_table = Table(title="YouTube Requests")
        youtube_table.add_column("Status", style="cyan")
        youtube_table.add_column("Count", justify="right", style="magenta")

        youtube_requests = processing_stats.get("youtube_requests", {})
        for status, count in youtube_requests.items():
            youtube_table.add_row(status.title(), str(count))

        console.print(youtube_table)

        # Audio files table
        audio_table = Table(title="Audio Files")
        audio_table.add_column("Status", style="cyan")
        audio_table.add_column("Count", justify="right", style="magenta")

        audio_files = processing_stats.get("audio_files", {})
        for status, count in audio_files.items():
            audio_table.add_row(status.title(), str(count))

        console.print(audio_table)

        # User activity
        console.print("\n[bold green]👥 User Activity (Last 7 Days)[/bold green]")
        console.print(f"Total Queries: {user_stats.get('total_queries', 0)}")
        console.print(f"Unique Users: {user_stats.get('unique_users', 0)}")
        console.print(
            f"Average Response Time: {user_stats.get('avg_response_time_ms', 0):.0f}ms"
        )

        # Feedback
        feedback = user_stats.get("feedback", {})
        if feedback:
            console.print("\n[bold yellow]📝 Feedback[/bold yellow]")
            for feedback_type, count in feedback.items():
                console.print(f"{feedback_type}: {count}")

    except Exception as e:
        console.print(f"[red]Error getting status: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def add_url(
    url: str = typer.Argument(..., help="YouTube URL to process"),
    user_id: int = typer.Option(0, "--user-id", "-u", help="User ID (0 for system)"),
):
    """Add a YouTube URL to the processing queue."""
    try:
        db = TelegramDatabase()

        # Add URL to processing queue
        db.log_youtube_request(
            user_id, url, "pending", {"source": "cli", "added_by": "admin"}
        )

        console.print(f"[green]✅ Added URL to processing queue: {url}[/green]")

    except Exception as e:
        console.print(f"[red]Error adding URL: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def list_users():
    """List active users and their activity."""
    try:
        db = TelegramDatabase()

        # Get recent user activity
        with db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT user_id, username, COUNT(*) as activity_count,
                       MAX(created_at) as last_activity
                FROM user_activity
                WHERE created_at >= datetime('now', '-7 days')
                GROUP BY user_id, username
                ORDER BY activity_count DESC
            """)
            users = cursor.fetchall()

        if not users:
            console.print("[yellow]No user activity found in the last 7 days[/yellow]")
            return

        table = Table(title="Active Users (Last 7 Days)")
        table.add_column("User ID", justify="right", style="cyan")
        table.add_column("Username", style="green")
        table.add_column("Activity Count", justify="right", style="magenta")
        table.add_column("Last Activity", style="yellow")

        for user in users:
            table.add_row(str(user[0]), user[1] or "Unknown", str(user[2]), user[3])

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error listing users: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def alerts():
    """Show system alerts."""
    try:
        db = TelegramDatabase()
        alerts = db.get_unacknowledged_alerts()

        if not alerts:
            console.print("[green]✅ No unacknowledged alerts[/green]")
            return

        table = Table(title=f"System Alerts ({len(alerts)} unacknowledged)")
        table.add_column("ID", justify="right", style="cyan")
        table.add_column("Type", style="yellow")
        table.add_column("Severity", style="red")
        table.add_column("Message", style="white")
        table.add_column("Created", style="blue")

        for alert in alerts:
            severity_style = {
                "info": "blue",
                "warning": "yellow",
                "error": "red",
                "critical": "bold red",
            }.get(alert["severity"], "white")

            table.add_row(
                str(alert["id"]),
                alert["alert_type"],
                f"[{severity_style}]{alert['severity'].upper()}[/{severity_style}]",
                alert["message"][:50] + "..."
                if len(alert["message"]) > 50
                else alert["message"],
                alert["created_at"],
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error getting alerts: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def ack_alert(alert_id: int = typer.Argument(..., help="Alert ID to acknowledge")):
    """Acknowledge a system alert."""
    try:
        db = TelegramDatabase()
        db.acknowledge_alert(alert_id)
        console.print(f"[green]✅ Acknowledged alert {alert_id}[/green]")

    except Exception as e:
        console.print(f"[red]Error acknowledging alert: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def cleanup():
    """Clean up old database records and files."""

    try:
        db = TelegramDatabase()

        console.print("[yellow]🧹 Starting cleanup...[/yellow]")

        # Clean up old completed jobs (older than 7 days)
        with db.get_connection() as conn:
            cursor = conn.execute("""
                DELETE FROM pipeline_jobs
                WHERE status = 'completed' AND completed_at < datetime('now', '-7 days')
            """)
            deleted_jobs = cursor.rowcount

            # Clean up old acknowledged alerts (older than 7 days)
            cursor = conn.execute("""
                DELETE FROM system_alerts
                WHERE acknowledged = TRUE AND acknowledged_at < datetime('now', '-7 days')
            """)
            deleted_alerts = cursor.rowcount

            # Clean up old user activity (older than 30 days)
            cursor = conn.execute("""
                DELETE FROM user_activity
                WHERE created_at < datetime('now', '-30 days')
            """)
            deleted_activity = cursor.rowcount

            conn.commit()

        console.print("[green]✅ Cleanup completed:[/green]")
        console.print(f"  - Deleted {deleted_jobs} old completed jobs")
        console.print(f"  - Deleted {deleted_alerts} old acknowledged alerts")
        console.print(f"  - Deleted {deleted_activity} old user activity records")

    except Exception as e:
        console.print(f"[red]Error during cleanup: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
