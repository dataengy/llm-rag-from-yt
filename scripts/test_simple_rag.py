#!/usr/bin/env python3
"""Simple test script for philosophical podcast without ML dependencies."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_imports():
    """Test basic imports without ML dependencies."""
    print("🧪 Testing basic imports...")
    
    try:
        from llm_rag_yt._common.config.settings import get_config
        print("✅ Config loaded")
        
        config = get_config()
        print(f"✅ Config initialized: {config.openai_model}")
        
    except Exception as e:
        print(f"❌ Config error: {e}")
        return False
    
    try:
        from llm_rag_yt.text.processor import TextProcessor
        print("✅ Text processor available")
        
        processor = TextProcessor()
        test_text = "Это тестовый текст для проверки обработки."
        normalized = processor.normalize_text(test_text)
        print(f"✅ Text normalization works: '{normalized[:50]}...'")
        
    except Exception as e:
        print(f"❌ Text processor error: {e}")
        return False
    
    return True

def test_philosophical_data():
    """Test if we have philosophical podcast data."""
    print("\n🎭 Testing philosophical data...")
    
    audio_file = Path("data/audio/Философская беседа ｜ Юрий Вафин ｜ подкаст.mp3")
    if audio_file.exists():
        print(f"✅ Audio file found: {audio_file}")
        size_mb = audio_file.stat().st_size / 1024 / 1024
        print(f"📊 Size: {size_mb:.1f} MB")
        return True
    else:
        print(f"❌ Audio file not found: {audio_file}")
        
        # Check what's in the data directory
        data_dir = Path("data")
        if data_dir.exists():
            print("📁 Available data files:")
            for item in data_dir.rglob("*"):
                if item.is_file():
                    print(f"  - {item}")
        else:
            print("❌ Data directory not found")
        
        return False

def simple_qa_demo():
    """Run a simple Q&A demo without RAG."""
    print("\n💬 Simple Q&A Demo (without RAG)")
    print("=" * 50)
    
    # Mock some philosophical content
    philosophical_content = """
    В этой философской беседе Юрий Вафин обсуждает важные вопросы 
    бытия и смысла жизни. Разговор затрагивает темы о природе сознания,
    свободе воли и этических дилеммах современного общества.
    """
    
    questions = [
        "О чем говорит Юрий Вафин?",
        "Какие философские темы обсуждаются?",
        "Что говорится о смысле жизни?"
    ]
    
    print("📝 Демонстрационные вопросы:")
    for i, question in enumerate(questions, 1):
        print(f"\n{i}. {question}")
        # Simple keyword matching
        answer = "Извините, для полного ответа нужна обработанная RAG система."
        if "Юрий" in question or "говорит" in question:
            answer = "Юрий Вафин обсуждает философские вопросы бытия и смысла жизни."
        elif "темы" in question or "философские" in question:
            answer = "Обсуждаются темы сознания, свободы воли и этических дилемм."
        elif "смысл" in question:
            answer = "В беседе затрагивается тема смысла жизни в контексте современного общества."
        
        print(f"💡 Ответ: {answer}")

def main():
    """Main function."""
    print("🎭 Простой тест философской RAG системы")
    print("=" * 60)
    
    # Test 1: Basic imports
    if not test_imports():
        print("\n❌ Основные импорты не работают")
        return 1
    
    # Test 2: Check philosophical data
    data_available = test_philosophical_data()
    
    # Test 3: Simple demo
    simple_qa_demo()
    
    print("\n📋 Результаты тестирования:")
    print(f"  ✅ Базовые импорты: OK")
    print(f"  {'✅' if data_available else '❌'} Данные подкаста: {'OK' if data_available else 'Отсутствуют'}")
    print(f"  ✅ Простое Q&A: OK")
    
    if data_available:
        print("\n🚀 Готово к запуску полной RAG системы!")
        print("💡 Используйте: uv run python scripts/test_philosophical_rag.py")
    else:
        print("\n⚠️  Для полного тестирования нужен аудиофайл")
        print("📁 Поместите файл: data/audio/Философская беседа ｜ Юрий Вафин ｜ подкаст.mp3")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())