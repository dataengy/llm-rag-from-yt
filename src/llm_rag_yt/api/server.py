"""FastAPI server for RAG pipeline."""

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from .. import __version__
from ..pipeline import RAGPipeline
from .models import (
    ErrorResponse,
    HealthResponse,
    ProcessUrlRequest,
    ProcessUrlResponse,
    QueryRequest,
    QueryResponse,
)

# Global pipeline instance
pipeline: Optional[RAGPipeline] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    global pipeline
    logger.info("Starting RAG API server")
    
    try:
        pipeline = RAGPipeline()
        logger.info("RAG Pipeline initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize pipeline: {e}")
        raise
    
    yield
    
    logger.info("Shutting down RAG API server")


app = FastAPI(
    title="LLM RAG YouTube Audio Processing API",
    description="Process YouTube audio content and answer questions using RAG",
    version=__version__,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    if pipeline is None:
        raise HTTPException(status_code=500, detail="Pipeline not initialized")
    
    try:
        collection_info = pipeline.vector_store.get_collection_info()
        return HealthResponse(
            status="healthy",
            version=__version__,
            collection_info=collection_info,
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process", response_model=ProcessUrlResponse)
async def process_urls(request: ProcessUrlRequest):
    """Process YouTube URLs through the RAG pipeline."""
    if pipeline is None:
        raise HTTPException(status_code=500, detail="Pipeline not initialized")
    
    try:
        logger.info(f"Processing {len(request.urls)} URLs")
        
        # Update config for this request
        pipeline.config.use_fake_asr = request.use_fake_asr
        pipeline.transcriber = pipeline.transcriber.__class__(
            model_name=pipeline.config.asr_model,
            device=pipeline.config.device,
            compute_type=pipeline.config.whisper_precision,
        )
        
        results = pipeline.download_and_process(request.urls)
        
        return ProcessUrlResponse(
            status="success",
            message=f"Processed {len(request.urls)} URLs successfully",
            downloads=results.get("downloads", {}),
            transcriptions_count=len(results.get("transcriptions", {})),
            chunks_count=results.get("chunks", 0),
        )
        
    except Exception as e:
        logger.error(f"Failed to process URLs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """Query the RAG system with a question."""
    if pipeline is None:
        raise HTTPException(status_code=500, detail="Pipeline not initialized")
    
    try:
        logger.info(f"Processing query: {request.question[:50]}...")
        
        result = pipeline.query_engine.query(
            request.question,
            top_k=request.top_k or 3,
            system_prompt=request.system_prompt,
        )
        
        return QueryResponse(
            question=result["question"],
            answer=result["answer"],
            sources=result["sources"],
            context=result["context"],
        )
        
    except Exception as e:
        logger.error(f"Failed to process query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status")
async def get_status():
    """Get pipeline status information."""
    if pipeline is None:
        raise HTTPException(status_code=500, detail="Pipeline not initialized")
    
    try:
        status = pipeline.get_status()
        return {
            "pipeline_status": "active",
            "collection": status["collection"],
            "config": {
                "chunk_size": status["config"].chunk_size,
                "chunk_overlap": status["config"].chunk_overlap,
                "embedding_model": status["config"].embedding_model,
                "openai_model": status["config"].openai_model,
            },
        }
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")