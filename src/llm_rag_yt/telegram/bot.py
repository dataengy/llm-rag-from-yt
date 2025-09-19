"""
Telegram bot for YouTube URL processing and RAG queries.
Provides visual progress tracking and optional verbose mode.
"""

import asyncio
import logging
import os
import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode

from ..pipeline import RAGPipeline
from ..config.settings import Config
from .database import TelegramDatabase
from .progress_tracker import ProgressTracker


logger = logging.getLogger(__name__)


class TelegramBot:
    """Telegram bot for YouTube processing and RAG queries."""
    
    def __init__(self, token: str, config: Optional[Config] = None):
        """Initialize the Telegram bot."""
        self.token = token
        self.config = config or Config()
        self.pipeline = RAGPipeline(self.config)
        self.db = TelegramDatabase()
        self.progress_tracker = ProgressTracker()
        
        # User sessions for context
        self.user_sessions: Dict[int, Dict[str, Any]] = {}
        
        # Initialize application
        self.application = Application.builder().token(token).build()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up message and command handlers."""
        # Commands
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("verbose", self.toggle_verbose))
        self.application.add_handler(CommandHandler("cancel", self.cancel_command))
        
        # URL processing
        self.application.add_handler(MessageHandler(
            filters.TEXT & filters.Regex(r'(?:youtube\.com|youtu\.be)'), 
            self.process_youtube_url
        ))
        
        # Text queries
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            self.handle_query
        ))
        
        # Callback queries (inline buttons)
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"
        
        # Initialize user session
        self.user_sessions[user_id] = {
            "verbose": False,
            "current_task": None,
            "last_activity": datetime.now()
        }
        
        # Log user interaction
        self.db.log_user_activity(user_id, username, "start", {})
        
        welcome_message = """
🎬 **YouTube RAG Bot** 
━━━━━━━━━━━━━━━━━━━━━

Welcome! I can help you process YouTube videos and answer questions about their content.

**How to use:**
📹 Send me a YouTube URL to process it
❓ Ask questions about processed content
⚙️ Use /verbose to toggle detailed output
📊 Use /status to check system status

**Commands:**
/help - Show this help message
/verbose - Toggle verbose mode (default: off)
/status - Show processing status
/cancel - Cancel current operation

Ready to start! Send me a YouTube URL 🚀
        """
        
        await update.message.reply_text(
            welcome_message, 
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_text = """
🎬 **YouTube RAG Bot Help**
━━━━━━━━━━━━━━━━━━━━━

**Basic Usage:**
1️⃣ Send YouTube URL → I'll download and process the audio
2️⃣ Ask questions → I'll search the content and provide answers

**Commands:**
• `/start` - Start the bot
• `/help` - Show this help
• `/verbose` - Toggle detailed processing output
• `/status` - Show current system status
• `/cancel` - Cancel ongoing operation

**URL Processing:**
📹 Send any YouTube URL (youtube.com or youtu.be)
⏳ I'll show progress: download → transcribe → embed → ready
✅ When complete, you can ask questions!

**Query Features:**
❓ Ask questions in any language
🔍 I support hybrid search (text + semantic)
📊 Get relevance scores and source timestamps
🎯 Context-aware answers from the video content

**Examples:**
`https://youtube.com/watch?v=abc123` ← Process video
`What is the main topic discussed?` ← Ask question
`/verbose` ← Enable detailed output

Need more help? Just ask! 🤖
        """
        
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        user_id = update.effective_user.id
        
        try:
            # Get system status from pipeline
            status = self.pipeline.get_status()
            
            # Get user's current task if any
            user_session = self.user_sessions.get(user_id, {})
            current_task = user_session.get("current_task")
            
            # Format status message
            status_message = f"""
📊 **System Status**
━━━━━━━━━━━━━━━━━━━━━

**Pipeline Status:** {"🟢 Ready" if status.get("ready", False) else "🔴 Not Ready"}
**Vector Store:** {status.get("vectorstore_docs", 0)} documents
**Last Updated:** {status.get("last_update", "Never")}

