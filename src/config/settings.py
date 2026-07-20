"""
Configuration Management Settings

STEP 1: Install required packages
Run the following command in your terminal to install Pydantic for settings management:
    pip install pydantic pydantic-settings python-dotenv

STEP 2: Create a .env file
Create a file named `.env` in the root of your project (trace-rag-pipeline/.env).
Add your secret keys and configurations there, for example:
    GEMINI_API_KEY=your_real_api_key_here
    CHROMA_DB_DIR=./chroma_data

STEP 3: Define your Settings Model
Uncomment and use the Pydantic BaseSettings class below. BaseSettings will automatically 
read the .env file and validate that your environment variables are correct.
"""
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

