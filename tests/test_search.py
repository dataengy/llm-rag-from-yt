"""Tests for advanced search components."""

import pytest
from unittest.mock import Mock, patch

from llm_rag_yt.search.hybrid_search import HybridSearchEngine
from llm_rag_yt.search.query_rewriter import QueryRewriter


class TestHybridSearchEngine:
    """Test hybrid search functionality."""

    @pytest.fixture
    def mock_vector_store(self):
        """Mock vector store."""
        mock_store = Mock()
        mock_store.query_similar.return_value = [
            {"id": "doc1", "text": "Python programming tutorial", "distance": 0.1},
            {"id": "doc2", "text": "Machine learning basics", "distance": 0.2}
        ]
        return mock_store

    @pytest.fixture
    def mock_encoder(self):
        """Mock embedding encoder."""
        mock_encoder = Mock()
        mock_encoder.embed_query.return_value = [0.1, 0.2, 0.3]
        return mock_encoder

    def test_search_engine_initialization(self, mock_vector_store, mock_encoder):
        """Test hybrid search engine initialization."""
        engine = HybridSearchEngine(mock_vector_store, mock_encoder)
        assert engine.vector_store == mock_vector_store
        assert engine.encoder == mock_encoder

    def test_keyword_extraction(self, mock_vector_store, mock_encoder):
        """Test keyword extraction."""
        engine = HybridSearchEngine(mock_vector_store, mock_encoder)
        
        # Test Russian query
        keywords_ru = engine._extract_keywords("Что такое машинное обучение?")
        assert "машинное" in keywords_ru
        assert "обучение" in keywords_ru
        assert "что" not in keywords_ru  # Stop word
        
        # Test English query
        keywords_en = engine._extract_keywords("What is machine learning?")
        assert "machine" in keywords_en
        assert "learning" in keywords_en
        assert "what" not in keywords_en  # Stop word

    def test_text_score_calculation(self, mock_vector_store, mock_encoder):
        """Test text relevance scoring."""
        engine = HybridSearchEngine(mock_vector_store, mock_encoder)
        
        text = "This is about machine learning and artificial intelligence"
        keywords = ["machine", "learning"]
        
        score = engine._calculate_text_score(text, keywords)
        assert score > 0
        assert isinstance(score, float)

    def test_search_method_detection(self, mock_vector_store, mock_encoder):
        """Test search method detection."""
        engine = HybridSearchEngine(mock_vector_store, mock_encoder)
        
        # Test both methods
        scores = {"vector_rank": 1, "text_rank": 2}
        method = engine._get_search_method(scores)
        assert method == "both"
        
        # Test vector only
        scores = {"vector_rank": 1, "text_rank": float('inf')}
        method = engine._get_search_method(scores)
        assert method == "vector"
        
        # Test text only
        scores = {"vector_rank": float('inf'), "text_rank": 1}
        method = engine._get_search_method(scores)
        assert method == "text"


class TestQueryRewriter:
    """Test query rewriting functionality."""

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'})
    def test_rewriter_initialization(self):
        """Test query rewriter initialization."""
        with patch('llm_rag_yt.search.query_rewriter.OpenAI'):
            rewriter = QueryRewriter()
            assert rewriter.model_name == "gpt-4o-mini"

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'})
    def test_rule_based_variants(self):
        """Test rule-based query variants."""
        with patch('llm_rag_yt.search.query_rewriter.OpenAI'):
            rewriter = QueryRewriter()
            
            # Test question word addition
            variants = rewriter._add_question_words("Python programming")
            assert len(variants) > 0
            
            # Test synonym expansion
            variants = rewriter._expand_with_synonyms("Обсуждение видео")
            assert any("рассказывать" in v or "упоминать" in v for v in variants)

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'})
    def test_keyword_extraction(self):
        """Test keyword extraction from queries."""
        with patch('llm_rag_yt.search.query_rewriter.OpenAI'):
            rewriter = QueryRewriter()
            
            keywords = rewriter._extract_keywords("Что такое машинное обучение?")
            assert "машинное" in keywords
            assert "обучение" in keywords
            assert "что" not in keywords  # Question word removed

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'})
    def test_domain_expansions(self):
        """Test domain-specific query expansions."""
        with patch('llm_rag_yt.search.query_rewriter.OpenAI'):
            rewriter = QueryRewriter()
            
            expansions = rewriter._add_domain_expansions("Python tutorial")
            assert any("видео" in exp for exp in expansions)
            assert any("говорят" in exp for exp in expansions)

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'})
    def test_reciprocal_rank_fusion(self):
        """Test reciprocal rank fusion algorithm."""
        with patch('llm_rag_yt.search.query_rewriter.OpenAI'):
            rewriter = QueryRewriter()
            
            # Mock search results from different queries
            results_dict = {
                "query_0": [
                    {"id": "doc1", "text": "First result", "distance": 0.1},
                    {"id": "doc2", "text": "Second result", "distance": 0.2}
                ],
                "query_1": [
                    {"id": "doc2", "text": "Second result", "distance": 0.15},
                    {"id": "doc3", "text": "Third result", "distance": 0.25}
                ]
            }
            
            fused = rewriter._reciprocal_rank_fusion(results_dict)
            
            assert len(fused) > 0
            assert all("rrf_score" in doc for doc in fused)
            assert all("query_appearances" in doc for doc in fused)
            
            # Doc2 should have higher score (appears in both queries)
            doc2_score = next(doc["rrf_score"] for doc in fused if doc["id"] == "doc2")
            doc1_score = next(doc["rrf_score"] for doc in fused if doc["id"] == "doc1")
            assert doc2_score > doc1_score