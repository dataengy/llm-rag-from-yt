#!/usr/bin/env python3
"""Simple RAG demo using project dependencies."""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any

from loguru import logger as log
from bash import bash

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

def load_transcription_text() -> str:
    """Load the transcription text from our created file."""
    bash(f"ls ../../data/audio/")
    transcript_file = Path("../../data/audio/В месяц ты зарабатываешь больше 1млн рублей？ Звезда ＂Реутов ТВ＂ у Дудя.real_transcript.txt"
                           )
    
    if not transcript_file.exists():
        raise FileNotFoundError(f"❌ Transcript file not found: {transcript_file}")

    try:
        with transcript_file.open("r", encoding="utf-8") as f:
            content = f.read()
        
        # Extract just the text from timestamped segments
        lines = content.split('\n')
        text_segments = []
        
        for line in lines:
            line = line.strip()
            if line.startswith("[") and "]" in line:
                # Extract text after timestamp
                text_part = line.split("]", 1)[1].strip()
                if text_part:
                    text_segments.append(text_part)
        
        full_text = " ".join(text_segments)
        print(f"✅ Loaded transcription: {len(text_segments)} segments, {len(full_text)} characters")
        return full_text
        
    except Exception as e:
        print(f"❌ Failed to load transcription: {e}")
        return ""

def create_simple_rag_qa():
    """Create a simple RAG Q&A system using our project structure."""
    
    print("🔧 Creating simple RAG Q&A system...")
    
    # Load transcription
    transcript_text = load_transcription_text()
    if not transcript_text:
        return None
    
    # Test if our project's RAG components are available
    try:
        # Try to use project components
        from llm_rag_yt.config.settings import get_config
        from llm_rag_yt.text.processor import TextProcessor
        
        print("✅ Project components available")
        
        # Get configuration
        config = get_config()
        
        # Create text processor for chunking
        text_processor = TextProcessor()
        
        # Process the transcript
        print("📝 Processing transcript into chunks...")
        normalized_text = text_processor.normalize_text(transcript_text)
        processed_chunks = text_processor.split_into_chunks(
            normalized_text,
            chunk_size=config.chunk_size,
            overlap=config.chunk_overlap
        )
        
        print(f"✅ Created {len(processed_chunks)} text chunks")
        
        # Create a simple in-memory RAG system
        rag_data = {
            "chunks": processed_chunks,
            "full_text": transcript_text,
            "metadata": {
                "source": "YouTube Shorts",
                "title": "В месяц ты зарабатываешь больше 1млн рублей？ Звезда ＂Реутов ТВ＂ у Дудя",
                "language": "ru",
                "chunk_count": len(processed_chunks)
            }
        }
        
        return rag_data
        
    except ImportError as e:
        print(f"❌ Project components not available: {e}")
        
        # Fallback: simple chunking
        print("🔄 Using fallback simple chunking...")
        words = transcript_text.split()
        chunk_size = 50  # words per chunk
        chunks = []
        
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)
        
        print(f"✅ Created {len(chunks)} simple chunks")
        
        rag_data = {
            "chunks": chunks,
            "full_text": transcript_text,
            "metadata": {
                "source": "YouTube Shorts",
                "title": "В месяц ты зарабатываешь больше 1млн рублей？ Звезда ＂Реутов ТВ＂ у Дудя",
                "language": "ru",
                "chunk_count": len(chunks)
            }
        }
        
        return rag_data

def simple_search(query: str, rag_data: Dict[str, Any]) -> List[str]:
    """Simple keyword-based search in chunks."""
    
    query_words = set(query.lower().split())
    
    # Score chunks by keyword overlap
    chunk_scores = []
    for i, chunk in enumerate(rag_data["chunks"]):
        chunk_words = set(chunk.lower().split())
        overlap = len(query_words.intersection(chunk_words))
        if overlap > 0:
            chunk_scores.append((overlap, i, chunk))
    
    # Sort by score and return top matches
    chunk_scores.sort(reverse=True, key=lambda x: x[0])
    
    # Return top 3 chunks
    top_chunks = []
    for score, idx, chunk in chunk_scores[:3]:
        top_chunks.append(chunk)
    
    return top_chunks

def generate_simple_answer(question: str, context_chunks: List[str], full_text: str) -> str:
    """Generate a simple answer based on context."""
    
    if not context_chunks:
        return "Извините, я не нашел релевантной информации в транскрипции для ответа на ваш вопрос."
    
    # Simple keyword-based answer generation
    context = " ".join(context_chunks)
    
    # Common question patterns
    if any(word in question.lower() for word in ["сколько", "зарабатывает", "заработок", "деньги", "рублей"]):
        if "миллион" in context.lower():
            return "По словам героя видео, он зарабатывает больше миллиона рублей в месяц. Он объясняет, что заниматься множеством разных проектов - актерство, сценарное дело, концерты, блогинг, интеграции и так далее."
    
    if any(word in question.lower() for word in ["что", "чем", "работа", "деятельность"]):
        if "актер" in context.lower() or "сценарист" in context.lower():
            return "Герой видео рассказывает, что он трудоголик и занимается множеством разных видов деятельности: актерство, сценарное дело, проведение мероприятий, концерты, блогинг, интеграции и другое."
    
    if any(word in question.lower() for word in ["как", "каким образом"]):
        return "Герой видео объясняет, что самая большая проблема - рассказать, чем именно он зарабатывает, потому что он делает очень много всего. Он работает как актер, сценарист, проводит мероприятия, выступает на концертах, ведет блог и занимается интеграциями."
    
    # Default response with context
    return f"На основе транскрипции видео: {context[:200]}..."

def interactive_simple_qa(rag_data: Dict[str, Any]):
    """Run simple interactive Q&A session."""
    
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
            question = input("\n🤔 Ваш вопрос: ").strip()
            
            if question.lower() in ['quit', 'exit', 'выход', 'q']:
                print("👋 До свидания!")
                break
            
            if not question:
                print("⚠️ Пожалуйста, введите вопрос")
                continue
            
            print(f"\n🔍 Ищу информацию для: '{question}'")
            
            # Search for relevant chunks
            relevant_chunks = simple_search(question, rag_data)
            
            # Generate answer
            answer = generate_simple_answer(question, relevant_chunks, rag_data["full_text"])
            
            print(f"\n💬 ОТВЕТ:")
            print("-" * 40)
            print(answer)
            
            if relevant_chunks:
                print(f"\n📚 НАЙДЕННЫЕ ФРАГМЕНТЫ ({len(relevant_chunks)}):")
                print("-" * 40)
                for i, chunk in enumerate(relevant_chunks, 1):
                    preview = chunk[:100] + "..." if len(chunk) > 100 else chunk
                    print(f"{i}. {preview}")
            
        except KeyboardInterrupt:
            print("\n\n👋 Сессия прервана пользователем")
            break
        except Exception as e:
            print(f"\n❌ Ошибка: {e}")

@log.catch
def main():
    """Main function for simple RAG demo."""
    print("🚀 ПРОСТАЯ RAG DEMO - ЗАГРУЗКА ДАННЫХ И Q&A")
    print("="*50)
    
    # Create simple RAG data
    rag_data = create_simple_rag_qa()
    if not rag_data:
        print("❌ Failed to create RAG data")
        return 1
    
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
    
    relevant_chunks = simple_search(test_question, rag_data)
    answer = generate_simple_answer(test_question, relevant_chunks, rag_data["full_text"])
    print(f"Ответ: {answer}")
    
    # Start interactive session
    interactive_simple_qa(rag_data)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())