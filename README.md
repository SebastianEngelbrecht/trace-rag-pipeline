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
- **LLM Generation:** Injecting searched context into Gemini models using the `genai` SDK
- **REST API:** A FastAPI backend allowing background initiation of crawl jobs, and searching your vector store.
- **Structured Logging:** Centralized structlog configuration emitting structured logs (ConsoleRenderer by default; JSON rendering can be enabled for service deployments).

## Architecture & Project Structure

The project encompasses tools for both offline data ingestion and live querying handled through a unified FastAPI application. See more details in the [Architecture & Guide](docs/GUIDE.md).

```text
fontend/                 Vite React Application
  src/                   Frontend components and views (TypeScript/Tailwind)
src/
  main.py                Application entry point for the FastAPI server
  api/
    routes.py            FastAPI REST endpoints and WebSocket ingestion logic
  config/
    settings.py          Pydantic settings loading from `.env`
    logger.py            Structlog structured logging configuration
  database/
    chroma_manager.py    ChromaDB vector store integration
  embedding/
    gemini.py            Batch embedding generation
  generation/
    engine.py            Retrieval-Augmented Generation execution logic
  ingestion/
    crawler.py           Async Playwright crawler
    chunker.py           Text cleaning and chunk generation
Makefile                 Developer execution shortcuts
docker-compose.yml       Container orchestration configuration
Dockerfile               Production backend image build instruction
```

For more details on the design, see the documentation in `docs/`.

## Requirements

- Docker and Docker Compose (Recommended for isolated execution)
- Python 3.12+ (For local development)
- `uv` for environment and dependency management
- Playwright browser binaries for crawling
- A Gemini API Key

## Setup & Execution

### Environment Variables

1. Create frontend and backend `.env` files:
   - For backend `.env` in the root:
   ```env
   GEMINI_API_KEY="your_api_key_here"
   LOG_LEVEL="INFO" 
   ```
   - For frontend `frontend/.env`:
   ```env
   VITE_API_BASE_URL="http://localhost:8000"
   ```

### Option 1: Docker (Recommended)

1. Build and start the containerized backend and frontend (if configured in docker-compose):
   ```bash
   make build
   make up
   ```
   If using the React frontend locally with Docker backend, the FastAPI server will run on `http://localhost:8000/docs`. The local `data/` directory will mount persistently for ChromaDB.

### Option 2: Local Development

First, initialize the Python environment and install the backend dependencies using `uv` via the provided Makefile command:
```bash
make install
```

Then, install the React frontend dependencies via npm (or use the provided Makefile shortcut):
```bash
make front-install
```

## Usage

### Using the Dedicated Frontend React UI

The application backend exposes REST and WebSocket APIs. The primary way to interact with the pipeline is via the dedicated frontend React application.

From the root project folder, you can boot both the FastAPI hot-reloading server and the Vite React development server:

**Terminal 1 (Backend):**
```bash
make dev
```

**Terminal 2 (Frontend):**
```bash
make front-dev
```

The Web UI dashboard will run locally at `http://localhost:5173/`. You can visit `http://localhost:8000/docs` to interact with the auto-generated backend API Swagger documentation.

For complete details on using the interactive UI, executing crawl pipelines, and running RAG requests, refer to the [System Guide](docs/GUIDE.md).

## Contributing

For guidelines on how to contribute to this repository, please see our [Contributing Guide](docs/CONTRIBUTING.md).
