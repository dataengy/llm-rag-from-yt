"""Pydantic models for API requests and responses."""

from typing import Optional

from pydantic import BaseModel, Field


class ProcessUrlRequest(BaseModel):
    """Request model for processing YouTube URLs."""

    urls: list[str] = Field(..., description="List of YouTube URLs to process")
    use_fake_asr: bool = Field(False, description="Use fake ASR for testing")
    language: str = Field("ru", description="Language code for transcription")


class QueryRequest(BaseModel):
    """Request model for RAG queries."""

    question: str = Field(..., description="Question to ask the RAG system")
    top_k: Optional[int] = Field(3, description="Number of top results to return")
    system_prompt: Optional[str] = Field(None, description="Custom system prompt")


class ProcessUrlResponse(BaseModel):
    """Response model for URL processing."""

    status: str = Field(..., description="Processing status")
    message: str = Field(..., description="Status message")
    downloads: dict = Field(..., description="Download results")
    transcriptions_count: int = Field(..., description="Number of transcriptions")
    chunks_count: int = Field(..., description="Number of chunks created")


class QueryResponse(BaseModel):
    """Response model for RAG queries."""

    question: str = Field(..., description="Original question")
    answer: str = Field(..., description="Generated answer")
    sources: list[dict] = Field(..., description="Source documents used")
    context: str = Field(..., description="Context provided to LLM")


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    collection_info: dict = Field(..., description="Vector store information")


class FeedbackRequest(BaseModel):
    """Request model for user feedback."""

    query: str = Field(..., description="Original query")
    answer: str = Field(..., description="System answer")
    rating: int = Field(..., ge=1, le=5, description="User rating (1-5)")
    feedback_text: Optional[str] = Field(None, description="Optional feedback text")
    session_id: Optional[str] = Field(None, description="Session identifier")


class FeedbackResponse(BaseModel):
    """Response model for feedback submission."""

    feedback_id: str = Field(..., description="Feedback ID")
    status: str = Field(..., description="Submission status")


class ErrorResponse(BaseModel):
    """Response model for errors."""

    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
