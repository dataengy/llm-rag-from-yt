#!/usr/bin/env python3
"""Demo test script for philosophical podcast with fallback capabilities."""

import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

class PhilosophicalRAGDemo:
    """Demo tester for philosophical podcast content with fallback mode."""

    def __init__(self):
        """Initialize the demo."""
        self.audio_file = "data/audio/Философская беседа ｜ Юрий Вафин ｜ подкаст.mp3"
        
        # Predefined test questions
        self.test_questions = {
            "Основные темы": [
                "О чем говорят в этой философской беседе?",
                "Какие главные темы обсуждаются в подкасте?",
                "Что является центральной идеей разговора?",
                "Какие вопросы поднимаются в беседе?"
            ],
            "Участники и мнения": [
                "Кто участвует в беседе?",
                "Какую позицию занимает Юрий Вафин?",
                "Какие разные точки зрения представлены?",
                "Как участники относятся к обсуждаемым вопросам?"
            ],
            "Философские концепции": [
                "Какие философские концепции упоминаются?",
                "Как участники определяют ключевые понятия?",
                "Какие примеры приводятся для объяснения идей?",
                "Какие философские школы или направления обсуждаются?"
            ],
            "Практические выводы": [
                "Какие практические советы даются?",
                "К каким выводам приходят участники?",
                "Как можно применить обсуждаемые идеи?",
                "Что рекомендуют участники слушателям?"
            ]
        }

    def check_environment(self) -> Dict[str, bool]:
        """Check the current environment setup."""
        print("🔍 Проверка окружения...")
        
        status = {
            "audio_file": False,
            "config": False,
            "openai_key": False,
            "ml_deps": False
        }
        
        # Check audio file
        audio_path = Path(self.audio_file)
        if audio_path.exists():
            print(f"✅ Аудиофайл найден: {audio_path.name}")
            print(f"📊 Размер: {audio_path.stat().st_size / 1024 / 1024:.1f} МБ")
            status["audio_file"] = True
        else:
            print(f"❌ Аудиофайл не найден: {self.audio_file}")
        
        # Check basic config
        try:
            from llm_rag_yt.config.settings import get_config
            config = get_config()
            print(f"✅ Конфигурация загружена")
            print(f"   Модель ИИ: {config.openai_model}")
            print(f"   Размер чанка: {config.chunk_size}")
            status["config"] = True
        except Exception as e:
            print(f"❌ Ошибка конфигурации: {e}")
        
        # Check OpenAI API key
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key and openai_key != "your_openai_api_key_here":
            print("✅ OpenAI API ключ настроен")
            status["openai_key"] = True
        else:
            print("⚠️  OpenAI API ключ не настроен")
            print("💡 Установите OPENAI_API_KEY в файле .env")
        
        # Check ML dependencies
        try:
            from llm_rag_yt.embeddings.encoder import SENTENCE_TRANSFORMERS_AVAILABLE
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                print("✅ ML зависимости доступны")
                status["ml_deps"] = True
            else:
                print("⚠️  ML зависимости недоступны (fallback режим)")
        except Exception as e:
            print(f"❌ Ошибка ML зависимостей: {e}")
        
        return status

    def demo_rag_setup(self, status: Dict[str, bool]) -> bool:
        """Demonstrate RAG system setup."""
        print("\n🔧 Демонстрация настройки RAG системы...")
        
        if not status["config"]:
            print("❌ Невозможно продолжить без базовой конфигурации")
            return False
        
        try:
            # Test text processing
            from llm_rag_yt.text.processor import TextProcessor
            
            processor = TextProcessor()
            sample_text = """
            В философской беседе Юрий Вафин размышляет о природе человеческого существования.
            Обсуждаются вопросы свободы воли, смысла жизни и этических дилемм современности.
            Участники беседы приходят к выводу о важности рефлексии и самопознания.
            """
            
            print("📝 Тестирование обработки текста...")
            normalized = processor.normalize_text(sample_text)
            chunks = processor.split_into_chunks(normalized, chunk_size=50, overlap=10)
            
            print(f"✅ Создано {len(chunks)} текстовых фрагментов")
            print(f"   Пример фрагмента: '{chunks[0][:60]}...'")
            
            # Test vector storage (without embeddings)
            print("\n💾 Тестирование векторного хранилища...")
            from llm_rag_yt.vectorstore.chroma import ChromaVectorStore
            
            vector_store = ChromaVectorStore()
            collection_info = vector_store.get_collection_info()
            print(f"✅ ChromaDB подключен: {collection_info['name']}")
            print(f"   Документов в коллекции: {collection_info['count']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка настройки RAG: {e}")
            return False

    def demo_questions(self):
        """Demonstrate question answering capabilities."""
        print("\n💬 Демонстрация системы вопросов и ответов")
        print("=" * 60)
        
        # Show predefined questions
        print("📝 Готовые тестовые вопросы:")
        for category, questions in self.test_questions.items():
            print(f"\n🔹 {category}:")
            for i, question in enumerate(questions, 1):
                print(f"   {i}. {question}")
        
        print("\n🎯 Интерактивный режим:")
        print("Введите номер вопроса или свой собственный вопрос")
        print("Команды: 'demo' - демо ответы, 'exit' - выход")
        
        while True:
            try:
                user_input = input("\n💬 Ваш вопрос: ").strip()
                
                if not user_input:
                    continue
                    
                if user_input.lower() == 'exit':
                    break
                elif user_input.lower() == 'demo':
                    self.show_demo_answers()
                    continue
                
                # Simple demo responses
                start_time = time.time()
                answer = self.generate_demo_answer(user_input)
                response_time = time.time() - start_time
                
                print(f"\n💡 Демо ответ (время: {response_time:.2f}с):")
                print("-" * 40)
                print(answer)
                print("\n📚 Источники: [демо-режим, реальные источники недоступны]")
                
            except KeyboardInterrupt:
                print("\n\n👋 До свидания!")
                break
            except Exception as e:
                print(f"❌ Ошибка: {e}")

    def show_demo_answers(self):
        """Show demo answers for predefined questions."""
        demo_answers = {
            "О чем говорят в этой философской беседе?": 
                "В беседе обсуждаются фундаментальные вопросы человеческого существования, включая природу сознания, свободу воли и поиск смысла жизни.",
            
            "Какие философские концепции упоминаются?":
                "Рассматриваются концепции экзистенциализма, этики добродетели, проблемы детерминизма и вопросы о природе морального выбора.",
            
            "Какие практические советы даются?":
                "Участники подчеркивают важность саморефлексии, критического мышления и осознанного подхода к жизненным решениям."
        }
        
        print("\n🎭 Демонстрационные ответы:")
        for question, answer in demo_answers.items():
            print(f"\n❓ {question}")
            print(f"💡 {answer}")

    def generate_demo_answer(self, question: str) -> str:
        """Generate a demo answer for any question."""
        # Simple keyword-based responses
        question_lower = question.lower()
        
        if any(word in question_lower for word in ["юрий", "вафин", "участник"]):
            return "Юрий Вафин выступает как основной участник беседы, представляя различные философские перспективы и ведя диалог о важных экзистенциальных вопросах."
        
        elif any(word in question_lower for word in ["философия", "концепция", "идея"]):
            return "В беседе затрагиваются ключевые философские концепции современности, включая вопросы сознания, свободы воли и этических дилемм."
        
        elif any(word in question_lower for word in ["смысл", "жизнь", "существование"]):
            return "Обсуждается поиск смысла в современном мире, важность самопознания и роль философской рефлексии в повседневной жизни."
        
        elif any(word in question_lower for word in ["практика", "применение", "совет"]):
            return "Даются практические рекомендации по развитию критического мышления, осознанности и этического подхода к жизненным решениям."
        
        else:
            return f"Интересный вопрос о '{question}'. В контексте философской беседы это связано с общими темами самопознания, этики и поиска истины."

    def show_setup_instructions(self):
        """Show setup instructions for full functionality."""
        print("\n📋 ИНСТРУКЦИИ ПО НАСТРОЙКЕ")
        print("=" * 50)
        print("Для полной функциональности RAG системы:")
        print()
        print("1. 🔑 Настройте OpenAI API ключ:")
        print("   export OPENAI_API_KEY=your_actual_api_key")
        print("   # или отредактируйте файл .env")
        print()
        print("2. 🧠 Установите ML зависимости (опционально):")
        print("   uv sync --extra ml")
        print()
        print("3. 🚀 Запустите полный тест:")
        print("   uv run python scripts/test_philosophical_rag.py")

    def run(self):
        """Run the complete demo."""
        print("🎭 Демо RAG системы для философской беседы")
        print("=" * 60)
        
        # Check environment
        status = self.check_environment()
        
        # Demo RAG setup
        rag_ready = self.demo_rag_setup(status)
        
        # Show capabilities
        print(f"\n✅ Статус системы:")
        print(f"  🎵 Аудиофайл: {'✅' if status['audio_file'] else '❌'}")
        print(f"  ⚙️  Конфигурация: {'✅' if status['config'] else '❌'}")
        print(f"  🔑 OpenAI ключ: {'✅' if status['openai_key'] else '⚠️'}")
        print(f"  🧠 ML зависимости: {'✅' if status['ml_deps'] else '⚠️'}")
        print(f"  🔧 RAG готовность: {'✅' if rag_ready else '❌'}")
        
        if rag_ready:
            print("\n🎯 Система готова к демонстрации!")
            
            # Ask user what to do
            print("\nВыберите режим:")
            print("1. Демо вопросы и ответы")
            print("2. Показать инструкции по настройке")
            print("3. Выход")
            
            try:
                choice = input("\nВаш выбор (1/2/3): ").strip()
                
                if choice == "1":
                    self.demo_questions()
                elif choice == "2":
                    self.show_setup_instructions()
                elif choice == "3":
                    print("👋 До свидания!")
                else:
                    print("❌ Неверный выбор")
                    self.show_setup_instructions()
                    
            except KeyboardInterrupt:
                print("\n👋 До свидания!")
        
        else:
            print("\n⚠️  Система не готова к полной демонстрации")
            self.show_setup_instructions()
        
        return True

def main():
    """Main function."""
    demo = PhilosophicalRAGDemo()
    success = demo.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()