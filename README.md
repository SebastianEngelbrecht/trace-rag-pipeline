# RAGLens: An Observable Production RAG Pipeline

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/badge/uv-fast-magenta.svg)](https://docs.astral.sh/uv/)

A production-ready Retrieval-Augmented Generation (RAG) pipeline with built-in observability and tracing.

## 📖 Overview

This project provides a complete RAG pipeline with components for document ingestion, chunking, and API serving. It leverages LangChain and Playwright for reliable data processing, extraction, and vectorization, with a strong focus on observing and tracing the generation process.

## 📂 Project Structure

- `src/main.py`: Main entry point for the application.
- `src/api/`: API endpoints for interacting with the RAG pipeline.
- `src/ingestion/`: Modules for data ingestion.
  - `crawler.py`: Web crawling and document fetching utilizing Playwright.
  - `chunker.py`: Text splitting and structural chunking using LangChain.

## 🚀 Setup & Installation

1. Ensure you have Python 3.12 or higher installed. We recommend using `uv` for dependency management.

2. Install the dependencies using `uv` (as indicated by the `uv.lock` file):

```bash
# To install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies 
uv sync
```

3. Install Playwright browsers (required for the web crawler):

```bash
uv run playwright install
```

## 💻 Usage

*(Detailed usage instructions and API documentation will be added as the project evolves.)*

### Running the pipeline

```bash
uv run python src/main.py
```
