"""Configuration settings for the RAG pipeline."""

import os
from dataclasses import dataclass
from pathlib import Path

try:
    import torch

    TORCH_AVAILABLE = True
    CUDA_AVAILABLE = torch.cuda.is_available() if hasattr(torch, "cuda") else False
except ImportError:
    TORCH_AVAILABLE = False
    CUDA_AVAILABLE = False


def _get_required_env(key: str) -> str:
    """Get required environment variable."""
    value = os.getenv(key)
    if not value:
        raise ValueError(f"Required environment variable {key} is not set")
    return value


def _get_env_bool(key: str, default: bool = False) -> bool:
    """Get boolean environment variable."""
    value = os.getenv(key, str(default)).lower()
    return value in ("true", "1", "yes", "on")


def _get_env_int(key: str) -> int:
    """Get required integer environment variable."""
    value = _get_required_env(key)
    try:
        return int(value)
    except ValueError as e:
        raise ValueError(f"Environment variable {key} must be an integer, got: {value}") from e


def _get_env_float(key: str) -> float:
    """Get required float environment variable."""
    value = _get_required_env(key)
    try:
        return float(value)
    except ValueError as e:
        raise ValueError(f"Environment variable {key} must be a float, got: {value}") from e


@dataclass
class Config:
    """Configuration for the RAG pipeline."""

    input_dir: Path
    artifacts_dir: Path
    persist_dir: Path
    collection_name: str
    asr_model: str
    embedding_model: str
    openai_model: str
    use_fake_asr: bool
    use_vad: bool
    segment_sec: int
    beam_size: int
    device: str
    whisper_precision: str
    chunk_size: int
    chunk_overlap: int
    max_tokens: int
    temperature: float
    top_k: int

    def __post_init__(self):
        """Create necessary directories."""
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.input_dir.mkdir(parents=True, exist_ok=True)


def get_config() -> Config:
    """Get configuration from environment variables."""
    # Auto-detect device if not explicitly set
    device = os.getenv("DEVICE", "auto")
    if device == "auto":
        device = "cuda" if CUDA_AVAILABLE else "cpu"

    # Auto-detect precision if not explicitly set
    whisper_precision = os.getenv("WHISPER_PRECISION", "auto")
    if whisper_precision == "auto":
        whisper_precision = "float16" if CUDA_AVAILABLE else "int8"

    return Config(
        input_dir=Path(os.getenv("INPUT_DIR", "data/audio")),
        artifacts_dir=Path(os.getenv("ARTIFACTS_DIR", "artifacts")),
        persist_dir=Path(os.getenv("CHROMA_DB_PATH", "data/chroma_db")),
        collection_name=os.getenv("COLLECTION_NAME", "rag_demo"),
        asr_model=_get_required_env("ASR_MODEL"),
        embedding_model=_get_required_env("EMBEDDING_MODEL"),
        openai_model=_get_required_env("OPENAI_MODEL"),
        use_fake_asr=_get_env_bool("USE_FAKE_ASR"),
        use_vad=_get_env_bool("USE_VAD"),
        segment_sec=_get_env_int("SEGMENT_SEC") if os.getenv("SEGMENT_SEC") else 60,
        beam_size=_get_env_int("BEAM_SIZE") if os.getenv("BEAM_SIZE") else 5,
        device=device,
        whisper_precision=whisper_precision,
        chunk_size=_get_env_int("CHUNK_SIZE"),
        chunk_overlap=_get_env_int("CHUNK_OVERLAP"),
        max_tokens=_get_env_int("MAX_TOKENS") if os.getenv("MAX_TOKENS") else 256,
        temperature=_get_env_float("TEMPERATURE") if os.getenv("TEMPERATURE") else 0.3,
        top_k=_get_env_int("TOP_K"),
    )
