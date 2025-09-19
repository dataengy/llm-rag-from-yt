#!/usr/bin/env python3
"""
Telegram bot runner script.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from llm_rag_yt.telegram.bot import TelegramBot
from llm_rag_yt._common.config.settings import Config
from llm_rag_yt._common.logging import log, setup_logging, log_startup
from llm_rag_yt._common.logging.telegram_handler import setup_telegram_logging


async def main():
    """Run the Telegram bot."""
    # Set up centralized logging
    setup_logging()
    
    # Set up Telegram logging for alerts
    setup_telegram_logging()
    
    # Get bot token
    token = os.getenv("BOT_TOKEN")
    if not token:
        log.error("BOT_TOKEN environment variable is required")
        sys.exit(1)
    
    # Create config
    config = Config()
    
    # Log startup
    log_startup("Telegram Bot", config={
        "token_present": bool(token),
        "fake_asr": config.use_fake_asr,
        "model": config.openai_model
    })
    
    # Create and run bot
    bot = TelegramBot(token, config)
    
    try:
        log.info("Starting Telegram bot...")
        await bot.run()
    except KeyboardInterrupt:
        log.info("Bot stopped by user")
    except Exception as e:
        log.error(f"Error running bot: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())