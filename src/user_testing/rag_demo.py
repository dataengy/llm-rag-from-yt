#!/usr/bin/env python3
"""Enhanced RAG demo using full project pipeline and features."""

import json
import sys
from pathlib import Path
from typing import Any, Optional

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from llm_rag_yt._common.logging import log
from llm_rag_yt._common.utils import (
    create_rag_metadata,
    generate_simple_answer,
    load_transcription_text,
    setup_log,
    simple_search,
)
from user_testing.config import get_demo_config


def get_log():
    log = None
    try:
        from loguru import log
    except ImportError:
        # Fallback log for testing without loguru
        class FallbackLogger:
            def debug(self, msg):
                print(f"DEBUG: {msg}")

            def info(self, msg):
                print(f"INFO: {msg}")

            def warning(self, msg):
                print(f"WARNING: {msg}")

            def error(self, msg):
                print(f"ERROR: {msg}")

            def catch(self, func):
                return func

        log = FallbackLogger()

    # Mock loguru for project modules that depend on it
    import sys

    if "loguru" not in sys.modules:
        sys.modules["loguru"] = type(sys)("loguru")
        sys.modules["loguru"].log = log

    try:
        from llm_rag_yt._common.config.settings import Config, get_config
        from llm_rag_yt.pipeline import RAGPipeline

        log.info("Full RAG pipeline available")
    except ImportError as e:
        log.warning(f"Full pipeline not available: {e}")

        # Create dummy classes for type hints when full pipeline unavailable
        class RAGPipeline:
            pass

    assert log
    return log


def create_enhanced_rag_system() -> Optional[RAGPipeline]:
    """Create an enhanced RAG system using the full project pipeline."""
    demo_config = get_demo_config()

    log.info("Starting enhanced RAG system creation")
    print("🔧 Creating enhanced RAG system with full pipeline...")

    # Load transcription using utility function
    log.debug("Loading transcription text")
    transcript_text = load_transcription_text(demo_config.transcript_paths)
    if not transcript_text:
        log.error("No transcript text loaded, aborting RAG creation")
        return None

    log.info(f"Transcript loaded successfully: {len(transcript_text)} characters")

    try:
        # Initialize full RAG pipeline with project configuration
        log.debug("Initializing RAG pipeline")
        project_config = get_config()
        rag_pipeline = RAGPipeline(project_config)

        log.info("RAG pipeline initialized successfully")
        print("✅ RAG pipeline components loaded")

        # Create mock transcription data structure that pipeline expects
        mock_file_id = "demo_transcript"
        mock_transcription = {
            mock_file_id: {
                "full_text": transcript_text,
                "segments": [],  # Not needed for this demo
                "language": "ru",
            }
        }

        # Process transcript through the text processor
        log.info("Processing transcript through pipeline")
        print("📝 Processing transcript with TextProcessor...")

        normalized_texts = rag_pipeline.text_processor.process_transcriptions(
            mock_transcription, project_config.chunk_size, project_config.chunk_overlap
        )

        # Create chunks with proper metadata
        chunks = rag_pipeline.text_processor.create_chunks(
            normalized_texts, project_config.chunk_size, project_config.chunk_overlap
        )

        log.info(f"Created {len(chunks)} chunks with metadata")
        print(f"✅ Created {len(chunks)} chunks with metadata")

        # Store chunks in vector database
        log.info("Storing chunks in vector database")
        print("🗃️ Indexing chunks in vector database...")

        rag_pipeline.vector_store.upsert_chunks(rag_pipeline.encoder, chunks)

        log.info("Chunks successfully stored in vector database")
        print("✅ Vector database ready for queries")

        # Save processing artifacts
        log.debug("Saving processing artifacts")
        rag_pipeline._save_artifacts(
            "demo_normalized", {"normalized_texts": normalized_texts}
        )

        # Store demo metadata
        metadata = create_rag_metadata(
            title=demo_config.video_title,
            chunk_count=len(chunks),
            transcript_length=len(transcript_text),
            method="full_pipeline",
            vector_store_collection=project_config.collection_name,
        )

        with open(
            project_config.artifacts_dir / "demo_metadata.json", "w", encoding="utf-8"
        ) as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        log.info("Enhanced RAG system created successfully")
        return rag_pipeline

    except Exception as e:
        log.error(f"Failed to create enhanced RAG system: {e}")
        print(f"❌ Failed to create enhanced RAG system: {e}")
        return None


