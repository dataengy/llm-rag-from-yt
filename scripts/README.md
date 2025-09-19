# Scripts Directory

This directory contains testing and demonstration scripts for the LLM RAG YouTube Audio Processing system.

## Available Scripts

### 1. test_full_pipeline.py
**Purpose**: Comprehensive system test for all evaluation criteria
**Usage**: 
```bash
python scripts/test_full_pipeline.py
```
**Features**:
- Tests all core functionality
- Validates evaluation and monitoring systems
- Checks advanced search features
- Provides system status overview

### 2. test_philosophical_rag.py ⭐ NEW
**Purpose**: Interactive test for philosophical podcast content
**Target File**: `data/audio/Философская беседа ｜ Юрий Вафин ｜ подкаст.mp3`
**Usage**:
```bash
python scripts/test_philosophical_rag.py
```

**Features**:
- **Predefined Test Questions**: 16 curated philosophical questions in Russian
- **Interactive User Input**: Real-time question processing
- **Advanced Search Methods**: 
  - Standard RAG
  - Hybrid search (`hybrid: your question`)
  - Query rewriting (`rewrite: your question`)
- **Performance Metrics**: Response timing and relevance scoring
- **Feedback Collection**: User rating system with SQLite storage
- **Persistent Data**: Uses existing ChromaDB storage

**Question Categories**:
1. **Основные темы** (Main Topics) - 4 questions
2. **Участники и мнения** (Participants & Opinions) - 4 questions  
3. **Философские концепции** (Philosophical Concepts) - 4 questions
4. **Практические выводы** (Practical Conclusions) - 4 questions

**Interactive Commands**:
- `test` - Show predefined questions
- `hybrid: [question]` - Use hybrid search
- `rewrite: [question]` - Use query rewriting
- `stats` - Show feedback statistics
- `exit` - Exit session

## Prerequisites

### Required Dependencies
```bash
# Install ML dependencies for full functionality
uv sync --extra ml

# Or install specific packages
pip install sentence-transformers torch plotly pandas
```

### Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Add OpenAI API key for LLM features
export OPENAI_API_KEY="your_key_here"
```

### Audio File
Ensure the philosophical podcast file exists:
```
data/audio/Философская беседа ｜ Юрий Вафин ｜ подкаст.mp3
```

## Example Usage

### Quick System Test
```bash
# Test all components
python scripts/test_full_pipeline.py
```

### Philosophical Content Testing
```bash
# Start interactive philosophical RAG testing
python scripts/test_philosophical_rag.py

# Choose mode:
# 1. Predefined tests (automated)
# 2. Interactive session (user input)
# 3. Both modes

# Example interaction:
# Ваш вопрос: О чем говорит Юрий Вафин в подкасте?
# hybrid: Какие философские идеи обсуждаются?
# rewrite: Что можно узнать из этой беседы?
```

## Expected Output

### Philosophical Test Results
- **Processing**: Audio transcription and chunking status
- **Query Results**: Answers with source references
- **Performance**: Response times and relevance scores
- **Feedback**: User ratings and statistics
- **Search Methods**: Comparison of different approaches

### System Validation
- **Collection Status**: Document count and storage info
- **Search Capabilities**: Hybrid, rewriting, re-ranking demos
- **Monitoring**: Feedback collection and dashboard generation
- **Evaluation**: Multi-approach testing results

## Troubleshooting

### Common Issues
1. **Import Errors**: Install ML dependencies with `uv sync --extra ml`
2. **Missing Audio**: Ensure MP3 file exists in `data/audio/`
3. **OpenAI Errors**: Set `OPENAI_API_KEY` environment variable
4. **Python Version**: Requires Python <3.13 for PyTorch compatibility

### Debug Mode
```bash
# Run with verbose output
PYTHONPATH=src python scripts/test_philosophical_rag.py
```

## Integration with Main System

These scripts integrate with the full RAG pipeline:
- **Pipeline**: Uses main `RAGPipeline` class
- **Storage**: Persistent ChromaDB vector store
- **Search**: Advanced hybrid and rewriting features
- **Monitoring**: Feedback collection and analytics
- **Evaluation**: Multi-approach testing framework