"""Application entry point for the trace RAG API."""

import sys
from pathlib import Path
import uvicorn

# Ensure src can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.api.routes import app
from src.config.logger import setup_logging
from src.config.settings import get_settings

def main():
    """Start the FastAPI server."""
    # 1. Initialize configuration and logging
    settings = get_settings()
    setup_logging(settings.LOG_LEVEL)
    
    # 2. Run the FastAPI application using uvicorn
    uvicorn.run(
        "src.api.routes:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=settings.DEBUG if hasattr(settings, 'DEBUG') else False
    )

if __name__ == "__main__":
    main()

