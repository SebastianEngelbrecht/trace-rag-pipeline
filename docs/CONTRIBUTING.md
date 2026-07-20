# Contributing to Trace RAG Pipeline

We welcome contributions to the Trace RAG Pipeline project! This document provides guidelines for contributing to this repository.

## Development Environment Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-org/trace-rag-pipeline.git
   cd trace-rag-pipeline
   ```

2. **Set up the environment with `uv`:**
   We strictly use `uv` for package management and environment isolation. Ensure it is installed.
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   uv sync
   uv run playwright install
   ```

3. **Configure Environment Variables:**
   A `.env` file is required for development.
   ```env
   GEMINI_API_KEY="your-development-api-key"
   # Optional overrides:
   # CHROMA_DB_DIR="./chroma_store"
   # MAX_CRAWL_DEPTH=3
   # MAX_CONCURRENCY=5
   ```

## Development Guidelines

- **Formatting & Linting:** Please ensure your code follows standard PEP 8 styling conventions. We recommend using `ruff` or `black` for formatting before opening a PR.
- **Dependency Management:** Whenever adding a new dependency, please add it strictly via `pyproject.toml` and use `uv sync` to lock dependencies.
- **Type Hinting:** We encourage strict type hinting across all Python files (`def function(name: str) -> None:`).

## Pull Request Process

1. Create a descriptive branch name (`feature/add-new-embedder` or `bugfix/fix-chunking-error`).
2. Ensure you have tested your code locally using the `src/main.py` entry point.
3. If new REST endpoints were added, please update the main `README.md` and/or any architecture documentation in `/docs`.
4. Open a pull request against the `main` branch. Provide clear details on what was fixed or implemented.

Thank you for contributing!