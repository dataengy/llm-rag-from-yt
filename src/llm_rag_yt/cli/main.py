"""Command-line interface for RAG pipeline."""

import sys
from pathlib import Path
from typing import Optional

import typer
from loguru import logger
from rich.console import Console
from rich.table import Table

from .. import __version__
from ..pipeline import RAGPipeline

app = typer.Typer(
    name="llm-rag-yt",
    help="LLM RAG YouTube Audio Processing CLI",
    add_completion=False,
)
console = Console()


@app.command()
def version():
    """Show version information."""
    console.print(f"LLM RAG YouTube Audio Processing v{__version__}")


@app.command()
def process(
    urls: list[str] = typer.Argument(..., help="YouTube URLs to process"),
    fake_asr: bool = typer.Option(False, "--fake-asr", help="Use fake ASR for testing"),
    language: str = typer.Option("ru", "--language", "-l", help="Language code"),
    config_file: Optional[Path] = typer.Option(
        None, "--config", help="Config file path"
    ),
):
    """Process YouTube URLs through the RAG pipeline."""
    try:
        console.print(f"🔄 Processing {len(urls)} URLs...")

        pipeline = RAGPipeline()
        pipeline.config.use_fake_asr = fake_asr

        # Reinitialize transcriber with new settings
        pipeline.transcriber = pipeline.transcriber.__class__(
            model_name=pipeline.config.asr_model,
            device=pipeline.config.device,
            compute_type=pipeline.config.whisper_precision,
        )

        results = pipeline.download_and_process(urls)

        # Display results
        table = Table(title="Processing Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="green")

        table.add_row("Downloads", str(len(results.get("downloads", {}))))
        table.add_row("Transcriptions", str(len(results.get("transcriptions", {}))))
        table.add_row("Chunks", str(results.get("chunks", 0)))

        console.print(table)
        console.print("✅ Processing completed successfully!")

    except Exception as e:
        logger.error(f"Processing failed: {e}")
        console.print(f"❌ Error: {e}", style="red")
        sys.exit(1)


@app.command()
def query(
    question: str = typer.Argument(..., help="Question to ask"),
    top_k: int = typer.Option(3, "--top-k", "-k", help="Number of top results"),
    interactive: bool = typer.Option(
        False, "--interactive", "-i", help="Interactive mode"
    ),
):
    """Query the RAG system."""
    try:
        pipeline = RAGPipeline()

        if interactive:
            console.print("🔍 Interactive RAG Query Mode (type 'exit' to quit)")
            while True:
                question = typer.prompt("Question")
                if question.lower() in ["exit", "quit"]:
                    break

                result = pipeline.query(question, top_k)

                console.print(
                    f"\n💡 [bold green]Answer:[/bold green] {result['answer']}"
                )

                console.print("\n📚 [bold blue]Sources:[/bold blue]")
                for i, source in enumerate(result["sources"], 1):
                    source_id = source.get("metadata", {}).get("source_id", "unknown")
                    distance = source.get("distance", 0)
                    console.print(
                        f"  {i}. {source_id} (similarity: {1 - distance:.3f})"
                    )
                    console.print(f"     {source['text'][:100]}...")

                console.print()
        else:
            result = pipeline.query(question, top_k)

            console.print(f"💡 [bold green]Answer:[/bold green] {result['answer']}")

            console.print("\n📚 [bold blue]Sources:[/bold blue]")
            for i, source in enumerate(result["sources"], 1):
                source_id = source.get("metadata", {}).get("source_id", "unknown")
                distance = source.get("distance", 0)
                console.print(f"  {i}. {source_id} (similarity: {1 - distance:.3f})")
                console.print(f"     {source['text'][:100]}...")

    except Exception as e:
        logger.error(f"Query failed: {e}")
        console.print(f"❌ Error: {e}", style="red")
        sys.exit(1)


@app.command()
def status():
    """Show pipeline status."""
    try:
        pipeline = RAGPipeline()
        status_info = pipeline.get_status()

        table = Table(title="Pipeline Status")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")

        collection_info = status_info["collection"]
        table.add_row("Collection", collection_info["name"])
        table.add_row("Documents", str(collection_info["count"]))
        table.add_row("Storage", str(status_info["artifacts_dir"]))
        table.add_row("Input Dir", str(status_info["input_dir"]))

        console.print(table)

    except Exception as e:
        logger.error(f"Status check failed: {e}")
        console.print(f"❌ Error: {e}", style="red")
        sys.exit(1)


@app.command()
def serve_api(
    host: str = typer.Option("0.0.0.0", "--host", help="Host to bind"),
    port: int = typer.Option(8000, "--port", help="Port to bind"),
):
    """Start the FastAPI server."""
    try:
        import uvicorn

        from ..api.server import app as fastapi_app

        console.print(f"🚀 Starting API server on {host}:{port}")
        uvicorn.run(fastapi_app, host=host, port=port, log_level="info")

    except ImportError:
        console.print("❌ FastAPI not available", style="red")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        console.print(f"❌ Error: {e}", style="red")
        sys.exit(1)


@app.command()
def serve_ui(
    host: str = typer.Option("0.0.0.0", "--host", help="Host to bind"),
    port: int = typer.Option(7860, "--port", help="Port to bind"),
    share: bool = typer.Option(False, "--share", help="Create public link"),
):
    """Start the Gradio UI."""
    try:
        from ..ui.gradio_app import create_app

        console.print(f"🎨 Starting Gradio UI on {host}:{port}")
        gradio_app = create_app()
        gradio_app.launch(
            server_name=host,
            server_port=port,
            share=share,
            show_error=True,
        )

    except ImportError:
        console.print("❌ Gradio not available", style="red")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to start UI: {e}")
        console.print(f"❌ Error: {e}", style="red")
        sys.exit(1)


@app.command()
def evaluate(
    output_dir: Optional[Path] = typer.Option(
        None, "--output-dir", help="Output directory for evaluation results"
    ),
    run_retrieval: bool = typer.Option(True, "--retrieval", help="Run retrieval evaluation"),
    run_llm: bool = typer.Option(True, "--llm", help="Run LLM evaluation"),
):
    """Run evaluation suite for retrieval and LLM approaches."""
    try:
        pipeline = RAGPipeline()
        
        if output_dir is None:
            output_dir = pipeline.config.artifacts_dir / "evaluations"
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        console.print("🔬 Starting evaluation suite...")
        
        if run_retrieval:
            console.print("📊 Evaluating retrieval approaches...")
            from ..evaluation.retrieval_evaluator import RetrievalEvaluator
            
            retrieval_evaluator = RetrievalEvaluator(pipeline.vector_store, pipeline.encoder)
            retrieval_results = retrieval_evaluator.run_evaluation_suite(output_dir)
            
            best_approach = retrieval_results["summary"]["best_approach"]
            best_k = retrieval_results["summary"]["best_k"]
            console.print(f"✅ Best retrieval: {best_approach} with k={best_k}")
        
        if run_llm:
            console.print("🤖 Evaluating LLM approaches...")
            from ..evaluation.llm_evaluator import LLMEvaluator
            
            llm_evaluator = LLMEvaluator(pipeline.vector_store, pipeline.encoder)
            llm_results = llm_evaluator.run_evaluation_suite(output_dir)
            
            best_model = llm_results["summary"]["best_model"]
            best_prompt = llm_results["summary"]["best_prompt"]
            console.print(f"✅ Best LLM: {best_model} with {best_prompt}")
        
        console.print(f"📋 Evaluation results saved to: {output_dir}")
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        console.print(f"❌ Error: {e}", style="red")
        sys.exit(1)


@app.command()
def ingest_job(
    urls: list[str] = typer.Argument(..., help="YouTube URLs to add to ingestion queue"),
):
    """Add URLs to automated ingestion queue."""
    try:
        from ..ingestion.automated_pipeline import AutomatedIngestionPipeline
        
        pipeline = AutomatedIngestionPipeline()
        job_id = pipeline.add_job(urls)
        
        console.print(f"✅ Added ingestion job: {job_id}")
        console.print(f"📝 URLs queued: {len(urls)}")
        
    except Exception as e:
        logger.error(f"Failed to add ingestion job: {e}")
        console.print(f"❌ Error: {e}", style="red")
        sys.exit(1)


@app.command()
def run_ingestion(
    job_id: Optional[str] = typer.Option(None, "--job-id", help="Specific job ID to run"),
    all_pending: bool = typer.Option(False, "--all", help="Run all pending jobs"),
):
    """Run ingestion jobs."""
    try:
        from ..ingestion.automated_pipeline import AutomatedIngestionPipeline
        
        pipeline = AutomatedIngestionPipeline()
        
        if job_id:
            console.print(f"🔄 Running job: {job_id}")
            result = pipeline.run_job(job_id)
            console.print(f"✅ Job status: {result['status']}")
            
        elif all_pending:
            console.print("🔄 Running all pending jobs...")
            results = pipeline.run_pending_jobs()
            console.print(f"✅ Processed {results['processed']} jobs")
            
        else:
            console.print("❌ Specify --job-id or --all", style="red")
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        console.print(f"❌ Error: {e}", style="red")
        sys.exit(1)


@app.command()
def ingestion_status(
    status_filter: Optional[str] = typer.Option(None, "--status", help="Filter by status"),
):
    """Show ingestion pipeline status."""
    try:
        from ..ingestion.automated_pipeline import AutomatedIngestionPipeline
        
        pipeline = AutomatedIngestionPipeline()
        stats = pipeline.get_pipeline_stats()
        jobs = pipeline.list_jobs(status_filter)
        
        # Stats table
        stats_table = Table(title="Ingestion Pipeline Stats")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="green")
        
        stats_table.add_row("Total Jobs", str(stats["total_jobs"]))
        stats_table.add_row("Completed", str(stats["completed_jobs"]))
        stats_table.add_row("Failed", str(stats["failed_jobs"]))
        stats_table.add_row("Pending", str(stats["pending_jobs"]))
        stats_table.add_row("Success Rate", f"{stats['success_rate']:.2%}")
        stats_table.add_row("URLs Processed", str(stats["total_urls_processed"]))
        stats_table.add_row("Collection Size", str(stats["collection_size"]))
        
        console.print(stats_table)
        
        # Jobs table
        if jobs:
            jobs_table = Table(title=f"Jobs {f'({status_filter})' if status_filter else ''}")
            jobs_table.add_column("Job ID", style="cyan")
            jobs_table.add_column("Status", style="green")
            jobs_table.add_column("URLs", style="yellow")
            jobs_table.add_column("Created", style="blue")
            
            for job in jobs[-10:]:  # Show last 10 jobs
                created = job["created_at"][:16].replace("T", " ")
                jobs_table.add_row(
                    job["id"],
                    job["status"],
                    str(len(job["urls"])),
                    created
                )
            
            console.print(jobs_table)
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        console.print(f"❌ Error: {e}", style="red")
        sys.exit(1)


