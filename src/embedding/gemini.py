import google.generativeai as genai
from src.config.settings import settings
from tenacity import retry, wait_exponential, stop_after_attempt

# Configure the API key once when the module loads
genai.configure(api_key=settings.GEMINI_API_KEY)

class GeminiEmbedder:
    def __init__(self, model_name: str = settings.EMBEDDING_MODEL):
        self.model_name = model_name

    @retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(5))
    def _embed_single_batch(self, texts: list[str]) -> list[list[float]]:
        """Embeds a single batch of text using the Gemini API.
        
        It handles network instability and rate limits via exponential backoff.
        """
        response = genai.embed_content(model=self.model_name, content=texts)
        # For a list of texts, the response dict contains an 'embedding' key mapping to a list of vectors
        return response['embedding']

    def generate_embeddings(self, chunks: list[str], batch_size: int = 100) -> list[list[float]]:
        """Generates embeddings for a list of text chunks in batches."""
        all_embeddings = []
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            embeddings = self._embed_single_batch(batch)
            all_embeddings.extend(embeddings)
        return all_embeddings