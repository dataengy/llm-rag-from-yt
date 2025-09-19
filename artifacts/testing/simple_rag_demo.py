#!/usr/bin/env python3
"""Simple RAG demo using project dependencies."""

import sys
from pathlib import Path
from typing import List, Dict, Any

# Import common utilities
from utils import (
    setup_python_path, setup_logging, load_transcription_text,
    create_simple_chunks, simple_search, generate_simple_answer,
    interactive_qa_session, create_rag_metadata, print_session_header
)

# Setup Python path and logging
setup_python_path()
log_file = setup_logging('simple_rag_demo')

def create_simple_rag_qa():
    """Create a simple RAG Q&A system using our project structure."""
    
    log.info("Starting RAG Q&A system creation")
    print("🔧 Creating simple RAG Q&A system...")
    
    # Load transcription
    log.debug("Loading transcription text")
    # Try local data first, fallback to main data
    local_transcript = Path("data/audio/transcript.txt")
    main_transcript = Path(r"../../data/audio/В месяц ты зарабатываешь больше 1млн рублей？ Звезда ＂Реутов ТВ＂ у Дудя.real_transcript.txt")
    
    transcript_file = local_transcript if local_transcript.exists() else main_transcript
    transcript_text = load_transcription_text(transcript_file)
    
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
            "metadata": create_rag_metadata(
                source="YouTube Shorts",
                title="В месяц ты зарабатываешь больше 1млн рублей？ Звезда ＂Реутов ТВ＂ у Дудя",
                language="ru",
                chunk_count=len(processed_chunks),
                transcript_length=len(transcript_text)
            )
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
        chunks = create_simple_chunks(transcript_text, chunk_size=50)
        
        log.info(f"Created {len(chunks)} simple chunks using fallback method")
        print(f"✅ Created {len(chunks)} simple chunks")
        
        rag_data = {
            "chunks": [chunk['text'] for chunk in chunks],  # Extract text for compatibility
            "full_text": transcript_text,
            "metadata": create_rag_metadata(
                source="YouTube Shorts",
                title="В месяц ты зарабатываешь больше 1млн рублей？ Звезда ＂Реутов ТВ＂ у Дудя",
                language="ru",
                chunk_count=len(chunks),
                transcript_length=len(transcript_text),
                method="fallback_chunking"
            )
        }
        
        return rag_data

@log.catch
def main():
    """Main function for simple RAG demo."""
    log.info("=== MAIN FUNCTION STARTED ===")
    log.info(f"Script path: {Path(__file__)}")
    log.info(f"Current working directory: {Path.cwd()}")
    log.info(f"Python path: {sys.path[:3]}...")  # First 3 entries
    
    print_session_header("ПРОСТАЯ RAG DEMO - ЗАГРУЗКА ДАННЫХ И Q&A")
    
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
    print("
🧪 ПРИМЕРЫ ВОПРОСОВ:")
    example_questions = [
        "Сколько зарабатывает герой видео?",
        "Чем занимается герой?",
        "Как он зарабатывает деньги?",
        "Что он говорит о работе?"
    ]
    
    for q in example_questions:
        print(f"  • {q}")
    
    # Test one example
    print(f"
🧪 ТЕСТОВЫЙ ВОПРОС:")
    test_question = "Сколько зарабатывает герой видео?"
    print(f"Вопрос: {test_question}")
    
    log.info(f"Running test question: '{test_question}'")
    relevant_chunks = simple_search(test_question, rag_data)
    answer = generate_simple_answer(test_question, relevant_chunks, rag_data["full_text"])
    print(f"Ответ: {answer}")
    
    log.info(f"Test question completed successfully")
    
    # Start interactive session
    log.info("Starting interactive Q&A session")
    interactive_qa_session(rag_data, simple_search, generate_simple_answer, "ПРОСТАЯ ИНТЕРАКТИВНАЯ СЕССИЯ ВОПРОСОВ И ОТВЕТОВ")
    
    log.info("=== MAIN FUNCTION COMPLETED ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())
