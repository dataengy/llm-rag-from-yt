"""
Centralized logging configuration for the YouTube RAG project.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger as loguru_logger


class ProjectLogger:
    """Centralized logger for the entire project."""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.setup_logging()
            ProjectLogger._initialized = True

    def setup_logging(self, log_level: str = "INFO", log_dir: Optional[Path] = None):
        """Setup centralized logging configuration."""
        if log_dir is None:
            log_dir = Path("logs")

        # Create logs directory
        log_dir.mkdir(exist_ok=True)

        # Remove default loguru handler
        loguru_logger.remove()

        # Console handler with short colored format and emojis
        level_emojis = {
            "TRACE": "🔍",
            "DEBUG": "🐛",
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "CRITICAL": "🚨",
        }

        def format_record(record):
            emoji = level_emojis.get(record["level"].name, "📝")
            return (
                f"<green>{record['time']:HH:mm:ss}</green> "
                f"{emoji} <level>{record['level'].name[0]}</level> "
                f"<cyan>{record['name']}</cyan> "
                f"<level>{record['message']}</level>\n"
            )

        loguru_logger.add(
            sys.stderr, level=log_level, format=format_record, colorize=True
        )

        # File handler for general logs
        loguru_logger.add(
            log_dir / "app.log",
            rotation="10 MB",
            retention="30 days",
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            compression="gz",
        )

        # Separate file for errors
        loguru_logger.add(
            log_dir / "errors.log",
            rotation="10 MB",
            retention="30 days",
            level="ERROR",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            compression="gz",
        )

        # Telegram bot specific logs
        loguru_logger.add(
            log_dir / "telegram_bot.log",
            rotation="5 MB",
            retention="14 days",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            filter=lambda record: "telegram" in record["name"].lower(),
            compression="gz",
        )

        # Dagster pipeline specific logs
        loguru_logger.add(
            log_dir / "dagster.log",
            rotation="5 MB",
            retention="14 days",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            filter=lambda record: "dagster" in record["name"].lower(),
            compression="gz",
        )

        # RAG processing logs
        loguru_logger.add(
            log_dir / "rag_processing.log",
            rotation="5 MB",
            retention="14 days",
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            filter=lambda record: any(
                component in record["name"].lower()
                for component in [
                    "pipeline",
                    "audio",
                    "embeddings",
                    "vectorstore",
                    "rag",
                ]
            ),
            compression="gz",
        )

        # Intercept standard library logging
        class InterceptHandler(logging.Handler):
            def emit(self, record):
                # Get corresponding Loguru level if it exists
                try:
                    level = loguru_logger.level(record.levelname).name
                except ValueError:
                    level = record.levelno

                # Find caller from where originated the logged message
                frame, depth = logging.currentframe(), 2
                while frame.f_code.co_filename == logging.__file__:
                    frame = frame.f_back
                    depth += 1

                loguru_logger.opt(depth=depth, exception=record.exc_info).log(
                    level, record.getMessage()
                )

        # Replace standard library loggers
        logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

        # Specifically intercept common loggers
        for logger_name in ["uvicorn", "fastapi", "httpx", "telegram", "dagster"]:
            logging.getLogger(logger_name).handlers = [InterceptHandler()]
            logging.getLogger(logger_name).propagate = False

    def get_logger(self, name: str):
        """Get a logger instance with the given name."""
        return loguru_logger.bind(name=name)

    def log_startup(self, component: str, version: str = None, config: dict = None):
        """Log application startup information."""
        startup_info = [
            "=" * 60,
            f"🚀 Starting {component}",
            f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ]

        if version:
            startup_info.append(f"📦 Version: {version}")

        if config:
            startup_info.append("⚙️ Configuration:")
            for key, value in config.items():
                # Hide sensitive information
                if any(
                    sensitive in key.lower()
                    for sensitive in ["key", "token", "password", "secret"]
                ):
                    value = "*" * 8
                startup_info.append(f"   {key}: {value}")

        startup_info.append("=" * 60)

        loguru_logger.info("\n" + "\n".join(startup_info))

    def log_performance(self, operation: str, duration: float, details: dict = None):
        """Log performance metrics."""
        perf_info = [f"⏱️ {operation} completed in {duration:.3f}s"]

        if details:
            for key, value in details.items():
                perf_info.append(f"   {key}: {value}")

        loguru_logger.info(" | ".join(perf_info))

    def log_user_action(self, user_id: int, action: str, details: dict = None):
        """Log user actions for analytics."""
        action_info = [f"👤 User {user_id}: {action}"]

        if details:
            for key, value in details.items():
                action_info.append(f"{key}={value}")

        loguru_logger.info(" | ".join(action_info))

    def log_system_health(self, component: str, status: str, metrics: dict = None):
        """Log system health information."""
        health_info = [f"💚 {component}: {status}"]

        if metrics:
            for key, value in metrics.items():
                health_info.append(f"{key}={value}")

        loguru_logger.info(" | ".join(health_info))

    def log_error_context(self, error: Exception, context: dict = None):
        """Log errors with additional context."""
        error_info = [f"❌ {type(error).__name__}: {str(error)}"]

        if context:
            error_info.append("Context:")
            for key, value in context.items():
                error_info.append(f"   {key}: {value}")

        loguru_logger.error(" | ".join(error_info))


# Global logger instance
_project_logger = None


def get_logger(name: str = None):
    """Get the project logger instance."""
    global _project_logger
    if _project_logger is None:
        _project_logger = ProjectLogger()

    if name:
        return _project_logger.get_logger(name)
    return loguru_logger


# Global "log" instance for easy access
log = None


def get_log():
    """Get the global 'log' instance."""
    global log, _project_logger
    if log is None:
        if _project_logger is None:
            _project_logger = ProjectLogger()
        log = _project_logger.get_logger("app")
    return log


def setup_logging(log_level: str = "INFO", log_dir: Optional[Path] = None):
    """Setup project logging."""
    global _project_logger
    if _project_logger is None:
        _project_logger = ProjectLogger()

    _project_logger.setup_logging(log_level, log_dir)


def log_startup(component: str, version: str = None, config: dict = None):
    """Log application startup."""
    _project_logger.log_startup(component, version, config)


def log_performance(operation: str, duration: float, details: dict = None):
    """Log performance metrics."""
    _project_logger.log_performance(operation, duration, details)


def log_user_action(user_id: int, action: str, details: dict = None):
    """Log user actions."""
    _project_logger.log_user_action(user_id, action, details)


def log_system_health(component: str, status: str, metrics: dict = None):
    """Log system health."""
    _project_logger.log_system_health(component, status, metrics)


def log_error_context(error: Exception, context: dict = None):
    """Log errors with context."""
    _project_logger.log_error_context(error, context)
