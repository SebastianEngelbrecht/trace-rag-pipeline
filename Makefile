.PHONY: install dev run format build up down clean

# Local Development Setup
install:
	uv sync
	uv run playwright install chromium

# Run the FastAPI server in development mode
dev:
	uv run uvicorn src.api.routes:app --reload

# Run the standalone ingestion pipeline script
run:
	uv run python src/main.py

# Format code (assuming you use ruff)
format:
	uv run ruff check --fix src/
	uv run ruff format src/

# -- Docker Commands --

# Build the docker image
build:
	docker compose build

# Start the cluster in the background
up:
	docker compose up -d

# View logs
logs:
	docker compose logs -f

# Stop the cluster
down:
	docker compose down

# Clean up local environment
clean:
	rm -rf .venv
	find . -type d -name "__pycache__" -exec rm -rf {} +
