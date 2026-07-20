from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Enterprise RAG Pipeline"
    
    # Embedding/AI Models
    GEMINI_API_KEY: str
    EMBEDDING_MODEL: str = "gemini-embedding-2"
    CHAT_MODEL: str = "gemini-3.1-flash-lite"
    
    # Vector Database Configuration
    CHROMA_DB_DIR: str = "./chroma_store"
    
    # Crawler Configuration (You can move crawler parameters here too!)
    MAX_CRAWL_DEPTH: int = 3
    MAX_CONCURRENCY: int = 5
    

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

