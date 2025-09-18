#!/usr/bin/env python3
"""Complete RAG pipeline demo: load transcription data and create interactive Q&A."""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

def install_required_packages():
    """Install packages needed for RAG demo."""
    packages_to_check = [
        ("openai", "openai"),
        ("chromadb", "chromadb"), 
        ("sentence_transformers", "sentence-transformers"),
    ]
    
    missing_packages = []
    for import_name, pip_name in packages_to_check:
        try:
            __import__(import_name)
            print(f"✅ {import_name} available")
        except ImportError:
            missing_packages.append(pip_name)
    
    if missing_packages:
        print(f"📦 Installing missing packages: {missing_packages}")
        for package in missing_packages:
            result = os.system(f"pip install {package}")
            if result != 0:
                print(f"❌ Failed to install {package}")
                return False
        print("✅ All packages installed")
    
    return True

def load_transcription_data() -> List[Dict[str, Any]]:
    """Load transcription data from our test files."""
    
    # Load the real transcription we created
    transcript_file = Path("data/audio/В месяц ты зарабатываешь больше 1млн рублей？ Звезда ＂Реутов ТВ＂ у Дудя.real_transcript.txt")
    
    if not transcript_file.exists():
        print(f"❌ Transcript file not found: {transcript_file}")
        return []
    
    print(f"📖 Loading transcription: {transcript_file.name}")
    
    try:
        with transcript_file.open("r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # Parse the transcript format: [start-end] text
        documents = []
        metadata = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith("#"):
                # Parse metadata
                if "Language:" in line:
                    parts = line.split("Language:")
                    if len(parts) > 1:
                        lang_info = parts[1].split(",")[0].strip()
                        metadata["language"] = lang_info
                elif "Duration:" in line:
                    duration_part = line.split("Duration:")[1].split("s")[0].strip()
                    try:
                        metadata["duration"] = float(duration_part)
                    except:
                        pass
                continue
            
            if line.startswith("[") and "]" in line:
                # Parse timestamped segment: [start-end] text
                try:
                    timestamp_part = line.split("]")[0] + "]"
                    text_part = line.split("]", 1)[1].strip()
                    
                    # Extract start and end times
                    times = timestamp_part[1:-1]  # Remove brackets
                    start_str, end_str = times.split("-")
                    start_time = float(start_str)
                    end_time = float(end_str)
                    
                    if text_part:  # Only add non-empty segments
                        doc = {
                            "text": text_part,
                            "metadata": {
                                "source": "youtube_shorts",
                                "video_title": "В месяц ты зарабатываешь больше 1млн рублей？ Звезда ＂Реутов ТВ＂ у Дудя",
                                "start_time": start_time,
                                "end_time": end_time,
                                "duration": end_time - start_time,
                                "language": metadata.get("language", "ru"),
                                "segment_id": len(documents)
                            }
                        }
                        documents.append(doc)
                        
                except Exception as e:
                    print(f"⚠️ Failed to parse line: {line[:50]}... Error: {e}")
                    continue
        
        print(f"✅ Loaded {len(documents)} text segments")
        
        # Add full text as a single document as well
        if documents:
            full_text = " ".join([doc["text"] for doc in documents])
            full_doc = {
                "text": full_text,
                "metadata": {
                    "source": "youtube_shorts",
                    "video_title": "В месяц ты зарабатываешь больше 1млн рублей？ Звезда ＂Реутов ТВ＂ у Дудя",
                    "start_time": 0.0,
                    "end_time": metadata.get("duration", 44.8),
                    "duration": metadata.get("duration", 44.8),
                    "language": metadata.get("language", "ru"),
                    "segment_id": "full_text"
                }
            }
            documents.append(full_doc)
            print(f"✅ Added full text document ({len(full_text)} characters)")
        
        return documents
        
    except Exception as e:
        print(f"❌ Failed to load transcription: {e}")
        return []

def setup_rag_components():
    """Set up RAG components: embeddings, vector store, LLM."""
    
    print("🔧 Setting up RAG components...")
    
    # Initialize embeddings
    try:
        from sentence_transformers import SentenceTransformer
        print("📊 Loading embedding model...")
        embedding_model = SentenceTransformer('intfloat/multilingual-e5-large-instruct')
        print("✅ Embedding model loaded")
    except Exception as e:
        print(f"❌ Failed to load embedding model: {e}")
        return None, None, None
    
    # Initialize vector store
    try:
        import chromadb
        from chromadb.config import Settings
        
        print("🗄️ Setting up ChromaDB...")
        
        # Create client with persistent storage
        chroma_client = chromadb.PersistentClient(
            path=str(Path("data/chroma_db").absolute()),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        collection_name = "youtube_rag_demo"
        try:
            collection = chroma_client.get_collection(collection_name)
            print(f"✅ Using existing collection: {collection_name}")
        except:
            collection = chroma_client.create_collection(
                name=collection_name,
                metadata={"description": "YouTube RAG demo collection"}
            )
            print(f"✅ Created new collection: {collection_name}")
        
    except Exception as e:
        print(f"❌ Failed to setup ChromaDB: {e}")
        return None, None, None
    
    # Initialize OpenAI client
    try:
        import openai
        from dotenv import load_dotenv
        
        # Load environment variables
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            print("❌ OPENAI_API_KEY not found in environment")
            return None, None, None
        
        openai_client = openai.OpenAI(api_key=api_key)
        print("✅ OpenAI client initialized")
        
    except Exception as e:
        print(f"❌ Failed to setup OpenAI: {e}")
        return None, None, None
    
    return embedding_model, collection, openai_client

def load_documents_to_rag(documents: List[Dict[str, Any]], embedding_model, collection):
    """Load documents into RAG vector database."""
    
    if not documents:
        print("❌ No documents to load")
        return False
    
    print(f"📥 Loading {len(documents)} documents into RAG database...")
    
    try:
        # Check if collection already has documents
        existing_count = collection.count()
        if existing_count > 0:
            print(f"ℹ️ Collection already has {existing_count} documents")
            user_input = input("🤔 Clear existing data and reload? (y/n): ").lower().strip()
            if user_input == 'y':
                collection.delete(where={})
                print("🗑️ Cleared existing data")
            else:
                print("📚 Using existing data")
                return True
        
        # Prepare data for ChromaDB
        texts = []
        metadatas = []
        ids = []
        
        for i, doc in enumerate(documents):
            texts.append(doc["text"])
            metadatas.append(doc["metadata"])
            ids.append(f"doc_{i}")
        
        # Generate embeddings
        print("🔄 Generating embeddings...")
        embeddings = embedding_model.encode(texts, convert_to_tensor=False)
        embeddings_list = [emb.tolist() for emb in embeddings]
        
        # Add to collection
        print("💾 Adding documents to vector store...")
        collection.add(
            documents=texts,
            metadatas=metadatas,
            embeddings=embeddings_list,
            ids=ids
        )
        
        final_count = collection.count()
        print(f"✅ Successfully loaded {final_count} documents into RAG database")
        return True
        
    except Exception as e:
        print(f"❌ Failed to load documents: {e}")
        import traceback
        traceback.print_exc()
        return False

def query_rag(question: str, embedding_model, collection, openai_client, top_k: int = 3) -> Dict[str, Any]:
    """Query the RAG system with a question."""
    
    try:
        # Generate query embedding
        query_embedding = embedding_model.encode([question], convert_to_tensor=False)[0].tolist()
        
        # Search vector database
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        if not results["documents"][0]:
            return {
                "question": question,
                "answer": "Не найдено релевантных документов для ответа на вопрос.",
                "sources": []
            }
        
        # Prepare context from retrieved documents
        context_parts = []
        sources = []
        
        for i, (doc, metadata, distance) in enumerate(zip(
            results["documents"][0],
            results["metadatas"][0], 
            results["distances"][0]
        )):
            context_parts.append(f"[Сегмент {i+1}]: {doc}")
            
            source_info = {
                "segment_id": metadata.get("segment_id", i),
                "start_time": metadata.get("start_time", 0),
                "end_time": metadata.get("end_time", 0),
                "distance": distance,
                "text": doc[:100] + "..." if len(doc) > 100 else doc
            }
            sources.append(source_info)
        
        context = "\n\n".join(context_parts)
        
        # Generate answer using OpenAI
        system_prompt = """Ты помощник для ответов на вопросы на основе транскрипции видео с YouTube. 
Видео: "В месяц ты зарабатываешь больше 1млн рублей？ Звезда ＂Реутов ТВ＂ у Дудя"

Инструкции:
1. Отвечай на русском языке
2. Используй только информацию из предоставленного контекста
3. Если в контексте нет информации для ответа, так и скажи
4. Будь точным и конкретным
5. Ссылайся на конкретные моменты из видео когда это уместно"""

        user_prompt = f"""Контекст из видео:
{context}

Вопрос: {question}

Ответь на вопрос на основе предоставленного контекста."""

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        answer = response.choices[0].message.content
        
        return {
            "question": question,
            "answer": answer,
            "sources": sources,
            "context": context
        }
        
    except Exception as e:
        print(f"❌ Failed to query RAG: {e}")
        return {
            "question": question,
            "answer": f"Ошибка при обработке вопроса: {e}",
            "sources": []
        }

def interactive_qa_session(embedding_model, collection, openai_client):
    """Run interactive Q&A session."""
    
    print("\n" + "="*60)
    print("🤖 ИНТЕРАКТИВНАЯ СЕССИЯ ВОПРОСОВ И ОТВЕТОВ")
    print("="*60)
    print("📹 Видео: 'В месяц ты зарабатываешь больше 1млн рублей？ Звезда ＂Реутов ТВ＂ у Дудя'")
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
            
            print(f"\n🔍 Обрабатываю вопрос: '{question}'")
            print("⏳ Поиск релевантной информации...")
            
            result = query_rag(question, embedding_model, collection, openai_client)
            
            print(f"\n💬 ОТВЕТ:")
            print("-" * 40)
            print(result["answer"])
            
            if result["sources"]:
                print(f"\n📚 ИСТОЧНИКИ ({len(result['sources'])} сегментов):")
                print("-" * 40)
                for i, source in enumerate(result["sources"], 1):
                    start_time = source.get("start_time", 0)
                    end_time = source.get("end_time", 0)
                    print(f"{i}. [{start_time:.1f}s-{end_time:.1f}s]: {source['text']}")
            
        except KeyboardInterrupt:
            print("\n\n👋 Сессия прервана пользователем")
            break
        except Exception as e:
            print(f"\n❌ Ошибка: {e}")

def main():
    """Main RAG demo function."""
    print("🚀 RAG PIPELINE DEMO - ЗАГРУЗКА ДАННЫХ И ИНТЕРАКТИВНЫЙ Q&A")
    print("="*70)
    
    # Install required packages
    if not install_required_packages():
        return 1
    
    # Load transcription data
    documents = load_transcription_data()
    if not documents:
        return 1
    
    # Setup RAG components
    embedding_model, collection, openai_client = setup_rag_components()
    if not all([embedding_model, collection, openai_client]):
        return 1
    
    # Load documents into RAG
    if not load_documents_to_rag(documents, embedding_model, collection):
        return 1
    
    # Test the system with a sample query
    print("\n🧪 ТЕСТОВЫЙ ЗАПРОС")
    print("-" * 30)
    test_question = "Сколько зарабатывает герой видео?"
    print(f"Вопрос: {test_question}")
    
    test_result = query_rag(test_question, embedding_model, collection, openai_client)
    print(f"Ответ: {test_result['answer']}")
    
    # Start interactive session
    interactive_qa_session(embedding_model, collection, openai_client)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())