# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Install system dependencies required for Playwright and uv
RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

# Install `uv` for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set the working directory in the container
WORKDIR /app

# Enable bytecode compilation and disable uv caching for smaller image size
ENV UV_COMPILE_BYTECODE=1
ENV UV_CACHE_DIR=/opt/uv-cache/

# Copy dependency files first (to leverage Docker layer caching)
COPY pyproject.toml uv.lock ./

# Install python dependencies. 
# This creates a local .venv inside /app/
RUN uv sync --no-dev

# Activate the virtual environment in the container by updating the PATH
ENV PATH="/app/.venv/bin:$PATH"

# Install Playwright browsers and OS-level dependencies (only Chromium to keep image size reasonable)
RUN playwright install --with-deps chromium

# Copy the rest of the application code
COPY src/ ./src/

# Expose the API port
EXPOSE 8000

# Set default start command to the FastAPI entry point
CMD ["uvicorn", "src.api.routes:app", "--host", "0.0.0.0", "--port", "8000"]
