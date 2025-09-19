#!/usr/bin/env python3
"""Simple RAG demo using project dependencies."""

import sys
from pathlib import Path
from typing import Dict, Any

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from loguru import logger as log
except ImportError:
    # Fallback logger for testing without loguru
    class FallbackLogger:
        def debug(self, msg): print(f"DEBUG: {msg}")
        def info(self, msg): print(f"INFO: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
        def catch(self, func):
            return func
    log = FallbackLogger()
from utils import setup_logger, load_transcription_text, simple_search, generate_simple_answer, create_rag_metadata
from user_testing.config import get_demo_config




def create_simple_rag_qa():
    """Create a simple RAG Q&A system using our project structure."""
    config = get_demo_config()
    
    log.info("Starting RAG Q&A system creation")
    print("🔧 Creating simple RAG Q&A system...")

    # Load transcription using utility function
    log.debug("Loading transcription text")
    transcript_text = load_transcription_text(config.transcript_paths)
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

        # Get project configuration for chunking
        log.debug("Loading project configuration")
        project_config = get_config()
        log.info(
            f"Project config loaded - chunk_size: {project_config.chunk_size}, chunk_overlap: {project_config.chunk_overlap}"
        )

        # Create text processor for chunking
        log.debug("Creating TextProcessor instance")
        text_processor = TextProcessor()

        # Process the transcript
        log.info("Starting transcript processing")
        print("📝 Processing transcript into chunks...")

        log.debug("Normalizing transcript text")
        normalized_text = text_processor.normalize_text(transcript_text)
        log.debug(f"Normalized text length: {len(normalized_text)} characters")

        log.debug(
            f"Splitting into chunks with size={project_config.chunk_size}, overlap={project_config.chunk_overlap}"
        )
        processed_chunks = text_processor.split_into_chunks(
            normalized_text, chunk_size=project_config.chunk_size, overlap=project_config.chunk_overlap
        )

        log.info(f"Successfully created {len(processed_chunks)} text chunks")
        print(f"✅ Created {len(processed_chunks)} text chunks")

        # Create a simple in-memory RAG system
        log.debug("Creating RAG data structure")
        metadata = create_rag_metadata(
            title=config.video_title,
            chunk_count=len(processed_chunks),
            transcript_length=len(transcript_text)
        )
        
        rag_data = {
            "chunks": processed_chunks,
            "full_text": transcript_text,
            "metadata": metadata,
        }

        log.info("RAG data structure created successfully")
        log.debug(
            f"RAG data: {len(rag_data['chunks'])} chunks, metadata: {rag_data['metadata']}"
        )
        return rag_data

    except ImportError as e:
        log.warning(f"Project components not available: {e}")
        log.info("Falling back to simple chunking")
        print(f"❌ Project components not available: {e}")

        # Fallback: simple chunking
        print("🔄 Using fallback simple chunking...")
        words = transcript_text.split()
        chunk_size = config.fallback_chunk_size
        chunks = []

        log.debug(f"Splitting {len(words)} words into chunks of {chunk_size}")
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i : i + chunk_size])
            chunks.append(chunk)
            log.debug(f"Created chunk {len(chunks)}: '{chunk[:50]}...'")

        log.info(f"Created {len(chunks)} simple chunks using fallback method")
        print(f"✅ Created {len(chunks)} simple chunks")

        metadata = create_rag_metadata(
            title=config.video_title,
            chunk_count=len(chunks),
            transcript_length=len(transcript_text),
            method="fallback_chunking"
        )
        
        rag_data = {
            "chunks": chunks,
            "full_text": transcript_text,
            "metadata": metadata,
        }

        return rag_data






def interactive_simple_qa(rag_data: Dict[str, Any]):
    """Run simple interactive Q&A session."""

    log.info("Starting interactive Q&A session")
    log.debug(f"RAG data contains {len(rag_data['chunks'])} chunks")

    print("\n" + "=" * 60)
    print("🤖 ПРОСТАЯ ИНТЕРАКТИВНАЯ СЕССИЯ ВОПРОСОВ И ОТВЕТОВ")
    print("=" * 60)
    print(f"📹 Видео: {rag_data['metadata']['title']}")
    print(f"📊 Данные: {rag_data['metadata']['chunk_count']} фрагментов текста")
    print("💡 Задавайте вопросы о содержании видео")
    print("⌨️ Напишите 'quit' или 'exit' для выхода")
    print("=" * 60)

    while True:
        try:
            log.debug("Waiting for user input...")
            question = input("\n🤔 Ваш вопрос: ").strip()

            if question.lower() in ["quit", "exit", "выход", "q"]:
                log.info("User requested to quit interactive session")
                print("👋 До свидания!")
                break

            if not question:
                log.debug("Empty question received")
                print("⚠️ Пожалуйста, введите вопрос")
                continue

            log.info(f"Processing user question: '{question}'")
            print(f"\n🔍 Ищу информацию для: '{question}'")

            # Search for relevant chunks using utility function
            log.debug("Starting chunk search")
            relevant_chunks = simple_search(question, rag_data["chunks"])

            # Generate answer using utility function
            log.debug("Starting answer generation")
            answer = generate_simple_answer(
                question, relevant_chunks, rag_data["full_text"]
            )

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
    # Setup logger first
    setup_logger(script_name="rag_demo")
    
    log.info("=== MAIN FUNCTION STARTED ===")
    log.info(f"Script path: {Path(__file__)}")
    log.info(f"Current working directory: {Path.cwd()}")
    log.info(f"Python path: {sys.path[:3]}...")  # First 3 entries

    print("🚀 ПРОСТАЯ RAG DEMO - ЗАГРУЗКА ДАННЫХ И Q&A")
    print("=" * 50)

    # Create simple RAG data
    log.info("Creating RAG Q&A system")
    rag_data = create_simple_rag_qa()
    if not rag_data:
        log.error("Failed to create RAG data")
        print("❌ Failed to create RAG data")
        return 1

    log.info("RAG data created successfully")
    log.debug(f"RAG metadata: {rag_data['metadata']}")

    # Show some examples from config
    config = get_demo_config()
    print("\n🧪 ПРИМЕРЫ ВОПРОСОВ:")
    for q in config.example_questions:
        print(f"  • {q}")

    # Test one example
    print(f"\n🧪 ТЕСТОВЫЙ ВОПРОС:")
    test_question = "Сколько зарабатывает герой видео?"
    print(f"Вопрос: {test_question}")

    log.info(f"Running test question: '{test_question}'")
    relevant_chunks = simple_search(test_question, rag_data["chunks"])
    answer = generate_simple_answer(
        test_question, relevant_chunks, rag_data["full_text"]
    )
    print(f"Ответ: {answer}")

    log.info(f"Test question completed successfully")

    # Start interactive session
    log.info("Starting interactive Q&A session")
    interactive_simple_qa(rag_data)

    log.info("=== MAIN FUNCTION COMPLETED ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
