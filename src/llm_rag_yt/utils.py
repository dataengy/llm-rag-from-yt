"""Utility functions and logger setup for RAG demo."""

import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

try:
    from loguru import logger as log
except ImportError:
    # Fallback logger for testing without loguru
    class FallbackLogger:
        def debug(self, msg): print(f"DEBUG: {msg}")
        def info(self, msg): print(f"INFO: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
    log = FallbackLogger()


def setup_logger(log_dir: Path = None, script_name: str = "rag_demo") -> None:
    """Setup detailed logging configuration.
    
    Args:
        log_dir: Directory for log files. Defaults to project root/logs
        script_name: Name for log file prefix
    """
    # Check if we have the real loguru or fallback
    if hasattr(log, 'remove'):
        # Real loguru setup
        if log_dir is None:
            log_dir = Path(__file__).parent.parent / "logs"
        
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / f"{script_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

        # Configure loguru for detailed logging
        log.remove()  # Remove default handler
        log.add(
            sys.stderr, level="INFO", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
        )
        log.add(
            log_file,
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name}:{function}:{line} | {message}",
        )
        log.info(f"Log file: {log_file}")
    else:
        # Fallback logger - just print session info
        pass

    log.info(f"=== {script_name.upper()} SESSION STARTED ===")
    log.info(f"Working directory: {Path.cwd()}")


def load_transcription_text(transcript_paths: list[Path]) -> str:
    """Load the transcription text from provided file paths.
    
    Args:
        transcript_paths: List of potential transcript file paths
        
    Returns:
        Loaded transcript text
        
    Raises:
        FileNotFoundError: If no transcript file is found
    """
    log.debug("Starting transcription loading process")

    transcript_file = None
    for path in transcript_paths:
        if path.exists():
            transcript_file = path
            break

    if transcript_file is None:
        log.error(f"Transcript file not found in any of: {transcript_paths}")
        raise FileNotFoundError(f"❌ Transcript file not found in any of: {transcript_paths}")

    log.info(f"Using transcript file: {transcript_file}")

    try:
        log.debug(f"Reading transcript file: {transcript_file}")
        with transcript_file.open("r", encoding="utf-8") as f:
            content = f.read()

        log.debug(f"Raw content length: {len(content)} characters")

        # Extract just the text from timestamped segments
        lines = content.split("\n")
        text_segments = []

        log.debug(f"Processing {len(lines)} lines")
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith("[") and "]" in line:
                # Extract text after timestamp
                text_part = line.split("]", 1)[1].strip()
                if text_part:
                    text_segments.append(text_part)
                    log.debug(f"Line {i}: extracted segment '{text_part[:50]}...'")

        full_text = " ".join(text_segments)
        log.info(
            f"Successfully loaded transcription: {len(text_segments)} segments, {len(full_text)} characters"
        )
        print(
            f"✅ Loaded transcription: {len(text_segments)} segments, {len(full_text)} characters"
        )
        return full_text

    except Exception as e:
        log.error(f"Failed to load transcription: {e}")
        print(f"❌ Failed to load transcription: {e}")
        return ""


def simple_search(query: str, chunks: list[str]) -> list[str]:
    """Simple keyword-based search in chunks.
    
    Args:
        query: Search query
        chunks: List of text chunks to search
        
    Returns:
        Top 3 matching chunks
    """
    log.debug(f"Starting search for query: '{query}'")
    query_words = set(query.lower().split())
    log.debug(f"Query words: {query_words}")

    # Score chunks by keyword overlap
    chunk_scores = []
    log.debug(f"Searching through {len(chunks)} chunks")

    for i, chunk in enumerate(chunks):
        chunk_words = set(chunk.lower().split())
        overlap = len(query_words.intersection(chunk_words))
        if overlap > 0:
            chunk_scores.append((overlap, i, chunk))
            log.debug(f"Chunk {i}: {overlap} word overlap - '{chunk[:50]}...'")

    # Sort by score and return top matches
    chunk_scores.sort(reverse=True, key=lambda x: x[0])
    log.debug(f"Found {len(chunk_scores)} matching chunks, returning top 3")

    # Return top 3 chunks
    top_chunks = []
    for score, idx, chunk in chunk_scores[:3]:
        top_chunks.append(chunk)
        log.debug(f"Top chunk (score {score}): '{chunk[:50]}...'")

    log.info(
        f"Search completed: {len(top_chunks)} relevant chunks found for query '{query}'"
    )
    return top_chunks


def generate_simple_answer(question: str, context_chunks: list[str], full_text: str) -> str:
    """Generate a simple answer based on context.
    
    Args:
        question: User question
        context_chunks: Relevant text chunks
        full_text: Full transcript text
        
    Returns:
        Generated answer
    """
    log.debug(f"Generating answer for question: '{question}'")
    log.debug(f"Context chunks available: {len(context_chunks)}")

    if not context_chunks:
        log.warning("No context chunks available for answer generation")
        return "Извините, я не нашел релевантной информации в транскрипции для ответа на ваш вопрос."

    # Simple keyword-based answer generation
    context = " ".join(context_chunks)
    log.debug(f"Combined context length: {len(context)} characters")

    # Common question patterns
    if any(
        word in question.lower()
        for word in ["сколько", "зарабатывает", "заработок", "деньги", "рублей"]
    ):
        log.debug("Detected earnings-related question")
        if "миллион" in context.lower():
            answer = "По словам героя видео, он зарабатывает больше миллиона рублей в месяц. Он объясняет, что заниматься множеством разных проектов - актерство, сценарное дело, концерты, блогинг, интеграции и так далее."
            log.info(f"Generated earnings answer: '{answer[:50]}...'")
            return answer

    if any(
        word in question.lower() for word in ["что", "чем", "работа", "деятельность"]
    ):
        log.debug("Detected work/activity-related question")
        if "актер" in context.lower() or "сценарист" in context.lower():
            answer = "Герой видео рассказывает, что он трудоголик и занимается множеством разных видов деятельности: актерство, сценарное дело, проведение мероприятий, концерты, блогинг, интеграции и другое."
            log.info(f"Generated activity answer: '{answer[:50]}...'")
            return answer

    if any(word in question.lower() for word in ["как", "каким образом"]):
        log.debug("Detected how/method-related question")
        answer = "Герой видео объясняет, что самая большая проблема - рассказать, чем именно он зарабатывает, потому что он делает очень много всего. Он работает как актер, сценарист, проводит мероприятия, выступает на концертах, ведет блог и занимается интеграциями."
        log.info(f"Generated method answer: '{answer[:50]}...'")
        return answer

    # Default response with context
    log.debug("Using default answer template with context")
    answer = f"На основе транскрипции видео: {context[:200]}..."
    log.info(f"Generated default answer: '{answer[:50]}...'")
    return answer


def create_rag_metadata(title: str, chunk_count: int, transcript_length: int, **kwargs) -> Dict[str, Any]:
    """Create metadata for RAG data structure.
    
    Args:
        title: Video title
        chunk_count: Number of chunks
        transcript_length: Length of transcript
        **kwargs: Additional metadata fields
        
    Returns:
        Metadata dictionary
    """
    metadata = {
        "source": "YouTube Shorts",
        "title": title,
        "language": "ru",
        "chunk_count": chunk_count,
        "created_at": datetime.now().isoformat(),
        "transcript_length": transcript_length,
    }
    metadata.update(kwargs)
    
    log.debug(f"Created metadata: {metadata}")
    return metadata