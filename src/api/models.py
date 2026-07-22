from fastapi.templating import Jinja2Templates
from pathlib import Path
from pydantic import BaseModel
from typing import List, Optional

# Set up templates
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

class GenerationResponse(BaseModel):
    answer: str
    chunks: Optional[List[dict]] = None
    prompt: Optional[str] = None
    response_time_ms: Optional[float] = None
    tokens_used: Optional[int] = None
    retrieval_time_ms: Optional[float] = None
