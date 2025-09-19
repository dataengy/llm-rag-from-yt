"""Configuration for RAG demo."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class RAGDemoConfig:
    """Configuration for RAG demo."""

    # File paths (relative to project root)
    # todo: move all scalars to config.yml
    local_transcript_path: Path = Path("../../data/audio/transcript.txt")
    main_transcript_path: Path = Path(
        "../../data/audio/В месяц ты зарабатываешь больше 1млн рублей？ Звезда ＂Реутов ТВ＂ у Дудя.real_transcript.txt"
    )

    # Video metadata
    video_title: str = (
        "В месяц ты зарабатываешь больше 1млн рублей？ Звезда ＂Реутов ТВ＂ у Дудя"
    )
    video_language: str = "ru"
    video_source: str = "YouTube Shorts"

    # Chunking parameters (fallback)
    fallback_chunk_size: int = 50  # words per chunk

    # Search parameters
    top_k_results: int = 3

    # Example questions
    example_questions: list[str] = None

    def __post_init__(self):
        """Initialize default example questions."""
        if self.example_questions is None:
            self.example_questions = [
                "Сколько зарабатывает герой видео?",
                "Чем занимается герой?",
                "Как он зарабатывает деньги?",
                "Что он говорит о работе?",
            ]

    @property
    def transcript_paths(self) -> list[Path]:
        """Get list of potential transcript file paths in order of preference."""
        return [self.local_transcript_path, self.main_transcript_path]


def get_demo_config() -> RAGDemoConfig:
    """Get RAG demo configuration."""
    return RAGDemoConfig()
