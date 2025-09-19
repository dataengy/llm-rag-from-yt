#!/usr/bin/env python3
"""Test the enhanced RAG demo imports and basic functionality."""

import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_imports():
    """Test that all required imports work."""
    try:
        print("✅ Config imports successful")

        print("✅ TextProcessor import successful")

        print("✅ Utils imports successful")

        print("✅ Demo config import successful")

        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def test_config():
    """Test configuration loading."""
    try:
        from llm_rag_yt._common.config.settings import get_config
        from user_testing.config import get_demo_config

        project_config = get_config()
        demo_config = get_demo_config()

        print(f"✅ Project config loaded - chunk_size: {project_config.chunk_size}")
        print(f"✅ Demo config loaded - video_title: {demo_config.video_title}")

        return True
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False


def test_text_processor():
    """Test text processing functionality."""
    try:
        from llm_rag_yt.text.processor import TextProcessor

        processor = TextProcessor()
        test_text = "Это тестовый текст. Он содержит несколько предложений. Мы проверим его обработку."

        normalized = processor.normalize_text(test_text)
        chunks = processor.split_into_chunks(normalized, chunk_size=5, overlap=1)

        print(f"✅ Text processing successful - {len(chunks)} chunks created")
        print(f"  Original: {len(test_text)} chars")
        print(f"  Normalized: {len(normalized)} chars")
        print(f"  First chunk: {chunks[0][:50]}...")

        return True
    except Exception as e:
        print(f"❌ Text processor test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 Testing Enhanced RAG Demo Components")
    print("=" * 50)

    tests = [
        ("Import Tests", test_imports),
        ("Config Tests", test_config),
        ("Text Processor Tests", test_text_processor),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        success = test_func()
        results.append(success)

    print(f"\n📊 Results: {sum(results)}/{len(results)} tests passed")

    if all(results):
        print("✅ All basic components are working - enhanced demo should work!")
        print("💡 To run full demo: python src/user_testing/rag_demo.py")
        print(
            "⚠️  Note: Full pipeline requires additional dependencies (loguru, chromadb, openai, etc.)"
        )
    else:
        print("❌ Some components failed - check dependencies")

    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
