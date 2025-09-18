#!/usr/bin/env python3
"""Simple RAG demo using project dependencies."""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from loguru import logger as log
from bash import bash

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Setup detailed logging
log_dir = Path(__file__).parent.parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

log_file = log_dir / f"simple_rag_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Configure loguru for detailed logging
log.remove()  # Remove default handler
log.add(sys.stderr, level="INFO", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")
log.add(log_file, level="DEBUG", format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name}:{function}:{line} | {message}")

log.info("=== SIMPLE RAG DEMO SESSION STARTED ===")
log.info(f"Log file: {log_file}")
log.info(f"Working directory: {Path.cwd()}")

def load_transcription_text() -> str:
    """Load the transcription text from our created file."""
    log.debug("Starting transcription loading process")
    
    # Try local data first, fallback to main data
    local_transcript = Path("data/audio/transcript.txt")
    main_transcript = Path(r"../../data/audio/В месяц ты зарабатываешь больше 1млн рублей？ Звезда ＂Реутов ТВ＂ у Дудя.real_transcript.txt")
    
    transcript_file = local_transcript if local_transcript.exists() else main_transcript
    log.info(f"Using transcript file: {transcript_file}")
    
    bash(f"ls -la {transcript_file.parent}")
    
    if not transcript_file.exists():
        log.error(f"Transcript file not found: {transcript_file}")
        raise FileNotFoundError(f"❌ Transcript file not found: {transcript_file}")

    try:
        log.debug(f"Reading transcript file: {transcript_file}")
        with transcript_file.open("r", encoding="utf-8") as f:
            content = f.read()
        
        log.debug(f"Raw content length: {len(content)} characters")
        
        # Extract just the text from timestamped segments
        lines = content.split('\n')
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
        log.info(f"Successfully loaded transcription: {len(text_segments)} segments, {len(full_text)} characters")
        print(f"✅ Loaded transcription: {len(text_segments)} segments, {len(full_text)} characters")
        return full_text
        
    except Exception as e:
        log.error(f"Failed to load transcription: {e}")
        print(f"❌ Failed to load transcription: {e}")
        return ""

def create_simple_rag_qa():
    """Create a simple RAG Q&A system using our project structure."""
    
    log.info("Starting RAG Q&A system creation")
    print("🔧 Creating simple RAG Q&A system...")
    
    # Load transcription
    log.debug("Loading transcription text")
    transcript_text = load_transcription_text()
    if not transcript_text:
        log.error("No transcript text loaded, aborting RAG creation")
        return None
    
    log.info(f"Transcript loaded successfully: {len(transcript_text)} characters")
    
    # Test if our project's RAG components are available
    try:
        log.debug("Attempting to import project components")
        # Try to use project components
        from llm_rag_yt.config.settings import get_config
        from llm_rag_yt.text.processor import TextProcessor
        
        log.info("Project components imported successfully")
        print("✅ Project components available")
        
        # Get configuration
        log.debug("Loading configuration")
        config = get_config()
        log.info(f"Config loaded - chunk_size: {config.chunk_size}, chunk_overlap: {config.chunk_overlap}")
        
        # Create text processor for chunking
        log.debug("Creating TextProcessor instance")
        text_processor = TextProcessor()
        
        # Process the transcript
        log.info("Starting transcript processing")
        print("📝 Processing transcript into chunks...")
        
        log.debug("Normalizing transcript text")
        normalized_text = text_processor.normalize_text(transcript_text)
        log.debug(f"Normalized text length: {len(normalized_text)} characters")
        
        log.debug(f"Splitting into chunks with size={config.chunk_size}, overlap={config.chunk_overlap}")
        processed_chunks = text_processor.split_into_chunks(
            normalized_text,
            chunk_size=config.chunk_size,
            overlap=config.chunk_overlap
        )
        
        log.info(f"Successfully created {len(processed_chunks)} text chunks")
        print(f"✅ Created {len(processed_chunks)} text chunks")
        
        # Create a simple in-memory RAG system
        log.debug("Creating RAG data structure")
        rag_data = {
            "chunks": processed_chunks,
            "full_text": transcript_text,
            "metadata": {
                "source": "YouTube Shorts",
                "title": "В месяц ты зарабатываешь больше 1млн рублей？ Звезда ＂Реутов ТВ＂ у Дудя",
                "language": "ru",
                "chunk_count": len(processed_chunks),
                "created_at": datetime.now().isoformat(),
                "transcript_length": len(transcript_text)
            }
        }
        
        log.info("RAG data structure created successfully")
        log.debug(f"RAG data: {len(rag_data['chunks'])} chunks, metadata: {rag_data['metadata']}")
        return rag_data
        
    except ImportError as e:
        log.warning(f"Project components not available: {e}")
        log.info("Falling back to simple chunking")
        print(f"❌ Project components not available: {e}")
        
        # Fallback: simple chunking
        print("🔄 Using fallback simple chunking...")
        words = transcript_text.split()
        chunk_size = 50  # words per chunk
        chunks = []
        
        log.debug(f"Splitting {len(words)} words into chunks of {chunk_size}")
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)
            log.debug(f"Created chunk {len(chunks)}: '{chunk[:50]}...'")
        
        log.info(f"Created {len(chunks)} simple chunks using fallback method")
        print(f"✅ Created {len(chunks)} simple chunks")
        
        rag_data = {
            "chunks": chunks,
            "full_text": transcript_text,
            "metadata": {
                "source": "YouTube Shorts",
                "title": "В месяц ты зарабатываешь больше 1млн рублей？ Звезда ＂Реутов ТВ＂ у Дудя",
                "language": "ru",
                "chunk_count": len(chunks),
                "created_at": datetime.now().isoformat(),
                "transcript_length": len(transcript_text),
                "method": "fallback_chunking"
            }
        }
        
        return rag_data

