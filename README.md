# LLM RAG YouTube Audio Processing

End-to-end RAG pipeline for processing YouTube audio content and answering questions.

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

### 1. Installation

```bash
# Clone repository
git clone <repository-url>
cd llm-rag-from-yt

# Install with uv
uv sync

# Or install ML dependencies for full functionality
uv sync --extra ml
```

### 2. Environment Setup

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 3. Run the Pipeline

```bash
# Process YouTube video
uv run llm-rag-yt process "https://youtube.com/watch?v=..." --fake-asr

# Ask questions
uv run llm-rag-yt query "Your question here"

# Start web UI
uv run llm-rag-yt serve-ui

# Start API server
uv run llm-rag-yt serve-api
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

## Development

```bash
# Install development dependencies
uv sync

# Run tests
make test

# Lint and format
make lint
make format

# Run pre-commit checks
make pre-commit
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