def create_fallback_rag_system() -> Optional[dict[str, Any]]:
    """Create a fallback RAG system using basic text processing when full pipeline unavailable."""
    demo_config = get_demo_config()

    log.info("Creating fallback RAG system")
    print("🔧 Creating fallback RAG system (basic text processing)...")

    # Load transcription using utility function
    log.debug("Loading transcription text")
    transcript_text = load_transcription_text(demo_config.transcript_paths)
    if not transcript_text:
        log.error("No transcript text loaded, aborting RAG creation")
        return None

    log.info(f"Transcript loaded successfully: {len(transcript_text)} characters")

    try:
        from llm_rag_yt._common.config.settings import get_config
        from llm_rag_yt.text.processor import TextProcessor

        project_config = get_config()
        text_processor = TextProcessor()

        # Process the transcript
        log.info("Starting transcript processing with fallback method")
        print("📝 Processing transcript into chunks (fallback mode)...")

        normalized_text = text_processor.normalize_text(transcript_text)
        processed_chunks = text_processor.split_into_chunks(
            normalized_text,
            chunk_size=project_config.chunk_size,
            overlap=project_config.chunk_overlap,
        )

        log.info(f"Successfully created {len(processed_chunks)} text chunks")
        print(f"✅ Created {len(processed_chunks)} text chunks")

        metadata = create_rag_metadata(
            title=demo_config.video_title,
            chunk_count=len(processed_chunks),
            transcript_length=len(transcript_text),
            method="fallback_text_processor",
        )

        rag_data = {
            "chunks": processed_chunks,
            "full_text": transcript_text,
            "metadata": metadata,
        }

        log.info("Fallback RAG data structure created successfully")
        return rag_data

    except Exception as e:
        log.error(f"Failed to create fallback RAG system: {e}")
        print(f"❌ Failed to create fallback RAG system: {e}")
        return None


def interactive_fallback_qa(rag_data: dict[str, Any]):
    """Run fallback interactive Q&A session using basic search."""

    log.info("Starting fallback interactive Q&A session")

    print("\n" + "=" * 70)
    print("🤖 БАЗОВАЯ ИНТЕРАКТИВНАЯ СЕССИЯ ВОПРОСОВ И ОТВЕТОВ")
    print("=" * 70)
    print(f"📹 Видео: {rag_data['metadata']['title']}")
    print(f"📊 Данные: {rag_data['metadata']['chunk_count']} фрагментов текста")
    print("💡 Задавайте вопросы о содержании видео")
    print("⌨️ Команды: 'quit'/'exit' для выхода")
    print("⚠️  Используется базовый поиск (без AI-генерации)")
    print("=" * 70)

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

            print("\n💬 ОТВЕТ (базовый поиск):")
            print("-" * 50)
            print(answer)

            if relevant_chunks:
                log.debug(f"Displaying {len(relevant_chunks)} relevant chunks")
                print(f"\n📚 НАЙДЕННЫЕ ФРАГМЕНТЫ ({len(relevant_chunks)}):")
                print("-" * 50)
                for i, chunk in enumerate(relevant_chunks, 1):
                    preview = chunk[:120] + "..." if len(chunk) > 120 else chunk
                    print(f"{i}. {preview}")
                    log.debug(f"Chunk {i}: '{chunk[:50]}...'")

        except KeyboardInterrupt:
            log.info("Interactive session interrupted by user (Ctrl+C)")
            print("\n\n👋 Сессия прервана пользователем")
            break
        except Exception as e:
            log.error(f"Error in interactive session: {e}")
            print(f"\n❌ Ошибка: {e}")