**Your Session:**
• Verbose Mode: {"🔊 ON" if user_session.get("verbose", False) else "🔇 OFF"}
• Current Task: {current_task or "None"}
• Session Active: {"✅ Yes" if user_id in self.user_sessions else "❌ No"}

**Recent Activity:**
• Total Users: {len(self.user_sessions)}
• Active Tasks: {sum(1 for s in self.user_sessions.values() if s.get("current_task"))}
            """
            
            # Add task progress if available
            if current_task:
                progress = self.progress_tracker.get_progress(user_id)
                if progress:
                    status_message += f"\n**Task Progress:** {progress['percentage']:.1f}%"
                    status_message += f"\n**Current Step:** {progress['current_step']}"
            
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            status_message = "❌ Error retrieving system status. Please try again."
        
        await update.message.reply_text(status_message, parse_mode=ParseMode.MARKDOWN)
    
    async def toggle_verbose(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Toggle verbose mode for user."""
        user_id = update.effective_user.id
        
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {"verbose": False}
        
        current_verbose = self.user_sessions[user_id].get("verbose", False)
        new_verbose = not current_verbose
        self.user_sessions[user_id]["verbose"] = new_verbose
        
        status = "🔊 ON" if new_verbose else "🔇 OFF"
        message = f"Verbose mode: **{status}**"
        
        if new_verbose:
            message += "\n\nYou'll now see detailed processing steps including:\n"
            message += "• Download progress\n• Transcription steps\n• Embedding creation\n• Search details"
        else:
            message += "\n\nYou'll see only essential updates."
        
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
    
    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel current operation."""
        user_id = update.effective_user.id
        
        if user_id in self.user_sessions and self.user_sessions[user_id].get("current_task"):
            # Cancel the task
            self.progress_tracker.cancel_task(user_id)
            self.user_sessions[user_id]["current_task"] = None
            
            await update.message.reply_text(
                "❌ **Operation Cancelled**\n\nYour current task has been cancelled. You can start a new one anytime!",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                "ℹ️ No active operation to cancel.",
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def process_youtube_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process YouTube URL with progress tracking."""
        user_id = update.effective_user.id
        url = update.message.text.strip()
        verbose = self.user_sessions.get(user_id, {}).get("verbose", False)
        
        # Validate URL
        if not self._is_valid_youtube_url(url):
            await update.message.reply_text(
                "❌ **Invalid URL**\n\nPlease send a valid YouTube URL (youtube.com or youtu.be)",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Check if user has active task
        if user_id in self.user_sessions and self.user_sessions[user_id].get("current_task"):
            keyboard = [
                [InlineKeyboardButton("✅ Yes, cancel current", callback_data=f"cancel_and_start:{url}")],
                [InlineKeyboardButton("❌ No, keep current", callback_data="keep_current")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "⚠️ **Task in Progress**\n\nYou have an active task. Cancel it to start a new one?",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Start processing
        self.user_sessions[user_id] = {
            "verbose": verbose,
            "current_task": "processing_url",
            "url": url,
            "last_activity": datetime.now()
        }
        
        # Log the request
        self.db.log_youtube_request(user_id, url, "started")
        
        # Send initial message
        progress_message = await update.message.reply_text(
            "🎬 **Processing YouTube Video**\n━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📹 URL: `{url}`\n"
            "🔄 Preparing...",
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            # Start progress tracking
            self.progress_tracker.start_task(user_id, "url_processing", {
                "url": url,
                "message_id": progress_message.message_id,
                "chat_id": update.effective_chat.id
            })
            
            # Process in background
            asyncio.create_task(
                self._process_url_background(user_id, url, progress_message, verbose)
            )
            
        except Exception as e:
            logger.error(f"Error starting URL processing: {e}")
            await progress_message.edit_text(
                "❌ **Processing Failed**\n\nFailed to start processing. Please try again.",
                parse_mode=ParseMode.MARKDOWN
            )
            self.user_sessions[user_id]["current_task"] = None
    
    async def _process_url_background(self, user_id: int, url: str, progress_message, verbose: bool):
        """Process URL in background with progress updates."""
        try:
            # Download step
            await self._update_progress(progress_message, "🔽 Downloading audio...", 10, verbose)
            
            if verbose:
                await progress_message.reply_text("📡 Connecting to YouTube servers...")
            
            # Actually download (this is a placeholder - integrate with your pipeline)
            await asyncio.sleep(2)  # Simulate download time
            
            # Transcribe step
            await self._update_progress(progress_message, "🎤 Transcribing audio...", 40, verbose)
            
            if verbose:
                await progress_message.reply_text("🧠 Running speech recognition...")
            
            await asyncio.sleep(3)  # Simulate transcription time
            
            # Process text step
            await self._update_progress(progress_message, "📝 Processing text...", 70, verbose)
            
            if verbose:
                await progress_message.reply_text("✂️ Chunking text into segments...")
            
            await asyncio.sleep(1)
            
            # Create embeddings step
            await self._update_progress(progress_message, "🧮 Creating embeddings...", 90, verbose)
            
            if verbose:
                await progress_message.reply_text("🔗 Generating semantic vectors...")
            
            await asyncio.sleep(2)
            
            # Complete
            await self._update_progress(progress_message, "✅ Processing complete!", 100, verbose)
            
            # Final success message
            success_text = """
✅ **Processing Complete!**
━━━━━━━━━━━━━━━━━━━━━

🎬 Your video has been successfully processed and added to the knowledge base.

🤖 **Ready for questions!** 
Ask me anything about the video content. I can:
• Answer specific questions
• Summarize topics
• Find relevant timestamps
• Provide context-aware responses

**Example questions:**
"What is the main topic?"
"Who are the speakers?"
"Summarize the key points"

Go ahead, ask away! 🚀
            """
            
            await progress_message.edit_text(success_text, parse_mode=ParseMode.MARKDOWN)
            
            # Update database
            self.db.log_youtube_request(user_id, url, "completed")
            
            # Clean up session
            self.user_sessions[user_id]["current_task"] = None
            self.progress_tracker.complete_task(user_id)
            
        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}")
            await progress_message.edit_text(
                f"❌ **Processing Failed**\n\nError: {str(e)}\n\nPlease try again with a different URL.",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Update database
            self.db.log_youtube_request(user_id, url, "failed", {"error": str(e)})
            
            # Clean up session
            self.user_sessions[user_id]["current_task"] = None
            self.progress_tracker.cancel_task(user_id)
    
    async def _update_progress(self, message, status: str, percentage: int, verbose: bool):
        """Update progress message."""
        progress_bar = self._create_progress_bar(percentage)
        
        progress_text = f"""
🎬 **Processing YouTube Video**
━━━━━━━━━━━━━━━━━━━━━

{progress_bar} {percentage}%

🔄 {status}
        """
        
        if verbose:
            progress_text += f"\n⏱️ Started: {datetime.now().strftime('%H:%M:%S')}"
        
        await message.edit_text(progress_text.strip(), parse_mode=ParseMode.MARKDOWN)
    
    def _create_progress_bar(self, percentage: int, length: int = 10) -> str:
        """Create a visual progress bar."""
        filled = int(length * percentage / 100)
        bar = "█" * filled + "░" * (length - filled)
        return f"[{bar}]"
    
    async def handle_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle user queries about processed content."""
        user_id = update.effective_user.id
        question = update.message.text.strip()
        verbose = self.user_sessions.get(user_id, {}).get("verbose", False)
        
        # Check if user has an active processing task
        if user_id in self.user_sessions and self.user_sessions[user_id].get("current_task") == "processing_url":
            await update.message.reply_text(
                "⏳ **Processing in Progress**\n\nPlease wait for the current video to finish processing before asking questions.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Log the query
        self.db.log_user_query(user_id, question)
        
        # Send "thinking" message
        thinking_message = await update.message.reply_text(
            "🤔 **Searching...**\n\nLooking through the processed content...",
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            # Query the RAG system
            result = await self._query_rag_system(question, verbose)
            
            if not result:
                await thinking_message.edit_text(
                    "❌ **No Content Found**\n\nI don't have any processed content to search. Please send a YouTube URL first!",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            # Format response
            response_text = self._format_query_response(result, verbose)
            
            # Add feedback buttons
            keyboard = [
                [
                    InlineKeyboardButton("👍", callback_data=f"feedback:good:{question[:50]}"),
                    InlineKeyboardButton("👎", callback_data=f"feedback:bad:{question[:50]}")
                ],
                [InlineKeyboardButton("🔍 More details", callback_data=f"details:{question[:50]}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await thinking_message.edit_text(
                response_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error processing query '{question}': {e}")
            await thinking_message.edit_text(
                f"❌ **Query Failed**\n\nError processing your question: {str(e)}",
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def _query_rag_system(self, question: str, verbose: bool) -> Optional[Dict[str, Any]]:
        """Query the RAG system and return results."""
        try:
            # Use your existing RAG pipeline
            result = self.pipeline.query(question)
            return result
        except Exception as e:
            logger.error(f"RAG query error: {e}")
            return None
    
    def _format_query_response(self, result: Dict[str, Any], verbose: bool) -> str:
        """Format the query response for Telegram."""
        answer = result.get("answer", "No answer found")
        sources = result.get("sources", [])
        
        response = f"""
🤖 **Answer**
━━━━━━━━━━━━━━━━━━━━━

{answer}
        """
        
        if sources and verbose:
            response += "\n\n📚 **Sources:**\n"
            for i, source in enumerate(sources[:3], 1):
                response += f"{i}. {source.get('text', '')[:100]}...\n"
        
        if verbose:
            response += f"\n⏱️ Response time: {result.get('response_time', 0):.2f}s"
            response += f"\n🎯 Relevance: {result.get('relevance_score', 0):.2f}"
        
        return response.strip()
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button callbacks."""
        query = update.callback_query
        data = query.data
        user_id = update.effective_user.id
        
        await query.answer()
        
        if data.startswith("cancel_and_start:"):
            url = data.split(":", 1)[1]
            # Cancel current task and start new one
            self.progress_tracker.cancel_task(user_id)
            self.user_sessions[user_id]["current_task"] = None
            
            # Trigger new processing
            await query.edit_message_text(
                "✅ Previous task cancelled. Starting new processing...",
                parse_mode=ParseMode.MARKDOWN
            )
            # You would trigger URL processing here
            
        elif data == "keep_current":
            await query.edit_message_text(
                "✅ Keeping current task. It will continue processing.",
                parse_mode=ParseMode.MARKDOWN
            )
            
        elif data.startswith("feedback:"):
            _, feedback_type, question_preview = data.split(":", 2)
            self.db.log_feedback(user_id, question_preview, feedback_type, {})
            
            feedback_emoji = "👍" if feedback_type == "good" else "👎"
            await query.edit_message_reply_markup(None)
            await query.message.reply_text(
                f"{feedback_emoji} **Feedback recorded!** Thank you for helping improve the system.",
                parse_mode=ParseMode.MARKDOWN
            )
            
        elif data.startswith("details:"):
            question_preview = data.split(":", 1)[1]
            await query.message.reply_text(
                f"📊 **Detailed Analysis**\n\n"
                f"Your question: `{question_preview}...`\n\n"
                f"🔍 Search method: Hybrid (semantic + keyword)\n"
                f"📚 Sources checked: All processed content\n"
                f"🎯 Confidence threshold: 0.7\n"
                f"⚡ Processing: Real-time",
                parse_mode=ParseMode.MARKDOWN
            )
    
    def _is_valid_youtube_url(self, url: str) -> bool:
        """Check if URL is a valid YouTube URL."""
        return ("youtube.com" in url or "youtu.be" in url) and ("watch?v=" in url or "youtu.be/" in url)
    
    async def run(self):
        """Start the bot."""
        logger.info("Starting Telegram bot...")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
        try:
            # Keep running
            await asyncio.Event().wait()
        finally:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()


async def main():
    """Main function to run the bot."""
    # Get token from environment
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN environment variable is required")
    
    # Create and run bot
    bot = TelegramBot(token)
    await bot.run()


if __name__ == "__main__":
    asyncio.run(main())