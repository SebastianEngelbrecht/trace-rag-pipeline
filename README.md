# RAGLens: An Observable Production RAG Pipeline

A production-ready Retrieval-Augmented Generation (RAG) pipeline with built-in observability and tracing.

## Overview

This project provides a complete RAG pipeline with components for document ingestion, chunking, and API serving. It leverages LangChain and Playwright for data processing and extraction.

## Project Structure

- `src/main.py`: Main entry point for the application.
- `src/api/`: API endpoints for interacting with the RAG pipeline.
- `src/ingestion/`: Modules for data ingestion.
  - `crawler.py`: Web crawling and document fetching (using Playwright).
  - `chunker.py`: Text splitting and chunking using LangChain.

## Setup

1. Ensure you have Python 3.12 or higher installed.
2. Install the dependencies (e.g., using `pip` or your preferred package manager):

```bash
pip install .
```

If using Playwright for the first time, you may need to install the browsers:

```bash
playwright install
```

## Usage

More details to come as the project evolves.
