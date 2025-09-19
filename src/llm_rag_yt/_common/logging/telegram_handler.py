"""
Telegram logging handler for sending critical alerts.
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Optional

from telegram import Bot


class TelegramHandler(logging.Handler):
    """Custom logging handler that sends critical logs to Telegram."""

    def __init__(
        self,
        token: Optional[str] = None,
        chat_id: Optional[str] = None,
        level: int = logging.ERROR,
    ):
        """
        Initialize Telegram handler.

        Args:
            token: Telegram bot token (or from BOT_TOKEN env var)
            chat_id: Target chat ID (or from TELEGRAM_ADMIN_CHAT_ID env var)
            level: Minimum logging level to send to Telegram
        """
        super().__init__(level)

        self.token = token or os.getenv("BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_ADMIN_CHAT_ID")

        if not self.token:
            raise ValueError("Telegram bot token is required")
        if not self.chat_id:
            raise ValueError("Telegram chat ID is required")

        self.bot = Bot(token=self.token)

    def emit(self, record: logging.LogRecord):
        """Send log record to Telegram."""
        try:
            # Format the message
            message = self.format_message(record)

            # Send to Telegram (non-blocking)
            asyncio.create_task(self._send_message(message))

        except Exception as e:
            # Don't let logging errors crash the application
            print(f"Failed to send log to Telegram: {e}")

    def format_message(self, record: logging.LogRecord) -> str:
        """Format log record for Telegram."""
        level_emoji = {
            logging.DEBUG: "🐛",
            logging.INFO: "ℹ️",
            logging.WARNING: "⚠️",
            logging.ERROR: "❌",
            logging.CRITICAL: "🚨",
        }

        emoji = level_emoji.get(record.levelno, "📢")

        message = f"""
{emoji} **{record.levelname}**

**Module:** `{record.name}`
**Function:** `{record.funcName}`
**Line:** {record.lineno}

**Message:** {record.getMessage()}

**Time:** {datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")}
        """

        # Add exception info if present
        if record.exc_info:
            import traceback

            exc_text = "".join(traceback.format_exception(*record.exc_info))
            message += f"\n**Exception:**\n```\n{exc_text[:1000]}...\n```"

        return message.strip()

    async def _send_message(self, message: str):
        """Send message to Telegram (async)."""
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode="Markdown",
                disable_web_page_preview=True,
            )
        except Exception as e:
            print(f"Failed to send Telegram message: {e}")


class TelegramAlertManager:
    """Manages Telegram alerts and notifications."""

    def __init__(
        self, token: Optional[str] = None, admin_chat_id: Optional[str] = None
    ):
        """Initialize alert manager."""
        self.token = token or os.getenv("BOT_TOKEN")
        self.admin_chat_id = admin_chat_id or os.getenv("TELEGRAM_ADMIN_CHAT_ID")

        if self.token and self.admin_chat_id:
            self.bot = Bot(token=self.token)
            self.enabled = True
        else:
            self.bot = None
            self.enabled = False

    async def send_system_alert(
        self,
        alert_type: str,
        severity: str,
        message: str,
        details: Optional[dict] = None,
    ):
        """Send a system alert to administrators."""
        if not self.enabled:
            return

        severity_emoji = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "critical": "🚨"}

        emoji = severity_emoji.get(severity.lower(), "📢")

        alert_message = f"""
{emoji} **SYSTEM ALERT**

**Type:** {alert_type}
**Severity:** {severity.upper()}
**Time:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

**Message:** {message}
        """

        if details:
            alert_message += f"\n**Details:** {details}"

        try:
            await self.bot.send_message(
                chat_id=self.admin_chat_id,
                text=alert_message.strip(),
                parse_mode="Markdown",
            )
        except Exception as e:
            print(f"Failed to send system alert: {e}")

    async def send_processing_update(
        self, user_id: int, url: str, status: str, error: Optional[str] = None
    ):
        """Send processing status update."""
        if not self.enabled:
            return

        status_emoji = {"started": "🔄", "completed": "✅", "failed": "❌"}

        emoji = status_emoji.get(status, "📢")

        message = f"""
{emoji} **Processing Update**

**User:** {user_id}
**URL:** {url}
**Status:** {status.title()}
**Time:** {datetime.now().strftime("%H:%M:%S")}
        """

        if error:
            message += f"\n**Error:** {error}"

        try:
            await self.bot.send_message(
                chat_id=self.admin_chat_id, text=message.strip(), parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Failed to send processing update: {e}")

    async def send_usage_stats(self, stats: dict):
        """Send daily usage statistics."""
        if not self.enabled:
            return

        message = f"""
📊 **Daily Usage Report**

**Date:** {datetime.now().strftime("%Y-%m-%d")}

**YouTube Requests:**
• Total: {stats.get("total_requests", 0)}
• Completed: {stats.get("completed_requests", 0)}
• Failed: {stats.get("failed_requests", 0)}

**User Activity:**
• Active Users: {stats.get("active_users", 0)}
• Total Queries: {stats.get("total_queries", 0)}
• Avg Response Time: {stats.get("avg_response_time", 0):.1f}ms

**System Health:**
• Storage Used: {stats.get("storage_used_mb", 0):.1f} MB
• Processing Queue: {stats.get("queue_size", 0)} items
        """

        try:
            await self.bot.send_message(
                chat_id=self.admin_chat_id, text=message.strip(), parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Failed to send usage stats: {e}")


def setup_telegram_logging(level: int = logging.ERROR) -> bool:
    """
    Set up Telegram logging for the application.

    Args:
        level: Minimum logging level to send to Telegram

    Returns:
        bool: True if setup successful, False otherwise
    """
    try:
        token = os.getenv("BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_ADMIN_CHAT_ID")

        if not token or not chat_id:
            print(
                "Telegram logging not configured (missing BOT_TOKEN or TELEGRAM_ADMIN_CHAT_ID)"
            )
            return False

        # Create and add Telegram handler
        telegram_handler = TelegramHandler(token, chat_id, level)

        # Set formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        telegram_handler.setFormatter(formatter)

        # Add to root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(telegram_handler)

        print(
            f"Telegram logging enabled for level {logging.getLevelName(level)} and above"
        )
        return True

    except Exception as e:
        print(f"Failed to set up Telegram logging: {e}")
        return False
