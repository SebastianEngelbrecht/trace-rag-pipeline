import sys
from pathlib import Path

# Add project root to Python path so 'src' can be imported when running as a script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import chromadb
from src.config.settings import get_settings
from src.config.logger import get_logger

logger = get_logger(__name__)

class ChromaManager:
    def __init__(self, collection_name: str = "rag_collection"):
        """Initialize ChromaDB client and collection."""
        settings = get_settings()
        self.persist_directory = str(Path(settings.CHROMA_DB_DIR).resolve())
        self.collection_name = collection_name
        
        # Initialize a persistent client
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        
        # Get or create the collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"} # Use cosine similarity
        )
        logger.info(
            "chroma_db_initialized",
            directory=self.persist_directory,
            collection=self.collection_name,
        )

    def add_chunks(self, chunks: list[dict], embeddings: list[list[float]]):
        """Adds text chunks and their embeddings to ChromaDB."""
        if not chunks or not embeddings:
            return
            
        if len(chunks) != len(embeddings):
            raise ValueError(f"Number of chunks ({len(chunks)}) must match number of embeddings ({len(embeddings)})")

        ids = [chunk["chunk_id"] for chunk in chunks]
        documents = [chunk["content"] for chunk in chunks]
        metadatas = [
            {
                "source_url": chunk.get("source_url", ""),
                "chunk_index": chunk.get("chunk_index", 0),
                "token_count": chunk.get("token_count", 0)
            }
            for chunk in chunks
        ]

        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        logger.debug("chunks_added_to_chroma", count=len(chunks))

    def query(self, query_embeddings: list[list[float]], n_results: int = 5):
        """Queries the collection using embeddings."""
        logger.debug("querying_chroma", results_requested=n_results)
        return self.collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results
        )

    def peek(self, limit: int = 5):
        """Returns a few items from the collection to verify it's working."""
        return self.collection.peek(limit=limit)

    def count(self):
        """Returns the total number of items in the collection."""
        return self.collection.count()

if __name__ == "__main__":
    manager = ChromaManager()
    print(f"ChromaDB initialized at: {manager.persist_directory}")
    print(f"Collection count: {manager.count()}")

# Make sure that I do a hybrid search with vector retriever and BM25 retriever. The vector retriever will use the embeddings to find similar chunks, while the BM25 retriever will use keyword matching to find relevant chunks. This way, we can combine the strengths of both methods for better retrieval performance.
