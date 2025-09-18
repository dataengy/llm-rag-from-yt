"""Tests for configuration module."""

from pathlib import Path

from src.llm_rag_yt.config.settings import Config, get_config


class TestConfig:
    """Test cases for Config."""

    def test_config_defaults(self):
        """Test default configuration values."""
        config = Config()

        assert config.input_dir == Path("data/audio")
        assert config.collection_name == "rag_demo"
        assert config.chunk_size == 250
        assert config.chunk_overlap == 50
        assert config.top_k == 3

    def test_config_directories_created(self, tmp_path):
        """Test that configuration creates necessary directories."""
        config = Config(
            artifacts_dir=tmp_path / "artifacts",
            persist_dir=tmp_path / "persist",
            input_dir=tmp_path / "input",
        )

        assert config.artifacts_dir.exists()
        assert config.persist_dir.exists()
        assert config.input_dir.exists()

    def test_get_config(self):
        """Test get_config factory function."""
        config = get_config()
        assert isinstance(config, Config)