def interactive_enhanced_qa(rag_pipeline: RAGPipeline):
    """Run enhanced interactive Q&A session using full RAG pipeline."""

    log.info("Starting enhanced interactive Q&A session")

    # Get pipeline status for display
    status = rag_pipeline.get_status()
    collection_info = status["collection"]

    print("\n" + "=" * 70)
    print("🤖 РАСШИРЕННАЯ ИНТЕРАКТИВНАЯ СЕССИЯ ВОПРОСОВ И ОТВЕТОВ")
    print("=" * 70)
    print(f"📹 Видео: {get_demo_config().video_title}")
    print(
        f"📊 Коллекция: {collection_info['name']} ({collection_info['count']} документов)"
    )
    print(f"🧠 Модель: {rag_pipeline.config.openai_model}")
    print(f"🔍 Embedding: {rag_pipeline.config.embedding_model.split('/')[-1]}")
    print("💡 Задавайте вопросы о содержании видео")
    print("⌨️ Команды: 'quit'/'exit' для выхода, 'status' для статуса системы")
    print("=" * 70)

    while True:
        try:
            log.debug("Waiting for user input...")
            question = input("\n🤔 Ваш вопрос: ").strip()

            if question.lower() in ["quit", "exit", "выход", "q"]:
                log.info("User requested to quit interactive session")
                print("👋 До свидания!")
                break

            if question.lower() in ["status", "статус"]:
                log.debug("User requested system status")
                status = rag_pipeline.get_status()
                print("\n📊 СТАТУС СИСТЕМЫ:")
                print(f"  • Коллекция: {status['collection']['name']}")
                print(f"  • Документов: {status['collection']['count']}")
                print(f"  • Модель ИИ: {rag_pipeline.config.openai_model}")
                print(f"  • Размер чанка: {rag_pipeline.config.chunk_size} слов")
                print(f"  • Перекрытие: {rag_pipeline.config.chunk_overlap} слов")
                print(f"  • Top-K: {rag_pipeline.config.top_k}")
                continue

            if not question:
                log.debug("Empty question received")
                print("⚠️ Пожалуйста, введите вопрос")
                continue

            log.info(f"Processing user question: '{question}'")
            print(f"\n🔍 Обрабатываю запрос: '{question}'")

            # Query using full RAG pipeline with advanced features
            log.debug("Querying RAG pipeline")
            result = rag_pipeline.query(question, top_k=rag_pipeline.config.top_k)

            log.info(
                f"Generated answer in {result['response_time']:.2f}s using {result['search_method']} search"
            )

            print(
                f"\n💬 ОТВЕТ ({result['search_method']} поиск, {result['response_time']:.2f}с):"
            )
            print("-" * 50)
            print(result["answer"])

            if result["sources"]:
                log.debug(f"Displaying {len(result['sources'])} source documents")
                print(f"\n📚 ИСТОЧНИКИ ({len(result['sources'])}):")
                print("-" * 50)
                for i, source in enumerate(result["sources"], 1):
                    text_preview = (
                        source["text"][:120] + "..."
                        if len(source["text"]) > 120
                        else source["text"]
                    )
                    similarity = source.get("similarity", "N/A")
                    chunk_id = source.get("metadata", {}).get("source_id", "unknown")
                    print(f"{i}. [{chunk_id}] (sim: {similarity}) {text_preview}")
                    log.debug(
                        f"Source {i}: chunk_id={chunk_id}, similarity={similarity}"
                    )

        except KeyboardInterrupt:
            log.info("Interactive session interrupted by user (Ctrl+C)")
            print("\n\n👋 Сессия прервана пользователем")
            break
        except Exception as e:
            log.error(f"Error in interactive session: {e}")
            print(f"\n❌ Ошибка: {e}")
            print("💡 Убедитесь, что установлены переменные окружения OPENAI_API_KEY")


