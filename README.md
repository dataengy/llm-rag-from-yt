# LLM RAG YouTube Audio Processing

## Problem Statement

YouTube contains vast amounts of valuable audio content (podcasts, interviews, lectures, discussions) that are difficult to search and query efficiently. Users face several challenges:

1. **Content Discovery**: Finding specific information within hours of audio content is time-consuming
2. **Knowledge Extraction**: No easy way to ask questions about what was discussed in a video
3. **Multi-language Support**: Audio content in different languages lacks unified search capabilities
4. **Context Preservation**: Traditional transcription loses semantic meaning and context

This project solves these problems by building an end-to-end RAG (Retrieval-Augmented Generation) pipeline that:
- Automatically extracts and transcribes audio from YouTube videos
- Creates semantic embeddings for intelligent search and retrieval
- Enables natural language questioning of audio content
- Provides accurate, context-aware answers using state-of-the-art LLMs

The system transforms unstructured audio data into a queryable knowledge base, making YouTube's audio content as searchable as text documents.

## Features

- 🎵 **YouTube Audio Download**: Extract audio from YouTube videos using yt-dlp
- 🎙️ **Speech Recognition**: Transcribe audio using faster-whisper (Whisper ASR)
- 📝 **Text Processing**: Normalize and chunk transcriptions for optimal retrieval
- 🔍 **Semantic Search**: Create embeddings using sentence-transformers
- 💾 **Vector Storage**: Store and query embeddings with ChromaDB
- 🤖 **LLM Integration**: Generate answers using OpenAI GPT models
- 🌐 **Web API**: FastAPI server with REST endpoints
- 🎨 **Web UI**: Gradio interface for easy interaction
- ⌨️ **CLI**: Command-line interface for automation

## Quick Start

### Prerequisites

