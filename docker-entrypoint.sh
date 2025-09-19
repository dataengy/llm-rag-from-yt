#!/bin/bash
set -e

# Function to wait for ChromaDB to be ready
wait_for_chroma() {
    echo "Waiting for ChromaDB to be ready..."
    while ! nc -z chroma 8000 2>/dev/null; do
        sleep 1
    done
    echo "ChromaDB is ready!"
}

case "$1" in
    api)
        echo "Starting FastAPI server..."
        wait_for_chroma
        uv run python -m llm_rag_yt.api.server
        ;;
    ui)
        echo "Starting Gradio UI..."
        wait_for_chroma
        uv run llm-rag-yt serve-ui --host 0.0.0.0
        ;;
    cli)
        echo "Starting CLI mode..."
        shift
        uv run llm-rag-yt "$@"
        ;;
    worker)
        echo "Starting ingestion worker..."
        wait_for_chroma
        uv run llm-rag-yt run-ingestion --all
        ;;
    *)
        echo "Usage: $0 {api|ui|cli|worker}"
        echo "  api    - Start FastAPI server"
        echo "  ui     - Start Gradio UI"
        echo "  cli    - Run CLI commands"
        echo "  worker - Start ingestion worker"
        exit 1
        ;;
esac