def main():
    """Main function for enhanced RAG demo."""
    # Setup log first
    setup_log(script_name="enhanced_rag_demo")

    log.info("=== ENHANCED RAG DEMO STARTED ===")
    log.info(f"Script path: {Path(__file__)}")
    log.info(f"Current working directory: {Path.cwd()}")
    log.info(f"Python path: {sys.path[:3]}...")  # First 3 entries

    print("🚀 РАСШИРЕННАЯ RAG DEMO - ПОЛНЫЙ PIPELINE И Q&A")
    print("=" * 60)

    # Try to create enhanced RAG system first
    if FULL_PIPELINE_AVAILABLE:
        log.info("Attempting to create enhanced RAG system")
        rag_pipeline = create_enhanced_rag_system()

        if rag_pipeline:
            log.info("Enhanced RAG system created successfully")

            # Show system status
            status = rag_pipeline.get_status()
            print("\n✅ Полная система готова:")
            print(
                f"  • Коллекция: {status['collection']['name']} ({status['collection']['count']} документов)"
            )
            print(f"  • Модель ИИ: {rag_pipeline.config.openai_model}")
            print(
                f"  • Embedding модель: {rag_pipeline.config.embedding_model.split('/')[-1]}"
            )

            # Show some examples from config
            config = get_demo_config()
            print("\n🧪 ПРИМЕРЫ ВОПРОСОВ:")
            for q in config.example_questions:
                print(f"  • {q}")

            # Test one example using the full pipeline
            print("\n🧪 ТЕСТОВЫЙ ВОПРОС С ПОЛНЫМ PIPELINE:")
            test_question = "Сколько зарабатывает герой видео?"
            print(f"Вопрос: {test_question}")

            log.info(f"Running test question through full pipeline: '{test_question}'")
            try:
                result = rag_pipeline.query(test_question, top_k=3)
                print(
                    f"Ответ ({result['search_method']} поиск, {result['response_time']:.2f}с): {result['answer']}"
                )
                print(f"Источников найдено: {len(result['sources'])}")
                log.info(
                    f"Test question completed successfully in {result['response_time']:.2f}s"
                )
            except Exception as e:
                log.error(f"Test question failed: {e}")
                print(f"❌ Ошибка в тестовом вопросе: {e}")
                print("💡 Проверьте OPENAI_API_KEY в переменных окружения")

            # Start enhanced interactive session
            log.info("Starting enhanced interactive Q&A session")
            interactive_enhanced_qa(rag_pipeline)

            log.info("=== ENHANCED RAG DEMO COMPLETED ===")
            return 0

    # Fallback to basic system if enhanced fails
    log.warning("Enhanced pipeline not available, falling back to basic system")
    print("\n⚠️  Полный pipeline недоступен, переключение на базовую систему...")
    print(
        "💡 Для полной функциональности установите: chromadb, sentence-transformers, openai, loguru"
    )

    rag_data = create_fallback_rag_system()
    if not rag_data:
        log.error("Failed to create any RAG system")
        print("❌ Не удалось создать RAG систему")
        return 1

    log.info("Fallback RAG system created successfully")
    print("\n✅ Базовая система готова:")
    print(f"  • Фрагментов: {rag_data['metadata']['chunk_count']}")
    print(f"  • Метод: {rag_data['metadata'].get('method', 'unknown')}")

    # Show some examples from config
    config = get_demo_config()
    print("\n🧪 ПРИМЕРЫ ВОПРОСОВ:")
    for q in config.example_questions:
        print(f"  • {q}")

    # Test one example using fallback
    print("\n🧪 ТЕСТОВЫЙ ВОПРОС С БАЗОВЫМ ПОИСКОМ:")
    test_question = "Сколько зарабатывает герой видео?"
    print(f"Вопрос: {test_question}")

    log.info(f"Running test question through fallback system: '{test_question}'")
    try:
        from llm_rag_yt._common.utils import generate_simple_answer, simple_search

        relevant_chunks = simple_search(test_question, rag_data["chunks"])
        answer = generate_simple_answer(
            test_question, relevant_chunks, rag_data["full_text"]
        )
        print(f"Ответ (базовый поиск): {answer}")
        print(f"Фрагментов найдено: {len(relevant_chunks)}")
        log.info("Test question completed successfully")
    except Exception as e:
        log.error(f"Test question failed: {e}")
        print(f"❌ Ошибка в тестовом вопросе: {e}")

    # Start fallback interactive session
    log.info("Starting fallback interactive Q&A session")
    interactive_fallback_qa(rag_data)

    log.info("=== FALLBACK RAG DEMO COMPLETED ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
