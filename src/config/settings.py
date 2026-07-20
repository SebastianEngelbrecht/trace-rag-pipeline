from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Ensure we always look for .env in the project root, regardless of where python is executed from!
ROOT_DIR = Path(__file__).parent.parent.parent
ENV_PATH = ROOT_DIR / ".env"

class Settings(BaseSettings):
    PROJECT_NAME: str = "Enterprise RAG Pipeline"
    
    # Embedding/AI Models
    GEMINI_API_KEY: str
    EMBEDDING_MODEL: str = "gemini-embedding-2"
    CHAT_MODEL: str = "gemini-3.1-flash-lite"
    
    # Vector Database Configuration
    # TODO: Currently using local disk storage for testing & prototyping.
    # After testing is complete and we need to scale, migrate to a managed vector DB like Pinecone.
    CHROMA_DB_DIR: str = str(ROOT_DIR / "data" / "knowledge_base")
    
    # Crawler Configuration
    MAX_CRAWL_DEPTH: int = 3
    MAX_CONCURRENCY: int = 5
    
    # Pydantic v2 config standard
    # Provide the absolute path string so Pydantic knows exactly where to look
    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH), 
        env_file_encoding="utf-8", 
        extra="ignore"
    )

settings = Settings()

