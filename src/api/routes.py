import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

# Ensure src can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.ingestion.crawler import WebCrawler
from src.ingestion.chunker import TextChunker
from src.embedding.gemini import GeminiEmbedder
from src.database.chroma_manager import ChromaManager

router = APIRouter(prefix="/api/v1", tags=["RAG"])

class CrawlRequest(BaseModel):
    url: str
    max_depth: int = 1

class QueryRequest(BaseModel):
    query: str
    n_results: int = 5

async def process_crawl_task(url: str, max_depth: int):
    try:
        # Crawling
        crawler = WebCrawler(max_depth=max_depth)
        crawled_data = await crawler.crawl(url)
        if not crawled_data:
            return

        # Chunking
        chunker = TextChunker()
        chunks = chunker.process_crawled_data(crawled_data)
        if not chunks:
            return
            
        # Embedding
        embedder = GeminiEmbedder()
        chunk_texts = [c["content"] for c in chunks]
        embeddings = embedder.generate_embeddings(chunk_texts)
        
        # Storing
        db_manager = ChromaManager()
        db_manager.add_chunks(chunks, embeddings)
    except Exception as e:
        print(f"Error in background crawl task: {str(e)}")

@router.post("/crawl")
async def trigger_crawl(req: CrawlRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(process_crawl_task, req.url, req.max_depth)
    return {"message": f"Crawling process started in background for {req.url}"}

@router.post("/query")
async def query_documents(req: QueryRequest):
    try:
        embedder = GeminiEmbedder()
        query_embedding = embedder.generate_embeddings([req.query])[0]
        
        db_manager = ChromaManager()
        results = db_manager.query(query_embeddings=[query_embedding], n_results=req.n_results)
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_stats():
    try:
        db_manager = ChromaManager()
        count = db_manager.count()
        return {"total_documents": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

