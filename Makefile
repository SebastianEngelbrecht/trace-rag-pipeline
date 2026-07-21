.PHONY: install dev run format build up down clean

# Local Development Setup
install:
	uv sync
	uv run playwright install chromium

# Run the FastAPI server in development mode
dev:
	uv run uvicorn src.api.routes:app --reload

# Run the FastAPI server via the Python entry point (no auto-reload)
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

# Frontend specific commands
front-install:
	cd frontend && npm install

front-dev:
	cd frontend && npm run dev

# Frontend specific commands
front-install:
	cd frontend && npm install

front-dev:
	cd frontend && npm run dev

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
