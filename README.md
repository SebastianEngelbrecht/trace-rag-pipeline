# Trace RAG Pipeline

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/badge/uv-fast-magenta.svg)](https://docs.astral.sh/uv/)

Prototype ingestion pipeline for a Retrieval-Augmented Generation workflow. This robust backend crawls web content, splits text into chunks, generates Gemini embeddings, and allows for vector similarity searches against a persistent ChromaDB instance. 

## Overview

This complete ingestion and retrieval pipeline supports the following capabilities:

- **Web Crawling:** Concurrent extraction of text from target sites Using Playwright
- **Text Chunking:** Cleaning and chunking of text using LangChain recursive text splitters
- **Embeddings:** Generating embeddings using the native `google-genai` Gemini Client
- **Vector Store:** Local persistence of embeddings and metadata using ChromaDB
- **REST API:** A FastAPI backend allowing background initiation of crawl jobs, and searching your vector store.
- **Structured Logging:** Centralized structlog configurations emitting contextual JSON pipelines.

## Architecture & Project Structure

The project encompasses tools for both offline data ingestion and live querying:

```text
src/
  main.py                  Standalone testing script for the full pipeline
  api/
    routes.py              FastAPI server entry point & REST endpoints
  config/
    settings.py            Pydantic settings loading from `.env`
    logger.py              Structlog structured logging configuration
  database/
    chroma_manager.py      ChromaDB vector store integration
  embedding/
    gemini.py              Batch embedding generation
  ingestion/
    crawler.py             Async Playwright crawler
    chunker.py             Text cleaning and chunk generation
```

For more details on the design, see the documentation in `docs/`.

## Requirements

- Python 3.12+
- `uv` for environment and dependency management
- Playwright browser binaries for crawling
- A Gemini API Key

## Setup

First, initialize the environment and install dependencies using `uv`:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync
```

Next, ensure Playwright browsers are installed:

```bash
uv run playwright install
```

Finally, define your environment variables. Create a `.env` file in the root of the project:

```env
GEMINI_API_KEY="your_api_key_here"
LOG_LEVEL="INFO" # Optional: DEBUG, INFO, WARNING, ERROR
```

## Usage

### Using the REST API

The recommended way to interact with the system is via the FastAPI backend. Start the server:

```bash
uv run uvicorn src.api.routes:app --reload
```

The API will run locally at `http://0.0.0.0:8000`. You can visit `http://127.0.0.1:8000/docs` to interact with the auto-generated Swagger UI.

### Running a Pipeline Test Script

If you want to invoke a quick pipeline smoke test from the CLI (crawls 'example.com', chunks, embeds, and saves to the database), run:

```bash
uv run python src/main.py
```

## Contributing

For guidelines on how to contribute to this repository, please see our [Contributing Guide](docs/CONTRIBUTING.md).
