#!/usr/bin/env python3
"""Interactive test script for philosophical podcast RAG system."""

import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from llm_rag_yt.pipeline import RAGPipeline
from llm_rag_yt.monitoring.feedback_collector import FeedbackCollector
from llm_rag_yt.search.hybrid_search import HybridSearchEngine
from llm_rag_yt.search.query_rewriter import QueryRewriter


class PhilosophicalRAGTester:
    """Interactive tester for philosophical podcast content."""

    def __init__(self):
        """Initialize the tester."""
        self.audio_file = "data/audio/Философская беседа ｜ Юрий Вафин ｜ подкаст.mp3"
        self.pipeline = None
        self.feedback_collector = None
        self.hybrid_search = None
        self.query_rewriter = None
        
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

    def setup_system(self) -> bool:
        """Set up the RAG system."""
        print("🔧 Настройка системы RAG...")
        
        try:
            # Initialize pipeline
            self.pipeline = RAGPipeline()
            print("✅ Пайплайн RAG инициализирован")
            
            # Initialize feedback collector
            feedback_db = self.pipeline.config.artifacts_dir / "philosophical_feedback.db"
            self.feedback_collector = FeedbackCollector(feedback_db)
            print("✅ Система обратной связи готова")
            
            # Initialize advanced search components
            self.hybrid_search = HybridSearchEngine(self.pipeline.vector_store, self.pipeline.encoder)
            print("✅ Гибридный поиск готов")
            
            if os.getenv("OPENAI_API_KEY"):
                self.query_rewriter = QueryRewriter()
                print("✅ Переписчик запросов готов")
            else:
                print("⚠️ Переписчик запросов недоступен (нет OpenAI API ключа)")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка настройки системы: {e}")
            return False

    def check_audio_file(self) -> bool:
        """Check if the audio file exists."""
        audio_path = Path(self.audio_file)
        if audio_path.exists():
            print(f"✅ Аудиофайл найден: {self.audio_file}")
            print(f"📊 Размер файла: {audio_path.stat().st_size / 1024 / 1024:.1f} МБ")
            return True
        else:
            print(f"❌ Аудиофайл не найден: {self.audio_file}")
            return False

    def process_audio_if_needed(self) -> bool:
        """Process audio file if not already processed."""
        print("\n🎵 Проверка обработки аудиофайла...")
        
        # Check if we have any data in vector store
        collection_info = self.pipeline.vector_store.get_collection_info()
        if collection_info["count"] > 0:
            print(f"✅ Найдены данные в базе векторов: {collection_info['count']} документов")
            return True
        
        print("🔄 Обработка аудиофайла (это может занять несколько минут)...")
        
        try:
            # Use fake ASR for testing (faster)
            results = self.pipeline.download_and_process([f"file://{Path(self.audio_file).absolute()}"])
            
            if results and results.get("chunks", 0) > 0:
                print(f"✅ Аудиофайл обработан: {results['chunks']} фрагментов создано")
                return True
            else:
                print("❌ Не удалось обработать аудиофайл")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка обработки аудиофайла: {e}")
            return False

    def display_test_questions(self):
        """Display predefined test questions."""
        print("\n📝 Готовые тестовые вопросы:")
        print("=" * 60)
        
        for category, questions in self.test_questions.items():
            print(f"\n🔹 {category}:")
            for i, question in enumerate(questions, 1):
                print(f"   {i}. {question}")
        
        print("\n" + "=" * 60)

    def query_with_timing(self, question: str, search_method: str = "standard") -> Dict[str, Any]:
        """Execute query with timing and method selection."""
        print(f"\n🔍 Запрос ({search_method}): {question}")
        start_time = time.time()
        
        try:
            if search_method == "hybrid" and self.hybrid_search:
                # Use hybrid search
                docs = self.hybrid_search.search(question, top_k=3)
                # Create mock answer for hybrid search
                context = "\n".join(f"{i+1}. {doc['text']}" for i, doc in enumerate(docs))
                result = {
                    "question": question,
                    "answer": f"[Гибридный поиск] Найдено {len(docs)} релевантных фрагментов",
                    "sources": docs,
                    "context": context,
                    "search_method": "hybrid"
                }
            elif search_method == "rewritten" and self.query_rewriter:
                # Use query rewriting
                rewrite_result = self.query_rewriter.rewrite_query(question)
                print(f"   📝 Перефразированные запросы: {len(rewrite_result['rewritten_queries'])}")
                # Use first rewritten query or original
                query_to_use = rewrite_result['rewritten_queries'][0] if rewrite_result['rewritten_queries'] else question
                result = self.pipeline.query(query_to_use)
                result["original_query"] = question
                result["rewritten_query"] = query_to_use
                result["search_method"] = "rewritten"
            else:
                # Standard RAG query
                result = self.pipeline.query(question)
                result["search_method"] = "standard"
            
            end_time = time.time()
            response_time = end_time - start_time
            result["response_time"] = response_time
            
            return result
            
        except Exception as e:
            print(f"❌ Ошибка выполнения запроса: {e}")
            return {
                "question": question,
                "answer": f"Ошибка: {str(e)}",
                "sources": [],
                "response_time": time.time() - start_time,
                "search_method": search_method
            }

    def display_result(self, result: Dict[str, Any]):
        """Display query result with formatting."""
        print(f"\n💡 Ответ ({result.get('search_method', 'unknown')}):")
        print("-" * 50)
        print(result["answer"])
        
        print(f"\n⏱️ Время ответа: {result.get('response_time', 0):.2f} сек")
        
        sources = result.get("sources", [])
        if sources:
            print(f"\n📚 Источники ({len(sources)}):")
            for i, source in enumerate(sources[:3], 1):
                distance = source.get("distance", 0)
                similarity = 1 - distance if distance else 0
                print(f"   {i}. Релевантность: {similarity:.3f}")
                print(f"      {source.get('text', '')[:100]}...")
        
        # Show rewritten query if available
        if "rewritten_query" in result and result["rewritten_query"] != result["question"]:
            print(f"\n📝 Перефразированный запрос: {result['rewritten_query']}")

    def collect_feedback(self, result: Dict[str, Any]) -> bool:
        """Collect user feedback for the result."""
        try:
            print("\n📊 Оценка ответа:")
            print("1 - Очень плохо, 2 - Плохо, 3 - Нормально, 4 - Хорошо, 5 - Отлично")
            
            while True:
                try:
                    rating = int(input("Ваша оценка (1-5): "))
                    if 1 <= rating <= 5:
                        break
                    else:
                        print("Пожалуйста, введите число от 1 до 5")
                except ValueError:
                    print("Пожалуйста, введите корректное число")
            
            feedback_text = input("Комментарий (необязательно): ").strip()
            
            # Collect feedback
            feedback_id = self.feedback_collector.collect_feedback(
                query=result["question"],
                answer=result["answer"],
                rating=rating,
                feedback_text=feedback_text if feedback_text else None,
                response_time=result.get("response_time"),
                sources_count=len(result.get("sources", []))
            )
            
            print(f"✅ Обратная связь сохранена (ID: {feedback_id})")
            return True
            
        except KeyboardInterrupt:
            print("\n⚠️ Сбор обратной связи пропущен")
            return False
        except Exception as e:
            print(f"❌ Ошибка сбора обратной связи: {e}")
            return False

    def run_predefined_tests(self):
        """Run predefined test questions."""
        print("\n🧪 Запуск предопределенных тестов...")
        
        for category, questions in self.test_questions.items():
            print(f"\n📝 Тестирование категории: {category}")
            print("=" * 50)
            
            # Test first question from each category
            question = questions[0]
            result = self.query_with_timing(question)
            self.display_result(result)
            
            # Optional feedback
            feedback_input = input("\nСобрать обратную связь? (y/n): ").strip().lower()
            if feedback_input == 'y':
                self.collect_feedback(result)

    def interactive_session(self):
        """Run interactive user session."""
        print("\n🎯 Интерактивная сессия запросов")
        print("=" * 50)
        print("Введите ваши вопросы о философской беседе.")
        print("Команды:")
        print("  'test' - показать готовые вопросы")
        print("  'hybrid' - использовать гибридный поиск")
        print("  'rewrite' - использовать переписывание запросов")
        print("  'stats' - показать статистику")
        print("  'exit' - выход")
        print("=" * 50)
        
        while True:
            try:
                user_input = input("\n💬 Ваш вопрос: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() == 'exit':
                    break
                elif user_input.lower() == 'test':
                    self.display_test_questions()
                    continue
                elif user_input.lower() == 'stats':
                    self.show_feedback_stats()
                    continue
                
                # Determine search method
                search_method = "standard"
                if user_input.lower().startswith('hybrid:'):
                    search_method = "hybrid"
                    user_input = user_input[7:].strip()
                elif user_input.lower().startswith('rewrite:'):
                    search_method = "rewritten"
                    user_input = user_input[8:].strip()
                
                if not user_input:
                    print("❌ Пустой запрос")
                    continue
                
                # Execute query
                result = self.query_with_timing(user_input, search_method)
                self.display_result(result)
                
                # Ask for feedback
                feedback_input = input("\nОценить ответ? (y/n): ").strip().lower()
                if feedback_input == 'y':
                    self.collect_feedback(result)
                
            except KeyboardInterrupt:
                print("\n\n👋 До свидания!")
                break
            except Exception as e:
                print(f"❌ Ошибка: {e}")

    def show_feedback_stats(self):
        """Show feedback statistics."""
        try:
            stats = self.feedback_collector.get_feedback_stats()
            print("\n📊 Статистика обратной связи:")
            print("-" * 30)
            print(f"Всего отзывов: {stats['total_feedback']}")
            print(f"Средняя оценка: {stats['average_rating']:.2f}/5")
            print(f"Среднее время ответа: {stats['average_response_time']:.2f} сек")
            
            if stats['rating_distribution']:
                print("\nРаспределение оценок:")
                for rating, count in sorted(stats['rating_distribution'].items()):
                    print(f"  {rating} звезд: {count}")
                    
        except Exception as e:
            print(f"❌ Ошибка получения статистики: {e}")

    def run(self):
        """Run the complete testing session."""
        print("🎭 Тестирование RAG системы для философской беседы")
        print("=" * 60)
        
        # Step 1: Check audio file
        if not self.check_audio_file():
            return False
        
        # Step 2: Setup system
        if not self.setup_system():
            return False
        
        # Step 3: Process audio if needed
        if not self.process_audio_if_needed():
            return False
        
        # Step 4: Show system status
        collection_info = self.pipeline.vector_store.get_collection_info()
        print(f"\n✅ Система готова!")
        print(f"📊 Документов в базе: {collection_info['count']}")
        print(f"🎯 Режимы поиска: стандартный, гибридный, с переписыванием")
        
        # Step 5: Choose test mode
        print("\n🎮 Выберите режим тестирования:")
        print("1. Предопределенные тесты")
        print("2. Интерактивная сессия") 
        print("3. Оба режима")
        
        try:
            choice = input("Ваш выбор (1/2/3): ").strip()
            
            if choice == "1":
                self.run_predefined_tests()
            elif choice == "2":
                self.interactive_session()
            elif choice == "3":
                self.run_predefined_tests()
                print("\n" + "="*60)
                self.interactive_session()
            else:
                print("❌ Неверный выбор, запуск интерактивной сессии по умолчанию")
                self.interactive_session()
        
        except KeyboardInterrupt:
            print("\n\n👋 Тестирование прервано пользователем")
        
        # Final stats
        self.show_feedback_stats()
        print("\n🎉 Тестирование завершено!")
        return True


def main():
    """Main function."""
    tester = PhilosophicalRAGTester()
    success = tester.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()