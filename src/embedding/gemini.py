import sys
from pathlib import Path

# Add project root to Python path so 'src' can be imported when running as a script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import google.genai as genai
from src.config.settings import get_settings
from src.config.logger import get_logger
from tenacity import retry, wait_exponential, stop_after_attempt

logger = get_logger(__name__)

class GeminiEmbedder:
    def __init__(self, model_name: str | None = None):
        settings = get_settings()
        self.model_name = model_name or settings.EMBEDDING_MODEL
        # Initialize the Client lazily per-instance to allow tests to run without API keys
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def count_tokens(self, texts: list[str]) -> list[int]:
        """Gets exact token counts for a list of texts using the Gemini API.
        
        Because count_tokens groups all items into a single total, we process
        each text individually to get chunk-specific counts.
        """
        counts = []
        for text in texts:
            response = self.client.models.count_tokens(
                model=self.model_name,
                contents=[text]
            )
            counts.append(response.total_tokens)
        return counts

    @retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(5))
    def _embed_single_batch(self, texts: list[str]) -> list[list[float]]:
        """Embeds a single batch of text using the Gemini API.
        
        It handles network instability and rate limits via exponential backoff.
        """
        logger.debug("embedding_batch_request", batch_size=len(texts))
        
        # In current Google GenAI SDK, we need to pass each string as a separate embed_content call
        # or use specific batch parameters if supported. 
        # For a robust approach with the current SDK:
        embeddings = []
        for text in texts:
            response = self.client.models.embed_content(model=self.model_name, contents=text)
            # Each response.embeddings is a list with one item for a single content
            embeddings.append(response.embeddings[0].values)
            
        return embeddings

    def generate_embeddings(self, chunks: list[str], batch_size: int = 20) -> list[list[float]]:
        """Generates embeddings for a list of text chunks in batches."""
        if batch_size <= 0:
             raise ValueError("batch_size must be a positive integer")
        all_embeddings = []
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            embeddings = self._embed_single_batch(batch)
            all_embeddings.extend(embeddings)
        return all_embeddings
    

if __name__ == "__main__":
    # Example usage
    embedder = GeminiEmbedder()
    sample_texts = ["Hello world!", "This is a test.", "Embedding generation with Gemini API."]
    embeddings = embedder.generate_embeddings(sample_texts, batch_size=2)
    print(f"Generated embeddings for {len(sample_texts)} texts.")