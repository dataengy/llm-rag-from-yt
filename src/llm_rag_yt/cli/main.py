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
    config_file: Optional[Path] = typer.Option(None, "--config", help="Config file path"),
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
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Interactive mode"),
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
                
                console.print(f"\n💡 [bold green]Answer:[/bold green] {result['answer']}")
                
                console.print(f"\n📚 [bold blue]Sources:[/bold blue]")
                for i, source in enumerate(result["sources"], 1):
                    source_id = source.get("metadata", {}).get("source_id", "unknown")
                    distance = source.get("distance", 0)
                    console.print(f"  {i}. {source_id} (similarity: {1-distance:.3f})")
                    console.print(f"     {source['text'][:100]}...")
                
                console.print()
        else:
            result = pipeline.query(question, top_k)
            
            console.print(f"💡 [bold green]Answer:[/bold green] {result['answer']}")
            
            console.print(f"\n📚 [bold blue]Sources:[/bold blue]")
            for i, source in enumerate(result["sources"], 1):
                source_id = source.get("metadata", {}).get("source_id", "unknown")
                distance = source.get("distance", 0)
                console.print(f"  {i}. {source_id} (similarity: {1-distance:.3f})")
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


if __name__ == "__main__":
    app()