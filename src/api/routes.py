from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from functools import lru_cache
from src.generation.engine import RAGEngine
import traceback
import asyncio
import time
from src.ingestion.crawler import AsyncCrawler
from src.ingestion.chunker import TextChunker
from src.api.models import templates, GenerationResponse
from src.config.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(title="Trace RAG Pipeline")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter(prefix="/api/v1", tags=["RAG"])

@lru_cache()
def get_engine() -> RAGEngine:
    return RAGEngine()

class QueryRequest(BaseModel):
    question: str
    top_k: int = 5
    temperature: float = 0.3
    vector_weight: float = 0.5

class QueryResponse(BaseModel):
    answer: str

@app.get("/", response_class=HTMLResponse)
async def get_ui(request: Request):
    """Serve the advanced UI dashboard."""
    return templates.TemplateResponse(request, name="index.html")

@app.websocket("/ws/ingest")
async def websocket_ingest(websocket: WebSocket):
    """WebSocket endpoint for real-time ingestion logging and control."""
    await websocket.accept()
    try:
        # Receive configuration from client
        config_data = await websocket.receive_json()
        target_url = config_data.get("url")
        if not isinstance(target_url, str) or not target_url.strip():
            await websocket.send_json({"status": "error", "message": "Missing or invalid 'url' in request."})
            return
        target_url = target_url.strip()
        try:
            chunk_size = int(config_data.get("chunk_size", 500))
            overlap = int(config_data.get("overlap", 50))
            max_depth = int(config_data.get("max_depth", 3))
        except (ValueError, TypeError) as e:
            await websocket.send_json({"status": "error", "message": f"Invalid configuration value (expected integer): {e}"})
            return

        await websocket.send_json({"status": "running", "message": f"Starting crawler on {target_url} (depth={max_depth})..."})
        
        # Set up a queue to receive text content as it's scraped
        out_queue = asyncio.Queue()
        crawler = AsyncCrawler(target_url, max_depth=max_depth, max_concurrency=3)
        
        chunk_queue = asyncio.Queue()
        chunker = TextChunker(chunk_size=chunk_size, overlap=overlap)
        stats = {"crawled": 0, "embedded": 0, "total_tokens": 0}

        async def ws_chunking_worker():
            """Continuously reads crawled pages, chunks them, and passes them to embedder."""
            while True:
                item = await out_queue.get()
                if item is None:
                    await chunk_queue.put(None)
                    out_queue.task_done()
                    break
                
                url, text = item
                stats["crawled"] += 1
                await websocket.send_json({"status": "running", "message": f"Crawled & chunking: {url} ({len(text)} characters)"})
                
                chunks = chunker.process_crawled_data({url: text})
                for chunk in chunks:
                    stats["total_tokens"] += chunk.get("token_count", 0)
                    await chunk_queue.put(chunk)
                out_queue.task_done()

        async def ws_embedding_worker(batch_size=20):
            """Continuously reads chunks, batches them, embeds, and stores in DB."""
            batch = []
            loop = asyncio.get_running_loop()
            engine = get_engine()
            
            async def process_batch(current_batch):
                if not current_batch: return
                chunk_texts = [c["content"] for c in current_batch]
                embeddings = await loop.run_in_executor(None, engine.embeddings.embed_documents, chunk_texts)
                await loop.run_in_executor(None, engine.db.add_chunks, current_batch, embeddings)
                
                stats["embedded"] += len(current_batch)
                
                await websocket.send_json({"status": "running", "message": f"Indexed batch of {len(current_batch)} chunks. Total indexed: {stats['embedded']}"})

            while True:
                item = await chunk_queue.get()
                if item is None:
                    await process_batch(batch)
                    chunk_queue.task_done()
                    break
                
                batch.append(item)
                if len(batch) >= batch_size:
                    await process_batch(batch)
                    batch = []
                chunk_queue.task_done()

        # Start streaming workers in the background
        chunk_task = asyncio.create_task(ws_chunking_worker())
        embed_task = asyncio.create_task(ws_embedding_worker(batch_size=20))
        
        try:
            # Start producer (crawler) and wait for it to finish crawling
            await crawler.crawl(out_queue=out_queue)
        finally:
            # Guarantee workers that crawling is done, avoiding hung asyncio tasks
            await out_queue.put(None)
            
            # Wait for all workers to finish processing their queues
            await chunk_task
            await embed_task
        
        await websocket.send_json({
            "status": "complete", 
            "message": f"Pipeline run complete. Crawled {stats['crawled']} pages, indexed {stats['embedded']} chunks. ({stats['total_tokens']} tokens)"
        })
        await websocket.close()
        
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.exception("Error during pipeline run")
        await websocket.send_json({"status": "error", "message": str(e)})

