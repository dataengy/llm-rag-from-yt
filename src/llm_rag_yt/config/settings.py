"""Configuration settings for the RAG pipeline."""

from dataclasses import dataclass
from pathlib import Path

try:
    import torch

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


@dataclass
class Config:
    """Configuration for the RAG pipeline."""

    input_dir: Path = Path("data/audio")
    artifacts_dir: Path = Path("artifacts")
    persist_dir: Path = Path("data/chroma_db")
    collection_name: str = "rag_demo"
    asr_model: str = "large-v3"
    embedding_model: str = "intfloat/multilingual-e5-large-instruct"
    openai_model: str = "gpt-4o"
    use_fake_asr: bool = False
    use_vad: bool = False
    segment_sec: int = 60
    beam_size: int = 5
    device: str = "cuda" if TORCH_AVAILABLE and torch.cuda.is_available() else "cpu"
    whisper_precision: str = (
        "float16" if (TORCH_AVAILABLE and torch.cuda.is_available()) else "int8"
    )
    chunk_size: int = 250
    chunk_overlap: int = 50
    max_tokens: int = 256
    temperature: float = 0.3
    top_k: int = 3

    def __post_init__(self):
        """Create necessary directories."""
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.input_dir.mkdir(parents=True, exist_ok=True)


def get_config() -> Config:
    """Get default configuration."""
    return Config()
