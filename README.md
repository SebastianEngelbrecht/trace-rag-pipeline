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
- **Structured Logging:** Centralized structlog configuration emitting structured logs (ConsoleRenderer by default; JSON rendering can be enabled for service deployments).

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
Makefile                   Developer execution shortcuts
docker-compose.yml         Container orchestration configuration
Dockerfile                 Production image build instruction
```

For more details on the design, see the documentation in `docs/`.

## Requirements

- Docker and Docker Compose (Recommended for isolated execution)
- Python 3.12+ (For local development)
- `uv` for environment and dependency management
- Playwright browser binaries for crawling
- A Gemini API Key

## Setup & Execution

### Option 1: Docker (Recommended)

1. Create a `.env` file in the root of the project with your API keys:
   ```env
   GEMINI_API_KEY="your_api_key_here"
   LOG_LEVEL="INFO" 
   ```
2. Build and start the containerized backend:
   ```bash
   make build
   make up
   ```
   The FastAPI server will now be running on `http://127.0.0.1:8000/docs`, and the local `data/` directory will mount persistently for ChromaDB.

### Option 2: Local Development

First, initialize the environment and install dependencies using `uv` via the provided Makefile command:
```bash
make install
```
*(This triggers `uv sync` and installs the required chromium browser for the crawler.)*

Finally, define your environment variables. Create a `.env` file in the root of the project:

```env
GEMINI_API_KEY="your_api_key_here"
LOG_LEVEL="INFO" # Optional: DEBUG, INFO, WARNING, ERROR
```

## Usage

### Using the REST API

The recommended way to interact with the system is via the FastAPI backend. You can use the Makefile to start the local server with live-reloading:

```bash
make dev
```

The API will run locally at `http://0.0.0.0:8000`. You can visit `http://127.0.0.1:8000/docs` to interact with the auto-generated Swagger UI.

### Running a Pipeline Test Script

If you want to invoke a quick pipeline smoke test from the CLI (crawls 'example.com', chunks, embeds, and saves to the database), run:

```bash
make run
```

## Contributing

For guidelines on how to contribute to this repository, please see our [Contributing Guide](docs/CONTRIBUTING.md).
