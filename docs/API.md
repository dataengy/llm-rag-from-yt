# API Documentation

## FastAPI Server

Start the API server:
```bash
uv run llm-rag-yt serve-api --host 0.0.0.0 --port 8000
```

### Endpoints

#### Health Check
- **GET** `/health`
- Returns server health and collection info

#### Process YouTube URLs
- **POST** `/process`
- Body:
```json
{
  "urls": ["https://youtube.com/watch?v=..."],
  "use_fake_asr": false,
  "language": "ru"
}
```

#### Query RAG System
- **POST** `/query`
- Body:
```json
{
  "question": "Your question here",
  "top_k": 3,
  "system_prompt": "Optional custom prompt"
}
```

#### Get Status
- **GET** `/status`
- Returns pipeline status and configuration

## Gradio UI

Start the Gradio interface:
```bash
uv run llm-rag-yt serve-ui --host 0.0.0.0 --port 7860
```

Features:
- **Process Audio Tab**: Download and process YouTube content
- **Ask Questions Tab**: Query the RAG system
- **Status Tab**: View system status and collection info

## CLI Interface

### Commands

```bash
# Process YouTube URLs
uv run llm-rag-yt process "https://youtube.com/watch?v=..." --language ru

# Query the system
uv run llm-rag-yt query "Your question here" --top-k 5

# Interactive query mode
uv run llm-rag-yt query "Initial question" --interactive

# Check status
uv run llm-rag-yt status

# Start servers
uv run llm-rag-yt serve-api --port 8000
uv run llm-rag-yt serve-ui --port 7860
```

### Options

- `--fake-asr`: Use fake ASR for testing (faster)
- `--language`: Language code (ru, en, auto)
- `--top-k`: Number of similar documents to retrieve
- `--interactive`: Enter interactive query mode

## Environment Setup

Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
```

Required environment variables:
- `OPENAI_API_KEY`: Your OpenAI API key

Optional variables:
- `ASR_MODEL`: Whisper model name (default: large-v3)
- `EMBEDDING_MODEL`: Sentence transformer model
- `DEVICE`: Processing device (auto, cpu, cuda)