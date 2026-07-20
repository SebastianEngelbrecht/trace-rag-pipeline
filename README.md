# trace-rag-pipeline

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/badge/uv-fast-magenta.svg)](https://docs.astral.sh/uv/)

Prototype ingestion pipeline for a Retrieval-Augmented Generation workflow, centered on crawling web content, splitting text into chunks, and preparing content for Gemini embeddings.

## Overview

This repository is an early-stage RAG pipeline project. The implemented pieces focus on ingestion:

- Crawling site content with Playwright
- Cleaning and chunking extracted text with LangChain text splitters
- Generating embeddings through Gemini

The application entry point is still minimal, and the vector-store integration is not implemented yet.

## Current Status

What exists today:

- A concurrent crawler for collecting page text
- A chunking layer for converting crawled content into embedding-ready records
- A Gemini embedding utility for batched vector generation

What is not wired yet:

- A complete end-to-end pipeline entry point
- Persistent vector database storage
- API endpoints

## Project Structure

```text
src/
  main.py                  Minimal application entry point
  config/                  Project configuration
  database/                Future vector-store integration
  embedding/               Gemini embedding utilities
  ingestion/
    crawler.py             Async Playwright crawler
    chunker.py             Text cleaning and chunk generation
```

## Requirements

- Python 3.12+
- `uv` for environment and dependency management
- Playwright browser binaries for crawling

## Setup

Install dependencies:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync
```

Install Playwright browsers:

```bash
uv run playwright install
```

## Usage

The repository does not yet expose a complete top-level pipeline command. The current entry point is a stub:

```bash
uv run python src/main.py
```

At the moment, the most practical way to exercise the project locally is by running the ingestion modules directly while the main pipeline is being assembled.

## Development Notes

- The repo is currently organized around ingestion first, orchestration later.
- Expect the main workflow to evolve as database persistence and pipeline wiring are added.
- The empty [docs](docs) directory is available for future architecture notes, examples, or operational guides.

## Roadmap

- Wire the crawler, chunker, and embedding steps together from a real entry point
- Add vector-store persistence
- Add tests and smoke checks for the ingestion path
- Document configuration and example runs