@router.post("/query", response_model=GenerationResponse)
def api_query_rag_advanced(request: QueryRequest):
    """Hits the hybrid database, formats chunks, asks LLM, and returns full context."""
    engine = get_engine()
    start_time = time.time()
    
    try:
        content, prompt, docs, response_time, tokens, retrieval_time = engine.query(
            user_question=request.question,
            top_k=request.top_k,
            temperature=request.temperature,
            return_details=True
        )

        # Update global stats
        app.state.total_queries = getattr(app.state, "total_queries", 0) + 1
        
        current_avg = getattr(app.state, "avg_response_time", 0.0)
        app.state.avg_response_time = (current_avg * (app.state.total_queries - 1) + response_time) / app.state.total_queries
        app.state.total_tokens = getattr(app.state, "total_tokens", 0) + tokens
        
        return GenerationResponse(
            answer=content,
            chunks=docs,
            prompt=prompt,
            response_time_ms=response_time,
            tokens_used=tokens,
            retrieval_time_ms=retrieval_time
        )
    except Exception as e:
        logger.exception("query_error")
        raise HTTPException(status_code=500, detail=str(e))

class StatsResponse(BaseModel):
    total_queries: int
    avg_response_time: float
    total_tokens: int
    ingested_chunks: int
    total_db_tokens: int

@app.get("/api/v1/stats", response_model=StatsResponse)
def get_stats():
    # In a real app we'd query an analytics DB, but here we can query the vector store
    # and use some globals to proxy the stats to the frontend for UI demo purposes
    engine = get_engine()
    
    # Simple global tracking for demo
    queries = getattr(app.state, "total_queries", 0)
    avg_time = getattr(app.state, "avg_response_time", 0.0)
    tokens = getattr(app.state, "total_tokens", 0)
    
    try:
        cache_ttl_s = 30
        now = time.time()
        
        chunks = engine.db.collection.count()
        
        cached_tokens = getattr(app.state, "cached_total_db_tokens", None)
        cached_at = getattr(app.state, "cached_total_db_tokens_at", 0.0)

        if cached_tokens is not None and (now - cached_at) < cache_ttl_s:
            total_db_tokens = cached_tokens
        elif chunks > 0:
            db_data = engine.db.collection.get(include=["metadatas"])
            total_db_tokens = sum((meta or {}).get("token_count", 0) for meta in db_data.get("metadatas", []))
            
            app.state.cached_total_db_tokens = total_db_tokens
            app.state.cached_total_db_tokens_at = now
        else:
            total_db_tokens = 0
            
    except Exception as e:
        logger.error(f"Error getting chroma db stats: {e}")
        chunks = 0
        total_db_tokens = 0
        
    return StatsResponse(
        total_queries=queries,
        avg_response_time=round(avg_time, 2),
        total_tokens=tokens,
        ingested_chunks=chunks,
        total_db_tokens=total_db_tokens
    )

@app.post("/query", response_model=GenerationResponse)
def query_rag_advanced(request: QueryRequest):
    """Hits the vector database, formats chunks, asks LLM, and returns full context (Prompt, Chunks, Answer)."""
    try:
        engine = get_engine()
        
        answer, prompt, docs, response_time_ms, tokens_used, retrieval_time_ms = engine.query(
            user_question=request.question,
            top_k=request.top_k,
            temperature=request.temperature,
            vector_weight=request.vector_weight,
            return_details=True
        )
        
        # Update global stats for telemetry UI
        current_queries = getattr(app.state, "total_queries", 0)
        current_avg = getattr(app.state, "avg_response_time", 0.0)
        
        new_queries = current_queries + 1
        new_avg = ((current_avg * current_queries) + (response_time_ms / 1000.0)) / new_queries
        
        app.state.total_queries = new_queries
        app.state.avg_response_time = new_avg
        app.state.total_tokens = getattr(app.state, "total_tokens", 0) + tokens_used

        return GenerationResponse(
            answer=answer, 
            chunks=docs, 
            prompt=prompt,
            response_time_ms=response_time_ms,
            tokens_used=tokens_used,
            retrieval_time_ms=retrieval_time_ms
        )

    except Exception:
        logger.exception("query_rag_advanced_failed")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
def health_check():
    try:
        engine = get_engine()
        return {"status": "ok", "db_count": engine.db.collection.count()}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

app.include_router(router)