@app.command()
def dashboard(
    output_dir: Optional[Path] = typer.Option(None, "--output", help="Output directory for dashboard"),
    open_browser: bool = typer.Option(True, "--open", help="Open dashboard in browser"),
):
    """Generate monitoring dashboard."""
    try:
        pipeline = RAGPipeline()
        
        if output_dir is None:
            output_dir = pipeline.config.artifacts_dir / "monitoring"
        
        output_dir = Path(output_dir)
        
        from ..monitoring.dashboard import MonitoringDashboard
        from ..monitoring.feedback_collector import FeedbackCollector
        
        feedback_db = pipeline.config.artifacts_dir / "feedback.db"
        dashboard = MonitoringDashboard(feedback_db)
        
        dashboard_path = output_dir / "dashboard.html"
        result_path = dashboard.generate_dashboard_html(dashboard_path)
        
        console.print(f"📊 Dashboard generated: {result_path}")
        
        if open_browser:
            import webbrowser
            webbrowser.open(f"file://{dashboard_path.absolute()}")
            console.print("🌐 Opened dashboard in browser")
        
    except Exception as e:
        logger.error(f"Dashboard generation failed: {e}")
        console.print(f"❌ Error: {e}", style="red")
        sys.exit(1)


if __name__ == "__main__":
    app()
