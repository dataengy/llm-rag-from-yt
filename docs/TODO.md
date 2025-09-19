# LLM RAG YouTube Audio Processing Project

## Achive next Evaluation Criteria with maximum points
- choose next tools for stack: Dagster, 
* Problem description
    * 0 points: The problem is not described
    * 1 point: The problem is described but briefly or unclearly
    * 2 points: The problem is well-described and it's clear what problem the project solves
* Retrieval flow
    * 0 points: No knowledge base or LLM is used
    * 1 point: No knowledge base is used, and the LLM is queried directly
    * 2 points: Both a knowledge base and an LLM are used in the flow 
* Retrieval evaluation
    * 0 points: No evaluation of retrieval is provided
    * 1 point: Only one retrieval approach is evaluated
    * 2 points: Multiple retrieval approaches are evaluated, and the best one is used
* LLM evaluation
    * 0 points: No evaluation of final LLM output is provided
    * 1 point: Only one approach (e.g., one prompt) is evaluated
    * 2 points: Multiple approaches are evaluated, and the best one is used
* Interface
   * 0 points: No way to interact with the application at all
   * 1 point: Command line interface, a script, or a Jupyter notebook
   * 2 points: UI (e.g., Streamlit), web application (e.g., Django), or an API (e.g., built with FastAPI) 
* Ingestion pipeline
   * 0 points: No ingestion
   * 1 point: Semi-automated ingestion of the dataset into the knowledge base, e.g., with a Jupyter notebook
   * 2 points: Automated ingestion with a Python script or a special tool (e.g., Mage, dlt, Airflow, Prefect)
* Monitoring
   * 0 points: No monitoring
   * 1 point: User feedback is collected OR there's a monitoring dashboard
   * 2 points: User feedback is collected and there's a dashboard with at least 5 charts
* Containerization
    * 0 points: No containerization
    * 1 point: Dockerfile is provided for the main application OR there's a docker-compose for the dependencies only
    * 2 points: Everything is in docker-compose
* Reproducibility
    * 0 points: No instructions on how to run the code, the data is missing, or it's unclear how to access it
    * 1 point: Some instructions are provided but are incomplete, OR instructions are clear and complete, the code works, but the data is missing
    * 2 points: Instructions are clear, the dataset is accessible, it's easy to run the code, and it works. The versions for all dependencies are specified.
* Best practices
    * [ ] Hybrid search: combining both text and vector search (at least evaluating it) (1 point)
    * [ ] Document re-ranking (1 point)
    * [ ] User query rewriting (1 point)
* Bonus points (not covered in the course)
    * [ ] Deployment to the cloud (2 points)
    * [ ] Up to 3 extra bonus points if you want to award for something extra (write in feedback for what)


## Project Goal
Build an end-to-end RAG pipeline for YouTube audio content processing with question-answering capabilities.

## Phase 1: Project Structure & Setup ✅ COMPLETED
- [x] Create proper Python project structure (src/, tests/, docs/)
- [x] Extract requirements from Pipeline_Demo.py 
- [x] Create pyproject.toml with uv dependency management
- [x] Set up virtual environment with uv
- [x] Create .env.example for environment variables
- [x] Configure ruff for linting and formatting
- [x] Set up pytest for testing

## Phase 2: Modular Architecture ✅ COMPLETED
- [x] Refactor Pipeline_Demo.py into modular components:
  - [x] YouTube downloader module (yt_dlp integration)
  - [x] Audio processing module (faster-whisper ASR)
  - [x] Text processing module (normalization, chunking)  
  - [x] Embedding module (sentence-transformers)
  - [x] Vector storage module (ChromaDB)
  - [x] RAG query module (OpenAI integration)

## Phase 3: Configuration & Data Management ✅ COMPLETED
- [x] Create config management system
- [x] Set up data directories structure
- [x] Implement logging system
- [x] Add error handling and validation
- [x] Remove Google Colab dependencies

## Phase 4: API & Interface ✅ COMPLETED
- [x] Create FastAPI web interface
- [x] Implement REST API endpoints
- [x] Add Gradio UI for demo
- [x] Document API endpoints

## Phase 5: Testing & Quality ✅ MOSTLY COMPLETED
- [x] Add unit tests for each module (pytest)
- [x] Integration tests for full pipeline
- [ ] Performance testing with sample data
- [x] Code quality checks (ruff linting/formatting)

## Phase 6: Documentation & Deployment ✅ MOSTLY COMPLETED
- [x] Create comprehensive README
- [x] API documentation
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
✅ Complete modular project structure implemented
✅ Full interface layer (API, UI, CLI) working
✅ Comprehensive documentation created
🔄 Optional: Docker containerization and deployment guide pending

## Outstanding Items
- Performance testing with sample data
- Docker containerization  
- Deployment guide
- ML dependencies installation (requires `uv sync --extra ml`)