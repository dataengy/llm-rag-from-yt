"""Tests for text processing module."""

from src.llm_rag_yt.text.processor import TextProcessor


class TestTextProcessor:
    """Test cases for TextProcessor."""

    def setup_method(self):
        """Set up test fixtures."""
        self.processor = TextProcessor()

    def test_normalize_text_basic(self):
        """Test basic text normalization."""
        text = "  hello   world  "
        result = self.processor.normalize_text(text)
        assert result == "Hello world"

    def test_normalize_text_empty(self):
        """Test normalization of empty text."""
        assert self.processor.normalize_text("") == ""
        assert self.processor.normalize_text(None) == ""

    def test_normalize_text_already_capitalized(self):
        """Test text that's already properly capitalized."""
        text = "Hello world"
        result = self.processor.normalize_text(text)
        assert result == "Hello world"

    def test_split_into_chunks_basic(self):
        """Test basic text chunking."""
        text = " ".join([f"word{i}" for i in range(10)])
        chunks = self.processor.split_into_chunks(text, chunk_size=5, overlap=2)

        assert len(chunks) == 4
        assert "word0" in chunks[0]
        assert "word4" in chunks[0]
        assert "word3" in chunks[1]  # overlap

    def test_split_into_chunks_empty(self):
        """Test chunking empty text."""
        result = self.processor.split_into_chunks("")
        assert result == []

    def test_split_into_chunks_no_overlap(self):
        """Test chunking without overlap."""
        text = " ".join([f"word{i}" for i in range(10)])
        chunks = self.processor.split_into_chunks(text, chunk_size=5, overlap=0)

        assert len(chunks) == 2
        assert "word4" in chunks[0]
        assert "word5" in chunks[1]

    def test_process_transcriptions(self):
        """Test processing transcription results."""
        transcriptions = {
            "file1": {"full_text": "  hello   world  "},
            "file2": {"full_text": "another  text"},
        }

        result = self.processor.process_transcriptions(transcriptions)

        assert result["file1"] == "Hello world"
        assert result["file2"] == "Another text"

    def test_create_chunks(self):
        """Test chunk creation from normalized texts."""
        normalized_texts = {"file1": "Hello world test", "file2": "Another test text"}

        chunks = self.processor.create_chunks(normalized_texts, chunk_size=2, overlap=0)

        assert len(chunks) == 4
        assert chunks[0]["id"] == "file1::chunk::0"
        assert chunks[0]["metadata"]["source_id"] == "file1"
        assert "Hello world" in chunks[0]["text"]
