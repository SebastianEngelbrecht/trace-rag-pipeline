import sys
from pathlib import Path

# Ensure src can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

"""Application entry point for the trace RAG pipeline."""

import asyncio
from src.ingestion.crawler import WebCrawler
from src.ingestion.chunker import TextChunker
from src.embedding.gemini import GeminiEmbedder
from src.database.chroma_manager import ChromaManager

async def run_pipeline():
    print("🚀 Starting RAG Pipeline...")
    
    # 1. Crawl
    print("\n🕸️ Crawling data...")
    crawler = WebCrawler(max_depth=1)
    # Just crawl a small example for testing
    crawled_data = await crawler.crawl("https://www.example.com")
    print(f"Crawled {len(crawled_data)} pages.")
    
    # 2. Chunk
    print("\n✂️ Chunking text...")
    chunker = TextChunker()
    chunks = chunker.process_crawled_data(crawled_data)
    print(f"Generated {len(chunks)} chunks.")
    
    if not chunks:
        print("No chunks generated. Exiting.")
        return
        
    # 3. Embed
    print("\n🧠 Generating embeddings...")
    embedder = GeminiEmbedder()
    chunk_texts = [c["content"] for c in chunks]
    embeddings = embedder.generate_embeddings(chunk_texts)
    print(f"Generated {len(embeddings)} embeddings.")
    
    # 4. Store in ChromaDB
    print("\n💾 Storing in ChromaDB...")
    db_manager = ChromaManager()
    db_manager.add_chunks(chunks, embeddings)
    print(f"Successfully stored in ChromaDB. Total items in DB: {db_manager.count()}")
    print(f"Pipeline completed successfully! ✅")

def main():
    asyncio.run(run_pipeline())

if __name__ == "__main__":
    main()

