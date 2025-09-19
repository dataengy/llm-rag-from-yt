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

## Frequently Used Prompts (Updated 2025-01-19)
1. "Implement TODO.md" - Initial project setup request
2. "Create modular architecture from Pipeline_Demo.py"
3. "Set up pytest tests for the modules"
4. "Configure ruff linting rules"
5. "Extract requirements and create pyproject.toml"
6. "Move all docs under @docs/" - Documentation organization
7. "Update @.gitignore for python project" - Project configuration
8. "Implement @docs/TODO.md starting from evaluation criteria" - LLM Zoomcamp scoring implementation
9. "Update prompt logs, docs, todos, tests, reports and status. Then commit" - Documentation sync
10. "go on" - Continue with current task/development
11. "Run comprehensive tests" - Quality assurance workflow
12. "uv run llm-rag-yt evaluate" - Run evaluation suite
13. "uv run llm-rag-yt dashboard" - Generate monitoring dashboard
14. "python scripts/test_full_pipeline.py" - Full system test