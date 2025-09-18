# CLAUDE.md - Project Configuration

## Project Standards
- Use descriptive variable names
- Follow Python PEP 8 conventions
- Use uv for package management
- Use pytest for testing
- Use ruff for linting and formatting

## Tech Stack
- **Package Manager**: uv
- **Testing**: pytest  
- **Linting/Formatting**: ruff
- **ASR**: faster-whisper
- **Embeddings**: sentence-transformers
- **Vector DB**: ChromaDB
- **LLM**: OpenAI GPT-4o
- **YouTube Download**: yt-dlp
- **Web Framework**: FastAPI
- **UI**: Gradio

## Common Commands
- `uv sync` - Install dependencies
- `uv run pytest` - Run tests
- `uv run ruff check .` - Lint code
- `uv run ruff format .` - Format code

## Frequently Used Prompts
1. "Create modular architecture from Pipeline_Demo.py"
2. "Set up pytest tests for the modules"
3. "Configure ruff linting rules"
4. "Extract requirements and create pyproject.toml"
5. "Refactor monolithic code into separate modules"