#!/usr/bin/env python3
"""Simple ChromaDB demo with basic embeddings."""

import os
import sys
import yaml
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

import chromadb
from loguru import logger as log

# Import common utilities
from utils import (
    setup_python_path, setup_logging, load_config, load_transcription_text,
    create_simple_chunks, print_session_header, print_section_header
)

# Setup Python path and logging
setup_python_path()
log_file = setup_logging('simple_chroma_demo')

def create_chroma_collection(config: dict, chunks: List[Dict[str, Any]]):
    """Create ChromaDB collection with basic embeddings."""
    
    log.info("Creating ChromaDB collection")
    print("🗄️ Creating ChromaDB collection...")
    
    # Setup ChromaDB
    chroma_path = Path(config['chroma_db']['path'])
    collection_name = config['chroma_db']['collection_name']
    
    log.debug(f"ChromaDB path: {chroma_path}")
    chroma_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize client
    client = chromadb.PersistentClient(path=str(chroma_path))
    
    # Create collection with default embedding function
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"description": "RAG demo collection"}
    )
    
    log.info(f"ChromaDB collection created: {collection_name}")
    print(f"✅ ChromaDB collection: {collection_name}")
    
    # Add chunks to collection
    log.info("Adding chunks to ChromaDB")
    print("💾 Storing chunks in ChromaDB...")
    
    chunk_ids = [chunk["id"] for chunk in chunks]
    documents = [chunk["text"] for chunk in chunks]
    metadatas = [chunk["metadata"] for chunk in chunks]
    
    collection.upsert(
        ids=chunk_ids,
        documents=documents,
        metadatas=metadatas
    )
    
    count = collection.count()
    log.info(f"Stored {count} chunks in ChromaDB")
    print(f"✅ Stored {count} chunks in ChromaDB")
    
    return {
        "client": client,
        "collection": collection,
        "path": chroma_path,
        "name": collection_name,
        "count": count
    }

def search_chroma(query: str, chroma_info: dict, top_k: int = 3) -> List[Dict[str, Any]]:
    """Search ChromaDB collection."""
    
    log.debug(f"Searching ChromaDB for: '{query}'")
    
    results = chroma_info["collection"].query(
        query_texts=[query],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )
    
    # Format results
    search_results = []
    for i in range(len(results["ids"][0])):
        result = {
            "id": results["ids"][0][i],
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i]
        }
        search_results.append(result)
    
    log.info(f"Found {len(search_results)} results for query: '{query}'")
    return search_results

def generate_answer(question: str, search_results: List[Dict[str, Any]]) -> str:
    """Generate answer from search results."""
    
    log.debug(f"Generating answer for: '{question}'")
    
    if not search_results:
        return "Извините, я не нашел релевантной информации для ответа на ваш вопрос."
    
    # Use best matching chunk
    best_match = search_results[0]
    context = best_match["text"]
    
    # Simple pattern matching
    if any(word in question.lower() for word in ["сколько", "зарабатывает", "деньги", "рублей"]):
        if "миллион" in context.lower():
            answer = "По словам героя видео, он зарабатывает больше миллиона рублей в месяц."
            log.info(f"Generated earnings answer")
            return answer
    
    if any(word in question.lower() for word in ["что", "чем", "работа"]):
        if "актер" in context.lower():
            answer = "Герой видео занимается актерством, сценарным делом и множеством других проектов."
            log.info(f"Generated work answer")
            return answer
    
    # Default context-based answer
    answer = f"На основе найденного фрагмента: {context[:150]}..."
    log.info(f"Generated context-based answer")
    return answer

def test_chroma_demo():
    """Test ChromaDB functionality."""
    
    print_session_header("SIMPLE CHROMADB DEMO")
    
    try:
        # Load config and data
        config = load_config()
        transcript_file = Path(config['data']['transcript_file'])
        transcript_text = load_transcription_text(transcript_file)
        
        # Create chunks
        chunk_size = config['text_processing']['chunk_size'] // 5  # Smaller chunks for better search
        chunks = create_simple_chunks(transcript_text, chunk_size)
        
        # Create ChromaDB collection
        chroma_info = create_chroma_collection(config, chunks)
        
        # Test questions
        test_questions = [
            "Сколько зарабатывает герой видео?",
            "Чем занимается герой?",
            "Что он говорит о работе?"
        ]
        
        print_section_header("TESTING SEMANTIC SEARCH")
        
        for i, question in enumerate(test_questions, 1):
            print(f"
{i}. Вопрос: {question}")
            
            # Search
            results = search_chroma(question, chroma_info, top_k=2)
            answer = generate_answer(question, results)
            
            print(f"   Ответ: {answer}")
            
            if results:
                print(f"   📊 Найдено: {len(results)} фрагментов")
                best_distance = results[0]["distance"]
                similarity = (1 - best_distance) * 100
                print(f"   🎯 Схожесть: {similarity:.1f}%")
        
        print(f"
✅ Demo completed!")
        print(f"📄 Логи: {log_file}")
        print(f"🗄️ ChromaDB: {chroma_info['path']}")
        
        return True
        
    except Exception as e:
        log.error(f"Demo failed: {e}")
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_chroma_demo()
    sys.exit(0 if success else 1)