def simple_search(query: str, rag_data: Dict[str, Any]) -> List[str]:
    """Simple keyword-based search in chunks."""
    
    log.debug(f"Starting search for query: '{query}'")
    query_words = set(query.lower().split())
    log.debug(f"Query words: {query_words}")
    
    # Score chunks by keyword overlap
    chunk_scores = []
    log.debug(f"Searching through {len(rag_data['chunks'])} chunks")
    
    for i, chunk in enumerate(rag_data["chunks"]):
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
    
    log.info(f"Search completed: {len(top_chunks)} relevant chunks found for query '{query}'")
    return top_chunks

def generate_simple_answer(question: str, context_chunks: List[str], full_text: str) -> str:
    """Generate a simple answer based on context."""
    
    log.debug(f"Generating answer for question: '{question}'")
    log.debug(f"Context chunks available: {len(context_chunks)}")
    
    if not context_chunks:
        log.warning("No context chunks available for answer generation")
        return "Извините, я не нашел релевантной информации в транскрипции для ответа на ваш вопрос."
    
    # Simple keyword-based answer generation
    context = " ".join(context_chunks)
    log.debug(f"Combined context length: {len(context)} characters")
    
    # Common question patterns
    if any(word in question.lower() for word in ["сколько", "зарабатывает", "заработок", "деньги", "рублей"]):
        log.debug("Detected earnings-related question")
        if "миллион" in context.lower():
            answer = "По словам героя видео, он зарабатывает больше миллиона рублей в месяц. Он объясняет, что заниматься множеством разных проектов - актерство, сценарное дело, концерты, блогинг, интеграции и так далее."
            log.info(f"Generated earnings answer: '{answer[:50]}...'")
            return answer
    
    if any(word in question.lower() for word in ["что", "чем", "работа", "деятельность"]):
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

