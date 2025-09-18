# LLM RAG YouTube Audio Processing Project

## Project Goal
Build an end-to-end RAG pipeline for YouTube audio content processing with question-answering capabilities.

## Phase 1: Project Structure & Setup
- [ ] Create proper Python project structure (src/, tests/, docs/)
- [ ] Extract requirements from Pipeline_Demo.py 
- [ ] Create pyproject.toml with uv dependency management
- [ ] Set up virtual environment with uv
- [ ] Create .env.example for environment variables
- [ ] Configure ruff for linting and formatting
- [ ] Set up pytest for testing

## Phase 2: Modular Architecture
- [ ] Refactor Pipeline_Demo.py into modular components:
  - [ ] YouTube downloader module (yt_dlp integration)
  - [ ] Audio processing module (faster-whisper ASR)
  - [ ] Text processing module (normalization, chunking)  
  - [ ] Embedding module (sentence-transformers)
  - [ ] Vector storage module (ChromaDB)
  - [ ] RAG query module (OpenAI integration)

## Phase 3: Configuration & Data Management
- [ ] Create config management system
- [ ] Set up data directories structure
- [ ] Implement logging system
- [ ] Add error handling and validation
- [ ] Remove Google Colab dependencies

## Phase 4: API & Interface
- [ ] Create FastAPI web interface
- [ ] Implement REST API endpoints
- [ ] Add Gradio UI for demo
- [ ] Document API endpoints

## Phase 5: Testing & Quality
- [ ] Add unit tests for each module (pytest)
- [ ] Integration tests for full pipeline
- [ ] Performance testing with sample data
- [ ] Code quality checks (ruff linting/formatting)

## Phase 6: Documentation & Deployment
- [ ] Create comprehensive README
- [ ] API documentation
- [ ] Docker containerization
- [ ] Deployment guide

## Tech Stack (from Pipeline_Demo.py)
- **Package Manager**: uv
- **Testing**: pytest
- **Linting/Formatting**: ruff
- **ASR**: faster-whisper
- **Embeddings**: sentence-transformers (multilingual-e5-large-instruct)
- **Vector DB**: ChromaDB
- **LLM**: OpenAI GPT-4o
- **YouTube Download**: yt-dlp
- **Web Framework**: FastAPI (planned)
- **UI**: Gradio (planned)

## Reference Links
- [LLM Zoomcamp Project Requirements](https://github.com/DataTalksClub/llm-zoomcamp/blob/main/project.md)
- [2025 Cohort Specifics](https://github.com/DataTalksClub/llm-zoomcamp/blob/main/cohorts/2025/project.md)
- Pattern Reference: /Users/nk.myg/github/llm-zoomcamp

## Current Status
✅ Working prototype in Pipeline_Demo.py  
🔄 Need to create modular project structure