"""Evaluation of different retrieval approaches."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from loguru import logger

from ..embeddings.encoder import EmbeddingEncoder
from ..vectorstore.chroma import ChromaVectorStore


class RetrievalEvaluator:
    """Evaluates different retrieval approaches."""

    def __init__(self, vector_store: ChromaVectorStore, encoder: EmbeddingEncoder):
        """Initialize evaluator."""
        self.vector_store = vector_store
        self.encoder = encoder

    def evaluate_retrieval_approaches(
        self,
        queries: list[str],
        ground_truth_docs: list[list[str]] = None,
        k_values: list[int] = None,
    ) -> dict[str, Any]:
        """Evaluate multiple retrieval approaches.

        Args:
            queries: List of test queries
            ground_truth_docs: Expected relevant documents for each query
            k_values: Different k values to test

        Returns:
            Evaluation results comparing different approaches
        """
        if k_values is None:
            k_values = [3, 5, 10]
        logger.info(f"Evaluating retrieval with {len(queries)} queries")

        results = {
            "timestamp": datetime.now().isoformat(),
            "queries": queries,
            "approaches": {},
            "summary": {},
        }

        # Approach 1: Semantic similarity only
        semantic_results = self._evaluate_semantic_retrieval(queries, k_values)
        results["approaches"]["semantic_only"] = semantic_results

        # Approach 2: Keyword + semantic hybrid
        hybrid_results = self._evaluate_hybrid_retrieval(queries, k_values)
        results["approaches"]["hybrid"] = hybrid_results

        # Approach 3: Different embedding models comparison
        embedding_results = self._evaluate_embedding_models(queries, k_values)
        results["approaches"]["embedding_models"] = embedding_results

        # Calculate best approach
        results["summary"] = self._summarize_results(results["approaches"])

        return results

    def _evaluate_semantic_retrieval(
        self, queries: list[str], k_values: list[int]
    ) -> dict[str, Any]:
        """Evaluate pure semantic retrieval."""
        results = {"method": "semantic_only", "k_results": {}}

        for k in k_values:
            k_results = []
            for query in queries:
                try:
                    query_embedding = self.encoder.embed_query(query)
                    docs = self.vector_store.query_similar(query_embedding, k)

                    # Calculate relevance scores
                    relevance_scores = [doc.get("distance", 0) for doc in docs]
                    avg_relevance = np.mean(relevance_scores) if relevance_scores else 0

                    k_results.append(
                        {
                            "query": query,
                            "num_results": len(docs),
                            "avg_relevance": float(avg_relevance),
                            "documents": docs[:3],  # Sample docs
                        }
                    )
                except Exception as e:
                    logger.error(f"Error in semantic retrieval for '{query}': {e}")
                    k_results.append(
                        {
                            "query": query,
                            "num_results": 0,
                            "avg_relevance": 0,
                            "error": str(e),
                        }
                    )

            results["k_results"][str(k)] = {
                "results": k_results,
                "avg_relevance": np.mean([r["avg_relevance"] for r in k_results]),
                "success_rate": len([r for r in k_results if "error" not in r])
                / len(k_results),
            }

        return results

    def _evaluate_hybrid_retrieval(
        self, queries: list[str], k_values: list[int]
    ) -> dict[str, Any]:
        """Evaluate hybrid keyword + semantic retrieval."""
        results = {"method": "hybrid", "k_results": {}}

        for k in k_values:
            k_results = []
            for query in queries:
                try:
                    # Get semantic results
                    query_embedding = self.encoder.embed_query(query)
                    semantic_docs = self.vector_store.query_similar(
                        query_embedding, k * 2
                    )

                    # Simple keyword filtering (in real implementation, use proper text search)
                    keywords = query.lower().split()
                    filtered_docs = []

                    for doc in semantic_docs:
                        text = doc.get("text", "").lower()
                        if any(keyword in text for keyword in keywords):
                            doc["relevance_boost"] = 0.1
                        else:
                            doc["relevance_boost"] = 0.0
                        filtered_docs.append(doc)

                    # Re-rank by combining semantic + keyword scores
                    for doc in filtered_docs:
                        original_score = 1 - doc.get(
                            "distance", 1
                        )  # Convert distance to similarity
                        doc["hybrid_score"] = original_score + doc["relevance_boost"]

                    # Sort by hybrid score and take top k
                    filtered_docs.sort(key=lambda x: x["hybrid_score"], reverse=True)
                    final_docs = filtered_docs[:k]

                    avg_relevance = (
                        np.mean([doc["hybrid_score"] for doc in final_docs])
                        if final_docs
                        else 0
                    )

                    k_results.append(
                        {
                            "query": query,
                            "num_results": len(final_docs),
                            "avg_relevance": float(avg_relevance),
                            "documents": final_docs[:3],  # Sample docs
                        }
                    )
                except Exception as e:
                    logger.error(f"Error in hybrid retrieval for '{query}': {e}")
                    k_results.append(
                        {
                            "query": query,
                            "num_results": 0,
                            "avg_relevance": 0,
                            "error": str(e),
                        }
                    )

            results["k_results"][str(k)] = {
                "results": k_results,
                "avg_relevance": np.mean([r["avg_relevance"] for r in k_results]),
                "success_rate": len([r for r in k_results if "error" not in r])
                / len(k_results),
            }

        return results

    def _evaluate_embedding_models(
        self, queries: list[str], k_values: list[int]
    ) -> dict[str, Any]:
        """Compare different embedding models."""
        models = [
            "sentence-transformers/all-MiniLM-L6-v2",
            "sentence-transformers/all-mpnet-base-v2",
            "intfloat/multilingual-e5-large-instruct",  # Current model
        ]

        results = {"method": "embedding_comparison", "models": {}}

        for model_name in models:
            try:
                logger.info(f"Testing embedding model: {model_name}")
                test_encoder = EmbeddingEncoder(model_name)

                model_results = {"k_results": {}}
                for k in k_values:
                    k_results = []
                    for query in queries:
                        try:
                            query_embedding = test_encoder.embed_query(query)
                            docs = self.vector_store.query_similar_with_embeddings(
                                query_embedding, k, test_encoder
                            )

                            relevance_scores = [doc.get("distance", 0) for doc in docs]
                            avg_relevance = (
                                np.mean(relevance_scores) if relevance_scores else 0
                            )

                            k_results.append(
                                {
                                    "query": query,
                                    "num_results": len(docs),
                                    "avg_relevance": float(avg_relevance),
                                }
                            )
                        except Exception as e:
                            logger.error(
                                f"Error with model {model_name} for '{query}': {e}"
                            )
                            k_results.append(
                                {
                                    "query": query,
                                    "num_results": 0,
                                    "avg_relevance": 0,
                                    "error": str(e),
                                }
                            )

                    model_results["k_results"][str(k)] = {
                        "avg_relevance": np.mean(
                            [r["avg_relevance"] for r in k_results]
                        ),
                        "success_rate": len([r for r in k_results if "error" not in r])
                        / len(k_results),
                    }

                results["models"][model_name] = model_results

            except Exception as e:
                logger.error(f"Failed to load model {model_name}: {e}")
                results["models"][model_name] = {"error": str(e)}

        return results

    def _summarize_results(self, approaches: dict[str, Any]) -> dict[str, Any]:
        """Summarize evaluation results to find best approach."""
        summary = {"best_approach": None, "best_k": None, "performance_comparison": {}}

        best_score = -1
        best_approach = None
        best_k = None

        for approach_name, approach_data in approaches.items():
            if "k_results" in approach_data:
                approach_scores = []
                for k, k_data in approach_data["k_results"].items():
                    score = k_data.get("avg_relevance", 0) * k_data.get(
                        "success_rate", 0
                    )
                    approach_scores.append(score)

                    if score > best_score:
                        best_score = score
                        best_approach = approach_name
                        best_k = int(k)

                summary["performance_comparison"][approach_name] = {
                    "avg_score": np.mean(approach_scores),
                    "max_score": max(approach_scores) if approach_scores else 0,
                }

        summary["best_approach"] = best_approach
        summary["best_k"] = best_k
        summary["best_score"] = best_score

        return summary

    def save_evaluation_results(
        self, results: dict[str, Any], output_path: Path
    ) -> None:
        """Save evaluation results to file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved evaluation results to {output_path}")

    def generate_test_queries(self) -> list[str]:
        """Generate test queries for evaluation."""
        return [
            "О чем говорят в видео?",
            "Какие основные темы обсуждаются?",
            "Кто участвует в разговоре?",
            "What is the main topic discussed?",
            "Who are the speakers?",
            "What are the key points mentioned?",
            "Какие проблемы обсуждаются?",
            "What solutions are proposed?",
        ]

    def run_evaluation_suite(self, output_dir: Path) -> dict[str, Any]:
        """Run complete evaluation suite."""
        logger.info("Starting retrieval evaluation suite")

        # Generate test queries
        queries = self.generate_test_queries()

        # Run evaluation
        results = self.evaluate_retrieval_approaches(queries)

        # Save results
        output_path = (
            output_dir
            / f"retrieval_evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        self.save_evaluation_results(results, output_path)

        # Log summary
        best_approach = results["summary"]["best_approach"]
        best_k = results["summary"]["best_k"]
        best_score = results["summary"]["best_score"]

        logger.info(
            f"Best retrieval approach: {best_approach} with k={best_k} (score: {best_score:.3f})"
        )

        return results
