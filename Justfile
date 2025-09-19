# Justfile for LLM RAG YouTube Processing System
# Use `just <command>` to run commands

set dotenv-load := true

# Default recipe - show available commands
default:
    @just --list

# Environment and setup commands
install:
    @echo "📦 Installing dependencies..."
    uv sync --extra ml

install-dev:
    @echo "📦 Installing development dependencies..."
    uv sync --extra ml --extra dev

setup:
    @echo "🔧 Setting up project..."
    mkdir -p data/dagster data/audio data/chroma_db logs artifacts
    cp .env.example .env
    @echo "✅ Project setup complete. Edit .env file with your configuration."

# Core services
api:
    #!/bin/bash
    echo "🚀 Starting FastAPI server..."
    uv run llm-rag-yt serve-api

ui:
    @echo "🎨 Starting Gradio UI..."
    uv run llm-rag-yt serve-ui

bot:
    @echo "🤖 Starting Telegram bot..."
    uv run llm-rag-yt bot start

dagster:
    @echo "⚙️ Starting Dagster development server..."
    uv run llm-rag-yt dagster dev

worker:
    @echo "👷 Starting background worker..."
    @echo "⚠️  No dedicated worker command found. Use 'just dagster' for pipeline processing."
    # uv run llm-rag-yt worker

# Docker services
docker-build:
    @echo "🐳 Building Docker images..."
    docker compose build

docker-up:
    @echo "🐳 Starting all services with Docker..."
    docker compose up -d

docker-down:
    @echo "🐳 Stopping all Docker services..."
    docker compose down

docker-logs service="":
    @echo "📋 Showing Docker logs..."
    @if [ "{{service}}" = "" ]; then \
        docker compose logs -f; \
    else \
        docker compose logs -f {{service}}; \
    fi

# Monitoring stack
monitoring-up:
    #!/bin/bash
    echo "📊 Starting monitoring stack..."
    docker compose up -d prometheus grafana node-exporter pushgateway alertmanager

monitoring-down:
    @echo "📊 Stopping monitoring stack..."
    docker compose stop prometheus grafana node-exporter pushgateway alertmanager

grafana:
    @echo "📈 Opening Grafana dashboard..."
    @echo "🌐 Grafana URL: http://localhost:3001"
    @echo "👤 Username: admin | Password: admin"

prometheus:
    @echo "🔍 Opening Prometheus..."
    @echo "🌐 Prometheus URL: http://localhost:9090"

