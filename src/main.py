"""Application entry point for the trace RAG pipeline."""

import sys
from pathlib import Path

# Ensure src can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
from src.ingestion.crawler import AsyncCrawler
from src.ingestion.chunker import TextChunker
from src.embedding.gemini import GeminiEmbedder
from src.database.chroma_manager import ChromaManager
from src.config.logger import setup_logging, get_logger
from src.config.settings import settings

logger = get_logger(__name__)

async def chunking_worker(page_queue: asyncio.Queue, chunk_queue: asyncio.Queue, chunker: TextChunker):
    """
    Worker task that continuously reads raw crawled pages from `page_queue`,
    splits them into chunks using the `chunker`, and places the chunks into `chunk_queue`.
    It shuts down when it receives a `None` sentinel value.
    """
    while True:
        item = await page_queue.get()
        if item is None: # Sentinel value indicates crawling is done
            await chunk_queue.put(None) # Pass sentinel to the next worker
            page_queue.task_done()
            break
        
        url, text = item
        # Chunking a single page dictionary
        chunks = chunker.process_crawled_data({url: text})
        for chunk in chunks:
            await chunk_queue.put(chunk)
        
        page_queue.task_done()

async def embedding_worker(chunk_queue: asyncio.Queue, embedder: GeminiEmbedder, db_manager: ChromaManager, batch_size: int = 20):
    """
    Worker task that reads parsed chunks from `chunk_queue`, batches them, 
    generates embeddings using the Gemini API, and stores them in ChromaDB.
    Batches are processed asynchronously using a thread pool to avoid blocking the event loop.
    """
    batch = []
    loop = asyncio.get_running_loop()
    
    async def process_batch(current_batch):
        """Helper to compute embeddings and save a single batch to the DB."""
        if not current_batch: return
        chunk_texts = [c["content"] for c in current_batch]
        # Run sync methods in thread pool to not block asyncio event loop
        embeddings = await loop.run_in_executor(None, embedder.generate_embeddings, chunk_texts)
        await loop.run_in_executor(None, db_manager.add_chunks, current_batch, embeddings)
        logger.info("batch_stored", batch_size=len(current_batch), total_db_count=db_manager.count())

    while True:
        item = await chunk_queue.get()
        if item is None: # Sentinel value indicates no more chunks are coming
            await process_batch(batch) # Flush any remaining items in the buffer
            chunk_queue.task_done()
            break
            
        batch.append(item)
        if len(batch) >= batch_size:
            await process_batch(batch)
            batch = []
            
        chunk_queue.task_done()

async def run_pipeline():
    """
    Sets up and executes the asynchronous streaming RAG pipeline.
    It links a producer (the web crawler) with consumers (chunker and embedder workers)
    using asyncio queues.
    """
    logger.info("pipeline_started")
    
    page_queue = asyncio.Queue()
    chunk_queue = asyncio.Queue()

    
    crawler = AsyncCrawler("https://detsundekoekken.dk", max_depth=1)
    chunker = TextChunker()
    embedder = GeminiEmbedder()
    db_manager = ChromaManager()
    
    # Start consumers
    chunk_task = asyncio.create_task(chunking_worker(page_queue, chunk_queue, chunker))
    embed_task = asyncio.create_task(embedding_worker(chunk_queue, embedder, db_manager, batch_size=20))
    
    # Start producer
    logger.info("crawling_started")
    await crawler.crawl(out_queue=page_queue)
    
    # Signal workers to finish
    logger.info("crawl_complete", status="waiting_for_chunks")
    await page_queue.put(None)
    
    await chunk_task
    await embed_task
    
    logger.info("pipeline_completed", final_db_count=db_manager.count())

def main():
    setup_logging(settings.LOG_LEVEL)
    asyncio.run(run_pipeline())

if __name__ == "__main__":
    main()

