#!/usr/bin/env python3
"""
Manual test script for the RAG API with YouTube Shorts URL
Test URL: https://www.youtube.com/shorts/pNOrDC8NyEo

Usage:
1. First start the API server:
   python -m llm_rag_yt.cli.main serve-api

2. Then run this test:
   python manual_test_api.py

Or run with server auto-start:
   python manual_test_api.py --start-server
"""

import requests
import json
import time
import subprocess
import threading
import argparse
from typing import Dict, Any


class APITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_health(self) -> Dict[str, Any]:
        """Test the health endpoint."""
        print("🔍 Testing health endpoint...")
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            result = response.json()
            print(f"✅ Health check passed: {result['status']}")
            return result
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return {"error": str(e)}
    
    def test_status(self) -> Dict[str, Any]:
        """Test the status endpoint."""
        print("🔍 Testing status endpoint...")
        try:
            response = self.session.get(f"{self.base_url}/status")
            response.raise_for_status()
            result = response.json()
            print(f"✅ Status check passed: {result['pipeline_status']}")
            return result
        except Exception as e:
            print(f"❌ Status check failed: {e}")
            return {"error": str(e)}
    
    def test_process_url(self, url: str, use_fake_asr: bool = False) -> Dict[str, Any]:
        """Test processing a YouTube URL."""
        print(f"🔍 Testing URL processing: {url}")
        
        payload = {
            "urls": [url],
            "use_fake_asr": use_fake_asr,
            "language": "en"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/process",
                json=payload,
                timeout=300  # 5 minutes timeout for processing
            )
            response.raise_for_status()
            result = response.json()
            print(f"✅ URL processing completed: {result['message']}")
            print(f"   Transcriptions: {result['transcriptions_count']}")
            print(f"   Chunks: {result['chunks_count']}")
            return result
        except Exception as e:
            print(f"❌ URL processing failed: {e}")
            return {"error": str(e)}
    
    def test_query(self, question: str, top_k: int = 3) -> Dict[str, Any]:
        """Test querying the RAG system."""
        print(f"🔍 Testing query: {question}")
        
        payload = {
            "question": question,
            "top_k": top_k
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/query",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            print(f"✅ Query completed successfully")
            print(f"   Answer length: {len(result['answer'])} characters")
            print(f"   Sources found: {len(result['sources'])}")
            return result
        except Exception as e:
            print(f"❌ Query failed: {e}")
            return {"error": str(e)}
    
    def test_feedback(self, query: str, answer: str, rating: int = 5) -> Dict[str, Any]:
        """Test submitting feedback."""
        print("🔍 Testing feedback submission...")
        
        payload = {
            "query": query,
            "answer": answer,
            "rating": rating,
            "feedback_text": "Test feedback from manual testing",
            "session_id": "manual_test_session"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/feedback",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            print(f"✅ Feedback submitted: {result['feedback_id']}")
            return result
        except Exception as e:
            print(f"❌ Feedback submission failed: {e}")
            return {"error": str(e)}


def wait_for_server(base_url: str, timeout: int = 30) -> bool:
    """Wait for server to be ready."""
    print(f"⏳ Waiting for server at {base_url} to be ready...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Server is ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(2)
    
    print(f"❌ Server not ready after {timeout} seconds")
    return False


def start_server():
    """Start the FastAPI server in background."""
    print("🚀 Starting API server...")
    process = subprocess.Popen(
        ["python", "-m", "llm_rag_yt.cli.main", "serve-api"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return process


def run_tests():
    """Run the actual API tests."""
    # Test URL from user request
    test_url = "https://www.youtube.com/shorts/pNOrDC8NyEo"
    
    tester = APITester()
    
    # Test 1: Health check
    print("\n1. Health Check")
    print("-" * 20)
    health_result = tester.test_health()
    
    if "error" in health_result:
        print("❌ Cannot proceed with tests - server not healthy")
        return
    
    # Test 2: Status check
    print("\n2. Status Check")
    print("-" * 20)
    status_result = tester.test_status()
    
    # Test 3: Process URL (with fake ASR for faster testing)
    print("\n3. Process YouTube Shorts URL")
    print("-" * 30)
    print(f"Processing: {test_url}")

    # print("⚠️  Using fake ASR for faster testing")
    # process_result = tester.test_process_url(test_url, use_fake_asr=True)
    print("⚠️  Using real ASR!")
    process_result = tester.test_process_url(test_url, use_fake_asr=False)

    # Test 4: Query the processed content
    if "error" not in process_result:
        print("\n4. Query Processed Content")
        print("-" * 25)
        test_questions = [
            "What is this video about?",
            "Summarize the main points of the content",
            "What are the key takeaways?"
        ]
        
        for question in test_questions:
            query_result = tester.test_query(question)
            if "error" not in query_result:
                print(f"   Q: {question}")
                print(f"   A: {query_result['answer'][:100]}...")
                print()
                
                # Test 5: Submit feedback for the first query
                if question == test_questions[0]:
                    print("5. Submit Feedback")
                    print("-" * 15)
                    tester.test_feedback(question, query_result['answer'])
    else:
        print("⚠️  Skipping query tests due to processing failure")
    
    # Test 6: Get feedback stats
    print("\n6. Feedback Statistics")
    print("-" * 20)
    try:
        response = tester.session.get(f"{tester.base_url}/feedback/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Feedback stats: {json.dumps(stats, indent=2)}")
        else:
            print(f"❌ Failed to get feedback stats: {response.status_code}")
    except Exception as e:
        print(f"❌ Failed to get feedback stats: {e}")


def main():
    """Run manual tests for the API."""
    parser = argparse.ArgumentParser(description="Manual API testing script")
    parser.add_argument(
        "--start-server", 
        action="store_true", 
        help="Start the API server automatically"
    )
    parser.add_argument(
        "--server-timeout", 
        type=int, 
        default=60, 
        help="Timeout for server startup (seconds)"
    )
    
    args = parser.parse_args()
    
    print("🚀 Starting manual API tests for YouTube Shorts URL")
    print("=" * 60)
    print(f"Test URL: https://www.youtube.com/shorts/pNOrDC8NyEo")
    
    server_process = None
    
    try:
        if args.start_server:
            server_process = start_server()
            
            if not wait_for_server("http://localhost:8000", args.server_timeout):
                print("❌ Failed to start server")
                return
        else:
            print("🔗 Connecting to existing server at http://localhost:8000")
            print("💡 If no server is running, start it with:")
            print("   python -m llm_rag_yt.cli.main serve-api")
            print("   or run this script with --start-server flag")
        
        run_tests()
        
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    
    finally:
        if server_process:
            print("\n🛑 Stopping server...")
            server_process.terminate()
            server_process.wait()
        
        print("\n" + "=" * 60)
        print("🏁 Manual API testing completed!")


if __name__ == "__main__":
    main()