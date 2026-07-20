import pytest
from unittest.mock import MagicMock, patch
from src.embedding.gemini import GeminiEmbedder

# Fixture to provide a mocked Embedder
@pytest.fixture
def mocked_embedder():
    # Avoid depending on a real .env / GEMINI_API_KEY in unit tests
    with patch("src.embedding.gemini.get_settings") as mock_get_settings:
        mock_get_settings.return_value = MagicMock(
            GEMINI_API_KEY="test_key",
            EMBEDDING_MODEL="gemini-embedding-2",
        )

        with patch("src.embedding.gemini.genai.Client") as MockClient:
            # Mock the client object itself
            mock_client_instance = MockClient.return_value

            # Mock the response structure: response.embeddings = [MockEmbedding(...)]
            mock_response = MagicMock()
            mock_embedding = MagicMock()
            mock_embedding.values = [0.1, 0.2, 0.3]
            mock_response.embeddings = [mock_embedding]

            # Connect the mock model function to return the mocked response
            mock_client_instance.models.embed_content.return_value = mock_response

            embedder = GeminiEmbedder()
            yield embedder, mock_client_instance
def test_embedder_initialization(mocked_embedder):
    embedder, _ = mocked_embedder
    assert embedder.model_name == "gemini-embedding-2" # Default from settings

def test_embed_single_batch(mocked_embedder):
    embedder, mock_client = mocked_embedder
    
    texts = ["Test string"]
    embeddings = embedder._embed_single_batch(texts)
    
    # Assert network was 'called' once
    mock_client.models.embed_content.assert_called_once_with(
        model=embedder.model_name,
        contents="Test string",
    )
    
    # Assert it returns the correctly mocked vector structure
    assert len(embeddings) == 1
    assert embeddings[0] == [0.1, 0.2, 0.3]

def test_generate_embeddings_batching(mocked_embedder):
    embedder, mock_client = mocked_embedder
    
    # Create 5 texts
    texts = ["A", "B", "C", "D", "E"]
    
    # Call generate with batch size of 2. It should result in 3 batches: [A, B], [C, D], [E]
    assert mock_client.models.embed_content.call_count == 5
def test_generate_embeddings_invalid_batch(mocked_embedder):
    embedder, _ = mocked_embedder
    with pytest.raises(ValueError, match="positive integer"):
        embedder.generate_embeddings(["test"], batch_size=0)