- Python 3.9+ (tested with Python 3.11)
- [uv](https://docs.astral.sh/uv/) package manager
- OpenAI API key
- FFmpeg (for audio processing)

### 1. Installation

```bash
# Clone repository
git clone https://github.com/dataengy/llm-rag-from-yt.git
cd llm-rag-from-yt

# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies (ML components included)
uv sync --extra ml

# Verify installation
uv run llm-rag-yt --help
```

### 2. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env file and add your OpenAI API key
# OPENAI_API_KEY=your_actual_api_key_here
```

### 3. Quick Test (using sample data)

```bash
# Process with fake ASR for quick testing
uv run llm-rag-yt process "https://youtube.com/watch?v=dQw4w9WgXcQ" --fake-asr

# Ask questions about the content
uv run llm-rag-yt query "What is this video about?"

# Check system status
uv run llm-rag-yt status
```

### 4. Full Pipeline Setup

```bash
# Process real YouTube video (requires OpenAI API key)
uv run llm-rag-yt process "https://youtube.com/watch?v=..." --language en

# Start web interface
uv run llm-rag-yt serve-ui  # UI at http://localhost:7860

# Start API server
uv run llm-rag-yt serve-api  # API at http://localhost:8000
```

### 5. Docker Setup (Alternative)

```bash
# Build and start all services
docker-compose up --build

# Access services:
# - UI: http://localhost:7860
# - API: http://localhost:8000
# - ChromaDB: http://localhost:8001
```

## Architecture

```
src/llm_rag_yt/
├── pipeline.py          # Main orchestrator
├── config/             
│   └── settings.py      # Configuration management
├── audio/
│   ├── downloader.py    # YouTube download (yt-dlp)
│   └── transcriber.py   # ASR (faster-whisper)
├── text/
│   └── processor.py     # Text normalization & chunking
├── embeddings/
│   └── encoder.py       # Sentence transformers
├── vectorstore/
│   └── chroma.py        # ChromaDB integration
├── rag/
│   └── query_engine.py  # OpenAI RAG queries
├── api/
│   ├── server.py        # FastAPI server
│   └── models.py        # Pydantic models
├── ui/
│   └── gradio_app.py    # Gradio interface
└── cli/
    └── main.py          # CLI commands
```

## Usage Examples

### CLI Commands

```bash
# Process multiple URLs
uv run llm-rag-yt process \
  "https://youtube.com/watch?v=url1" \
  "https://youtube.com/watch?v=url2" \
  --language en

# Interactive query mode
uv run llm-rag-yt query "Initial question" --interactive

# Check system status
uv run llm-rag-yt status
```

### API Usage

```python
import requests

# Process URLs
response = requests.post("http://localhost:8000/process", json={
    "urls": ["https://youtube.com/watch?v=..."],
    "use_fake_asr": True,
    "language": "ru"
})

# Query system
response = requests.post("http://localhost:8000/query", json={
    "question": "Your question here",
    "top_k": 3
})
```

### Python Library

```python
from llm_rag_yt.pipeline import RAGPipeline

# Initialize pipeline
pipeline = RAGPipeline()

# Process content
results = pipeline.download_and_process([
    "https://youtube.com/watch?v=..."
])

# Query system
answer = pipeline.query("Your question here")
print(answer["answer"])
```

## Advanced Features

### Evaluation & Optimization

```bash
# Run comprehensive evaluation of retrieval and LLM approaches
uv run llm-rag-yt evaluate

# Generate monitoring dashboard
uv run llm-rag-yt dashboard

# View ingestion pipeline status
uv run llm-rag-yt ingestion-status
```

### Automated Ingestion

```bash
# Add URLs to ingestion queue
uv run llm-rag-yt ingest-job "https://youtube.com/watch?v=url1" "https://youtube.com/watch?v=url2"

# Run all pending ingestion jobs
uv run llm-rag-yt run-ingestion --all
```

### Advanced Search Features

The system includes several advanced search capabilities:

- **Hybrid Search**: Combines semantic vector search with keyword matching
- **Query Rewriting**: Automatically generates query variants for better retrieval
- **Document Re-ranking**: Re-orders results using cross-encoder similarity
- **Multi-model Evaluation**: Compares different LLM models and prompts

## Development

```bash
# Install development dependencies
uv sync --extra dev

# Run tests
make test

# Lint and format
make lint
make format

# Run pre-commit checks
make pre-commit

# Run evaluation suite
uv run llm-rag-yt evaluate --output-dir ./evaluations
```

## Testing & Reproducibility

### Quick Test with Sample Data

```bash
# 1. Install dependencies
uv sync --extra ml

# 2. Set up environment
cp .env.example .env
# Add your OPENAI_API_KEY to .env

# 3. Test with fake ASR (no API key required for processing)
uv run llm-rag-yt process "https://youtube.com/watch?v=dQw4w9WgXcQ" --fake-asr

# 4. Query the system (requires OpenAI API key)
uv run llm-rag-yt query "What is this video about?"

# 5. Start web interface
uv run llm-rag-yt serve-ui
```

### Full Test with Real Data

The repository includes sample Russian audio content for testing:

```bash
# Process existing sample data
uv run llm-rag-yt process "https://youtube.com/watch?v=sample" --language ru

# Test various query types
uv run llm-rag-yt query "О чем говорят в видео?"
uv run llm-rag-yt query "Кто участвует в разговоре?"
uv run llm-rag-yt query "Какие основные темы обсуждаются?"
```

### Comprehensive System Test

```bash
# Run full system functionality test
python scripts/test_full_pipeline.py

# This test verifies:
# - Pipeline initialization
# - Evaluation systems (retrieval + LLM)
# - Monitoring and feedback collection
# - Automated ingestion pipeline
# - Advanced search features (hybrid, reranking, query rewriting)
```

## Configuration

The system uses a configuration class that can be customized:

```python
from llm_rag_yt.config.settings import Config

config = Config(
    chunk_size=300,
    chunk_overlap=75,
    openai_model="gpt-4",
    use_fake_asr=True  # For testing
)

pipeline = RAGPipeline(config)
```

## Tech Stack

- **Package Manager**: uv
- **Web Framework**: FastAPI
- **UI**: Gradio
- **CLI**: Typer
- **ASR**: faster-whisper
- **Embeddings**: sentence-transformers
- **Vector DB**: ChromaDB
- **LLM**: OpenAI GPT-4o
- **Audio Download**: yt-dlp
- **Testing**: pytest
- **Code Quality**: ruff

## Documentation

- [API Documentation](docs/API.md)
- [TODO](docs/TODO.md)
- [Test Report](docs/TEST-REPORT.md)
- [Prompts Log](docs/.PROMPTS-LOG.md)
- [Claude Status](docs/CLAUDE-curr-status.md)
- [Claude MD](docs/CLAUDE.md)
- [Claude Local](docs/CLAUDE.local.md)

## License

MIT License