# Database and storage
chroma-reset:
    @echo "🗑️ Resetting ChromaDB..."
    rm -rf data/chroma_db/*
    @echo "✅ ChromaDB reset complete"

db-reset:
    @echo "🗑️ Resetting SQLite database..."
    rm -f data/llm_rag_yt.db
    @echo "✅ Database reset complete"

# Testing and development
test:
    @echo "🧪 Running tests..."
    uv run pytest tests/ -v

test-unit:
    @echo "🧪 Running unit tests..."
    uv run pytest tests/ -v -k "not integration"

test-integration:
    @echo "🧪 Running integration tests..."
    uv run pytest tests/ -v -k "integration"

test-pipeline:
    @echo "🧪 Testing full pipeline..."
    uv run python scripts/test_full_pipeline.py

test-rag:
    @echo "🧪 Testing RAG system..."
    uv run python scripts/test_philosophical_rag.py

demo:
    @echo "🎬 Running enhanced RAG demo..."
    uv run python src/user_testing/rag_demo.py

# Code quality
lint:
    @echo "🔍 Running linter..."
    uv run ruff check src/ tests/

format:
    @echo "🎨 Formatting code..."
    uv run ruff format src/ tests/

check: lint
    @echo "✅ Code quality check complete"

# Dagster operations
dagster-jobs:
    @echo "📋 Listing Dagster jobs..."
    uv run llm-rag-yt dagster list-jobs

dagster-assets:
    @echo "📋 Listing Dagster assets..."
    uv run llm-rag-yt dagster list-assets

dagster-run job:
    @echo "▶️ Running Dagster job: {{job}}"
    uv run llm-rag-yt dagster run-job {{job}}

dagster-materialize asset:
    @echo "🏗️ Materializing asset: {{asset}}"
    uv run llm-rag-yt dagster materialize-asset {{asset}}

dagster-sensors:
    @echo "📡 Showing sensor status..."
    uv run llm-rag-yt dagster sensor-status

# Telegram bot operations
bot-status:
    @echo "📊 Showing bot status..."
    uv run llm-rag-yt bot status

bot-users:
    @echo "👥 Listing bot users..."
    uv run llm-rag-yt bot list-users

bot-alerts:
    @echo "🚨 Showing bot alerts..."
    uv run llm-rag-yt bot alerts

bot-cleanup:
    @echo "🧹 Cleaning up bot data..."
    uv run llm-rag-yt bot cleanup

bot-add-url url:
    @echo "➕ Adding YouTube URL to bot queue..."
    uv run llm-rag-yt bot add-url "{{url}}"

# System utilities
logs:
    @echo "📋 Showing application logs..."
    tail -f logs/*.log

clean:
    @echo "🧹 Cleaning up temporary files..."
    find . -type f -name "*.pyc" -delete
    find . -type d -name "__pycache__" -delete
    find . -type d -name "*.egg-info" -exec rm -rf {} +
    rm -rf .pytest_cache/
    @echo "✅ Cleanup complete"

clean-all: clean chroma-reset db-reset
    @echo "🧹 Deep cleaning..."
    rm -rf data/dagster/* logs/* artifacts/logs/*
    @echo "✅ Deep cleanup complete"

# Development workflows
dev: install-dev setup
    @echo "🚀 Starting development environment..."
    @echo "Run 'just dev-services' to start core services"

dev-services:
    @echo "🚀 Starting development services..."
    @echo "Starting services in separate terminals..."
    @echo "1. API: just api"
    @echo "2. UI: just ui" 
    @echo "3. Bot: just bot"
    @echo "4. Dagster: just dagster"

dev-stop:
    @echo "🛑 Stopping development services..."
    pkill -f "llm-rag-yt"

# Production workflows
prod-up: docker-build docker-up monitoring-up
    @echo "🚀 Production environment started"
    @echo "🌐 Services:"
    @echo "  • API: http://localhost:8000"
    @echo "  • UI: http://localhost:7860"
    @echo "  • Grafana: http://localhost:3001"
    @echo "  • Prometheus: http://localhost:9090"

prod-down: docker-down monitoring-down
    @echo "🛑 Production environment stopped"

prod-logs: docker-logs

prod-status:
    @echo "📊 Production status..."
    docker compose ps

# Backup and restore
backup:
    @echo "💾 Creating backup..."
    tar -czf backup-$(date +%Y%m%d-%H%M%S).tar.gz data/ logs/ artifacts/
    @echo "✅ Backup created"

restore backup_file:
    @echo "📦 Restoring from backup: {{backup_file}}"
    tar -xzf {{backup_file}}
    @echo "✅ Restore complete"

# Health checks
health:
    @echo "🏥 Checking system health..."
    @echo "API: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health || echo 'DOWN')"
    @echo "UI: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:7860 || echo 'DOWN')"
    @echo "Grafana: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:3001 || echo 'DOWN')"
    @echo "Prometheus: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:9090 || echo 'DOWN')"

# Individual service health checks
api-health:
    @echo "🔍 Checking API health..."
    @echo "API endpoint: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health || echo 'DOWN')"
    -@uv run llm-rag-yt status 2>/dev/null || echo "API service not running"

ui-health:
    @echo "🎨 Checking UI health..."
    @echo "UI endpoint: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:7860 || echo 'DOWN')"

bot-health:
    @echo "🤖 Checking bot health..."
    -@uv run llm-rag-yt bot status 2>/dev/null || echo "Bot service error"

dagster-health:
    @echo "⚙️ Checking Dagster health..."
    @echo "Dagster endpoint: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:3000 || echo 'DOWN')"
    -@uv run llm-rag-yt dagster sensor-status 2>/dev/null || echo "Dagster service not running"

worker-health:
    @echo "👷 Checking worker health..."
    @echo "⚠️  Worker uses Dagster pipeline - checking Dagster sensors..."
    -@uv run llm-rag-yt dagster sensor-status 2>/dev/null || echo "Dagster sensors not available"

# Docker service health checks
docker-health:
    @echo "🐳 Checking Docker services health..."
    docker compose ps --format "table {{"{{"}}.Name}}\t{{"{{"}}.Status}}\t{{"{{"}}.Ports}}"

# Monitoring service health checks
monitoring-health:
    @echo "📊 Checking monitoring services health..."
    @echo "Prometheus: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:9090/api/v1/targets || echo 'DOWN')"
    @echo "Grafana: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:3001/api/health || echo 'DOWN')"
    @echo "Node Exporter: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:9100/metrics || echo 'DOWN')"

# Comprehensive health check for all services
health-all: api-health ui-health bot-health dagster-health worker-health docker-health monitoring-health
    @echo "✅ Comprehensive health check complete"

# Documentation
docs:
    @echo "📚 Available documentation:"
    @echo "  • README.md - Project overview"
    @echo "  • docs/API.md - API documentation"
    @echo "  • docs/TELEGRAM-BOT.md - Bot usage guide"
    @echo "  • docs/DAGSTER-PIPELINE.md - Pipeline documentation"

# Metrics and monitoring
metrics:
    @echo "📊 Current metrics:"
    @echo "ChromaDB size: $(du -sh data/chroma_db/ 2>/dev/null | cut -f1 || echo 'N/A')"
    @echo "Logs size: $(du -sh logs/ 2>/dev/null | cut -f1 || echo 'N/A')"
    @echo "Database size: $(du -sh data/llm_rag_yt.db 2>/dev/null | cut -f1 || echo 'N/A')"

# Quick commands for common workflows
quick-start: install setup api
    @echo "🚀 Quick start complete - API running on http://localhost:8000"

quick-demo: install demo
    @echo "🎬 Demo complete"

quick-test: test-unit test-pipeline
    @echo "🧪 Quick test complete"