"""Tests for evaluation components."""

from unittest.mock import Mock, patch

import pytest

from llm_rag_yt.evaluation.llm_evaluator import LLMEvaluator
from llm_rag_yt.evaluation.retrieval_evaluator import RetrievalEvaluator


class TestRetrievalEvaluator:
    """Test retrieval evaluation functionality."""

    @pytest.fixture
    def mock_vector_store(self):
        """Mock vector store."""
        mock_store = Mock()
        mock_store.query_similar.return_value = [
            {"id": "doc1", "text": "Sample text 1", "distance": 0.1},
            {"id": "doc2", "text": "Sample text 2", "distance": 0.2},
        ]
        mock_store.query_similar_with_embeddings.return_value = [
            {"id": "doc1", "text": "Sample text 1", "distance": 0.15}
        ]
        return mock_store

    @pytest.fixture
    def mock_encoder(self):
        """Mock embedding encoder."""
        mock_encoder = Mock()
        mock_encoder.embed_query.return_value = [0.1, 0.2, 0.3]
        return mock_encoder

    def test_evaluator_initialization(self, mock_vector_store, mock_encoder):
        """Test evaluator initialization."""
        evaluator = RetrievalEvaluator(mock_vector_store, mock_encoder)
        assert evaluator.vector_store == mock_vector_store
        assert evaluator.encoder == mock_encoder

    def test_generate_test_queries(self, mock_vector_store, mock_encoder):
        """Test test query generation."""
        evaluator = RetrievalEvaluator(mock_vector_store, mock_encoder)
        queries = evaluator.generate_test_queries()

        assert len(queries) > 0
        assert all(isinstance(q, str) for q in queries)
        assert any("О чем" in q for q in queries)  # Russian queries
        assert any("What" in q for q in queries)  # English queries

    def test_semantic_retrieval_evaluation(self, mock_vector_store, mock_encoder):
        """Test semantic retrieval evaluation."""
        evaluator = RetrievalEvaluator(mock_vector_store, mock_encoder)

        queries = ["Test query"]
        k_values = [3, 5]

        result = evaluator._evaluate_semantic_retrieval(queries, k_values)

        assert result["method"] == "semantic_only"
        assert "k_results" in result
        assert "3" in result["k_results"]
        assert "5" in result["k_results"]


class TestLLMEvaluator:
    """Test LLM evaluation functionality."""

    @pytest.fixture
    def mock_vector_store(self):
        """Mock vector store."""
        mock_store = Mock()
        mock_store.query_similar.return_value = [
            {"id": "doc1", "text": "Sample context", "distance": 0.1}
        ]
        return mock_store

    @pytest.fixture
    def mock_encoder(self):
        """Mock embedding encoder."""
        mock_encoder = Mock()
        mock_encoder.embed_query.return_value = [0.1, 0.2, 0.3]
        return mock_encoder

    def test_evaluator_initialization(self, mock_vector_store, mock_encoder):
        """Test evaluator initialization."""
        with patch("llm_rag_yt.evaluation.llm_evaluator.OpenAI"):
            evaluator = LLMEvaluator(mock_vector_store, mock_encoder)
            assert evaluator.vector_store == mock_vector_store
            assert evaluator.encoder == mock_encoder

    def test_get_system_prompts(self, mock_vector_store, mock_encoder):
        """Test system prompt generation."""
        with patch("llm_rag_yt.evaluation.llm_evaluator.OpenAI"):
            evaluator = LLMEvaluator(mock_vector_store, mock_encoder)
            prompts = evaluator._get_system_prompts()

            assert len(prompts) >= 3
            assert all(isinstance(p, str) for p in prompts)
            assert any("контекст" in p.lower() for p in prompts)  # Russian prompts
            assert any("context" in p.lower() for p in prompts)  # English prompts

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test_key"})
    def test_summarize_llm_results(self, mock_vector_store, mock_encoder):
        """Test LLM results summarization."""
        with patch("llm_rag_yt.evaluation.llm_evaluator.OpenAI"):
            evaluator = LLMEvaluator(mock_vector_store, mock_encoder)

            # Mock results structure
            results = {
                "models": {
                    "gpt-4o": {
                        "metrics": {
                            "success_rate": 1.0,
                            "avg_response_time": 2.0,
                            "avg_tokens_per_query": 100,
                        }
                    },
                    "gpt-3.5-turbo": {
                        "metrics": {
                            "success_rate": 0.9,
                            "avg_response_time": 1.0,
                            "avg_tokens_per_query": 80,
                        }
                    },
                },
                "prompts": {
                    "prompt_1": {
                        "metrics": {"success_rate": 1.0, "avg_response_time": 1.5}
                    },
                    "prompt_2": {
                        "metrics": {"success_rate": 0.8, "avg_response_time": 2.0}
                    },
                },
                "combinations": {},
            }

            summary = evaluator._summarize_llm_results(results)

            assert "best_model" in summary
            assert "best_prompt" in summary
            assert "recommendations" in summary
            assert len(summary["recommendations"]) > 0
