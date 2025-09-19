"""Evaluation of different LLM approaches and prompts."""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from loguru import logger
from openai import OpenAI

from ..embeddings.encoder import EmbeddingEncoder
from ..vectorstore.chroma import ChromaVectorStore


class LLMEvaluator:
    """Evaluates different LLM approaches and prompts."""

    def __init__(self, vector_store: ChromaVectorStore, encoder: EmbeddingEncoder):
        """Initialize evaluator."""
        self.vector_store = vector_store
        self.encoder = encoder
        self.client = OpenAI()

    def evaluate_llm_approaches(
        self,
        queries: List[str],
        models: List[str] = None,
        system_prompts: List[str] = None,
        top_k: int = 3
    ) -> Dict[str, Any]:
        """Evaluate different LLM models and prompt strategies.
        
        Args:
            queries: Test queries
            models: List of OpenAI models to test
            system_prompts: Different system prompts to evaluate
            top_k: Number of documents to retrieve for context
            
        Returns:
            Comprehensive evaluation results
        """
        if models is None:
            models = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]
        
        if system_prompts is None:
            system_prompts = self._get_system_prompts()
        
        logger.info(f"Evaluating {len(models)} models with {len(system_prompts)} prompts on {len(queries)} queries")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "queries": queries,
            "models": {},
            "prompts": {},
            "combinations": {},
            "summary": {}
        }
        
        # Evaluate models with default prompt
        default_prompt = system_prompts[0]
        for model in models:
            results["models"][model] = self._evaluate_model(
                model, queries, default_prompt, top_k
            )
        
        # Evaluate prompts with default model
        default_model = "gpt-4o"
        for i, prompt in enumerate(system_prompts):
            prompt_name = f"prompt_{i+1}"
            results["prompts"][prompt_name] = self._evaluate_prompt(
                default_model, queries, prompt, top_k
            )
        
        # Evaluate best combinations
        best_combinations = self._evaluate_best_combinations(
            queries, models[:2], system_prompts[:3], top_k
        )
        results["combinations"] = best_combinations
        
        # Generate summary
        results["summary"] = self._summarize_llm_results(results)
        
        return results

    def _get_system_prompts(self) -> List[str]:
        """Get different system prompts to evaluate."""
        return [
            "Отвечай только на основе контекста. Если ответа нет — скажи, что не знаешь.",
            
            "Ты эксперт-аналитик. Используй предоставленный контекст для ответа на вопрос. "
            "Если информации недостаточно, честно об этом скажи. "
            "Структурируй ответ и выделяй ключевые моменты.",
            
            "Answer based on the provided context. If you don't know the answer, say so. "
            "Be concise and accurate.",
            
            "Ты помощник для анализа аудиоконтента. Используй только информацию из контекста. "
            "Отвечай подробно, но структурированно. Указывай источники информации.",
            
            "You are an AI assistant that analyzes YouTube audio content. "
            "Use only the provided context to answer questions. "
            "If the context doesn't contain the answer, explicitly state that. "
            "Provide detailed, well-structured responses with key insights."
        ]

    def _evaluate_model(
        self, model: str, queries: List[str], system_prompt: str, top_k: int
    ) -> Dict[str, Any]:
        """Evaluate a specific model."""
        results = {
            "model": model,
            "query_results": [],
            "metrics": {}
        }
        
        total_time = 0
        successful_queries = 0
        
        for query in queries:
            try:
                start_time = time.time()
                
                # Get context
                query_embedding = self.encoder.embed_query(query)
                similar_docs = self.vector_store.query_similar(query_embedding, top_k)
                context = "\n".join(f"{i + 1}. {doc['text']}" for i, doc in enumerate(similar_docs))
                
                user_prompt = f"Вопрос: {query}\n\nКонтекст:\n{context}"
                
                # Query LLM
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.3,
                    max_tokens=256,
                )
                
                end_time = time.time()
                response_time = end_time - start_time
                total_time += response_time
                
                answer = response.choices[0].message.content
                tokens_used = response.usage.total_tokens if response.usage else 0
                
                results["query_results"].append({
                    "query": query,
                    "answer": answer,
                    "response_time": response_time,
                    "tokens_used": tokens_used,
                    "context_docs": len(similar_docs)
                })
                
                successful_queries += 1
                
            except Exception as e:
                logger.error(f"Error evaluating model {model} for query '{query}': {e}")
                results["query_results"].append({
                    "query": query,
                    "error": str(e),
                    "response_time": 0,
                    "tokens_used": 0
                })
        
        # Calculate metrics
        results["metrics"] = {
            "success_rate": successful_queries / len(queries),
            "avg_response_time": total_time / successful_queries if successful_queries else 0,
            "total_tokens": sum(r.get("tokens_used", 0) for r in results["query_results"]),
            "avg_tokens_per_query": sum(r.get("tokens_used", 0) for r in results["query_results"]) / successful_queries if successful_queries else 0
        }
        
        return results

    def _evaluate_prompt(
        self, model: str, queries: List[str], system_prompt: str, top_k: int
    ) -> Dict[str, Any]:
        """Evaluate a specific prompt."""
        return self._evaluate_model(model, queries, system_prompt, top_k)

    def _evaluate_best_combinations(
        self, queries: List[str], models: List[str], prompts: List[str], top_k: int
    ) -> Dict[str, Any]:
        """Evaluate best model-prompt combinations."""
        combinations = {}
        
        for model in models:
            for i, prompt in enumerate(prompts):
                combo_name = f"{model}_prompt_{i+1}"
                combinations[combo_name] = self._evaluate_model(
                    model, queries[:3], prompt, top_k  # Use fewer queries for combinations
                )
        
        return combinations

    def _summarize_llm_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize LLM evaluation results."""
        summary = {
            "best_model": None,
            "best_prompt": None,
            "best_combination": None,
            "model_comparison": {},
            "prompt_comparison": {},
            "recommendations": []
        }
        
        # Find best model
        best_model_score = -1
        best_model = None
        for model, data in results["models"].items():
            score = data["metrics"]["success_rate"] / (data["metrics"]["avg_response_time"] + 0.1)
            summary["model_comparison"][model] = {
                "score": score,
                "success_rate": data["metrics"]["success_rate"],
                "avg_response_time": data["metrics"]["avg_response_time"],
                "avg_tokens": data["metrics"]["avg_tokens_per_query"]
            }
            if score > best_model_score:
                best_model_score = score
                best_model = model
        
        summary["best_model"] = best_model
        
        # Find best prompt (using default model results)
        best_prompt_score = -1
        best_prompt = None
        for prompt_name, data in results["prompts"].items():
            score = data["metrics"]["success_rate"]
            summary["prompt_comparison"][prompt_name] = {
                "score": score,
                "success_rate": data["metrics"]["success_rate"],
                "avg_response_time": data["metrics"]["avg_response_time"]
            }
            if score > best_prompt_score:
                best_prompt_score = score
                best_prompt = prompt_name
        
        summary["best_prompt"] = best_prompt
        
        # Find best combination
        if results["combinations"]:
            best_combo_score = -1
            best_combo = None
            for combo_name, data in results["combinations"].items():
                score = data["metrics"]["success_rate"]
                if score > best_combo_score:
                    best_combo_score = score
                    best_combo = combo_name
            summary["best_combination"] = best_combo
        
        # Generate recommendations
        summary["recommendations"] = [
            f"Use {best_model} for best performance balance",
            f"Use {best_prompt} for best prompt effectiveness",
            "Consider cost vs. performance trade-offs for production",
            "Monitor token usage for budget optimization"
        ]
        
        return summary

    def save_evaluation_results(self, results: Dict[str, Any], output_path: Path) -> None:
        """Save LLM evaluation results."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved LLM evaluation results to {output_path}")

    def run_evaluation_suite(self, output_dir: Path) -> Dict[str, Any]:
        """Run complete LLM evaluation suite."""
        logger.info("Starting LLM evaluation suite")
        
        # Generate test queries
        queries = [
            "О чем говорят в видео?",
            "Какие основные темы обсуждаются?",
            "Кто участвует в разговоре?",
            "What is the main topic discussed?",
            "What are the key points mentioned?"
        ]
        
        # Run evaluation
        results = self.evaluate_llm_approaches(queries)
        
        # Save results
        output_path = output_dir / f"llm_evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.save_evaluation_results(results, output_path)
        
        # Log summary
        best_model = results["summary"]["best_model"]
        best_prompt = results["summary"]["best_prompt"]
        
        logger.info(f"Best LLM model: {best_model}")
        logger.info(f"Best prompt: {best_prompt}")
        
        return results