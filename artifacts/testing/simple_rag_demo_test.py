#!/usr/bin/env python3
"""Non-interactive version of simple RAG demo for testing."""

import sys
from pathlib import Path

# Import common utilities
from utils import (
    setup_python_path, setup_logging, print_session_header, print_section_header
)

# Setup Python path and logging
setup_python_path()
log_file = setup_logging('simple_rag_demo_test')

def test_rag_demo():
    """Test the RAG demo without interactive session."""
    
    print_session_header("TESTING RAG DEMO COMPONENTS")
    
    # Import the main functions
    from simple_rag_demo import create_simple_rag_qa, simple_search, generate_simple_answer
    
    # Create RAG data
    print("1. Creating RAG data...")
    rag_data = create_simple_rag_qa()
    if not rag_data:
        print("❌ Failed to create RAG data")
        return False
    
    print(f"✅ RAG data created: {rag_data['metadata']['chunk_count']} chunks")
    
    # Test questions
    test_questions = [
        "Сколько зарабатывает герой видео?",
        "Чем занимается герой?", 
        "Как он зарабатывает деньги?"
    ]
    
    print_section_header("Testing Q&A")
    for i, question in enumerate(test_questions, 1):
        print(f"
{i}. Вопрос: {question}")
        
        # Search and answer
        relevant_chunks = simple_search(question, rag_data)
        answer = generate_simple_answer(question, relevant_chunks, rag_data["full_text"])
        
        print(f"   Ответ: {answer[:100]}...")
        print(f"   Найдено фрагментов: {len(relevant_chunks)}")
    
    print("
✅ All tests completed successfully!")
    return True

if __name__ == "__main__":
    success = test_rag_demo()
    sys.exit(0 if success else 1)
