import pytest
from src.config.settings import Settings

def test_settings_load_defaults():
    # Attempting to init Settings without .env usually uses defaults or fails on required.
    # Since GEMINI_API_KEY is required and has no default, this should raise a Validation error
    # if env is totally empty. We'll mock the env file for a clean test.
    from pydantic import ValidationError
    
    with pytest.raises(ValidationError):
        # We temporarily clear out the env override just to prove validation catches missing keys.
        import os
        if "GEMINI_API_KEY" in os.environ:
            del os.environ["GEMINI_API_KEY"]
            
        Settings(
            _env_file=None, # Don't load actual .env
        )

def test_settings_custom_values():
    settings = Settings(
        GEMINI_API_KEY="test_key_123",
        PROJECT_NAME="Test RAG",
        CHROMA_DB_DIR="./test_chroma",
        MAX_CRAWL_DEPTH=10
    )
    
    assert settings.GEMINI_API_KEY == "test_key_123"
    assert settings.PROJECT_NAME == "Test RAG"
    assert settings.MAX_CRAWL_DEPTH == 10
    assert settings.MAX_CONCURRENCY == 5 # Default value should remain

def test_settings_project_root_logic():
    from src.config.settings import ROOT_DIR, ENV_PATH
    # Verify the paths resolve to actual paths rather than empty strings
    assert str(ROOT_DIR).endswith("trace-rag-pipeline")
    assert str(ENV_PATH).endswith(".env")