def interactive_simple_qa(rag_data: Dict[str, Any]):
    """Run simple interactive Q&A session."""
    
    log.info("Starting interactive Q&A session")
    log.debug(f"RAG data contains {len(rag_data['chunks'])} chunks")
    
    print("\n" + "="*60)
    print("🤖 ПРОСТАЯ ИНТЕРАКТИВНАЯ СЕССИЯ ВОПРОСОВ И ОТВЕТОВ")
    print("="*60)
    print(f"📹 Видео: {rag_data['metadata']['title']}")
    print(f"📊 Данные: {rag_data['metadata']['chunk_count']} фрагментов текста")
    print("💡 Задавайте вопросы о содержании видео")
    print("⌨️ Напишите 'quit' или 'exit' для выхода")
    print("="*60)
    
    while True:
        try:
            log.debug("Waiting for user input...")
            question = input("\n🤔 Ваш вопрос: ").strip()
            
            if question.lower() in ['quit', 'exit', 'выход', 'q']:
                log.info("User requested to quit interactive session")
                print("👋 До свидания!")
                break
            
            if not question:
                log.debug("Empty question received")
                print("⚠️ Пожалуйста, введите вопрос")
                continue
            
            log.info(f"Processing user question: '{question}'")
            print(f"\n🔍 Ищу информацию для: '{question}'")
            
            # Search for relevant chunks
            log.debug("Starting chunk search")
            relevant_chunks = simple_search(question, rag_data)
            
            # Generate answer
            log.debug("Starting answer generation")
            answer = generate_simple_answer(question, relevant_chunks, rag_data["full_text"])
            
            log.info(f"Generated answer for question '{question}': '{answer[:50]}...'")
            
            print(f"\n💬 ОТВЕТ:")
            print("-" * 40)
            print(answer)
            
            if relevant_chunks:
                log.debug(f"Displaying {len(relevant_chunks)} relevant chunks")
                print(f"\n📚 НАЙДЕННЫЕ ФРАГМЕНТЫ ({len(relevant_chunks)}):")
                print("-" * 40)
                for i, chunk in enumerate(relevant_chunks, 1):
                    preview = chunk[:100] + "..." if len(chunk) > 100 else chunk
                    print(f"{i}. {preview}")
                    log.debug(f"Chunk {i}: '{chunk[:50]}...'")
            
        except KeyboardInterrupt:
            log.info("Interactive session interrupted by user (Ctrl+C)")
            print("\n\n👋 Сессия прервана пользователем")
            break
        except Exception as e:
            log.error(f"Error in interactive session: {e}")
            print(f"\n❌ Ошибка: {e}")

@log.catch
def main():
    """Main function for simple RAG demo."""
    log.info("=== MAIN FUNCTION STARTED ===")
    log.info(f"Script path: {Path(__file__)}")
    log.info(f"Current working directory: {Path.cwd()}")
    log.info(f"Python path: {sys.path[:3]}...")  # First 3 entries
    
    print("🚀 ПРОСТАЯ RAG DEMO - ЗАГРУЗКА ДАННЫХ И Q&A")
    print("="*50)
    
    # Create simple RAG data
    log.info("Creating RAG Q&A system")
    rag_data = create_simple_rag_qa()
    if not rag_data:
        log.error("Failed to create RAG data")
        print("❌ Failed to create RAG data")
        return 1
    
    log.info("RAG data created successfully")
    log.debug(f"RAG metadata: {rag_data['metadata']}")
    
    # Show some examples
    print("\n🧪 ПРИМЕРЫ ВОПРОСОВ:")
    example_questions = [
        "Сколько зарабатывает герой видео?",
        "Чем занимается герой?",
        "Как он зарабатывает деньги?",
        "Что он говорит о работе?"
    ]
    
    for q in example_questions:
        print(f"  • {q}")
    
    # Test one example
    print(f"\n🧪 ТЕСТОВЫЙ ВОПРОС:")
    test_question = "Сколько зарабатывает герой видео?"
    print(f"Вопрос: {test_question}")
    
    log.info(f"Running test question: '{test_question}'")
    relevant_chunks = simple_search(test_question, rag_data)
    answer = generate_simple_answer(test_question, relevant_chunks, rag_data["full_text"])
    print(f"Ответ: {answer}")
    
    log.info(f"Test question completed successfully")
    
    # Start interactive session
    log.info("Starting interactive Q&A session")
    interactive_simple_qa(rag_data)
    
    log.info("=== MAIN FUNCTION COMPLETED ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())