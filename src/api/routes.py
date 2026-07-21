from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request, APIRouter
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from functools import lru_cache
from src.generation.engine import RAGEngine
import traceback
import asyncio
from src.ingestion.crawler import AsyncCrawler
from src.ingestion.chunker import TextChunker
from src.api.models import templates, GenerationResponse
from src.config.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(title="Trace RAG Pipeline")
router = APIRouter(prefix="/api/v1", tags=["RAG"])

@lru_cache()
def get_engine() -> RAGEngine:
    return RAGEngine()

class QueryRequest(BaseModel):
    question: str
    top_k: int = 5

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
        stats = {"crawled": 0, "embedded": 0}

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
        
        # Start producer (crawler) and wait for it to finish crawling
        await crawler.crawl(out_queue=out_queue)
        
        # Signal workers that crawling is done
        await out_queue.put(None)
        
        # Wait for all workers to finish processing their queues
        await chunk_task
        await embed_task

        await websocket.send_json({
            "status": "complete", 
            "message": f"Pipeline run complete. Crawled {stats['crawled']} pages, indexed {stats['embedded']} chunks."
        })
        
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.exception("Error during pipeline run")
        await websocket.send_json({"status": "error", "message": str(e)})

@router.post("/query/advanced", response_model=GenerationResponse)
def api_query_rag_advanced(request: QueryRequest):
    """Hits the hybrid database, formats chunks, asks LLM, and returns full context."""
    # Redirect to the main endpoint handler to prevent logic duplication
    return query_rag_advanced(request)

@app.post("/query/advanced", response_model=GenerationResponse)
def query_rag_advanced(request: QueryRequest):
    """Hits the vector database, formats chunks, asks LLM, and returns full context (Prompt, Chunks, Answer)."""
    try:
        engine = get_engine()
        # Retrieve
        question_embedding = engine.embeddings.embed_query(request.question)
        results = engine.db.query(query_embeddings=[question_embedding], n_results=request.top_k)
        
        # Format chunks for UI
        ui_chunks = []
        if results and results.get("documents") and results["documents"][0]:
            for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
                ui_chunks.append({
                    "content": doc,
                    "source_url": meta.get("source_url", "Unknown"),
                    "chunk_index": meta.get("chunk_index", 0)
                })

        # Generate Context String
        formatted_parts = []
        if results and results.get("documents") and results["documents"][0]:
            for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
                source = meta.get("source_url", "Unknown source")
                formatted_parts.append(f"[Source: {source}]\n{doc}\n")
        context_string = "\n---\n".join(formatted_parts) if formatted_parts else "No relevant context found."
        
        # Reconstruct Prompt (for observability)
        prompt = f"""
        {engine.system_instruction}

        Context Information:
        {context_string}
        
        User Question: {request.question}
        """

        # Generate
        answer_message = engine.llm.invoke(prompt)
        answer_content = answer_message.content
        
        # Handle cases where content might be a list of blocks instead of a plain string
        if isinstance(answer_content, list):
            answer = "".join(block.get("text", "") if isinstance(block, dict) else str(block) for block in answer_content)
        else:
            answer = str(answer_content)

        return GenerationResponse(answer=answer, chunks=ui_chunks, prompt=prompt)

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=QueryResponse)
def query_rag(request: QueryRequest):
    """Hits the vector database, formats the retrieved chunks, and asks the LLM to summarize."""
    try:
        engine = get_engine()
        answer = engine.query(request.question, top_k=request.top_k)
        return QueryResponse(answer=answer)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    try:
        engine = get_engine()
        return {"status": "ok", "db_count": engine.db.collection.count()}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

class CrawlRequest(BaseModel):
    url: str
    max_depth: int = 1

@router.post("/crawl")
async def api_crawl(request: CrawlRequest):
    """Old crawling backwards compatibility endpoint."""
    return {"status": "success", "message": "Background task deprecated, please use websocket /ws/ingest."}

@router.get("/stats")
def api_stats():
    """Old DB stats backwards compatibility endpoint."""
    return {"status": "success", "db_count": get_engine().db.collection.count()}

@router.post("/query", response_model=QueryResponse)
def api_query_rag(request: QueryRequest):
    """Hits the vector database, formats the retrieved chunks, and asks the LLM to summarize."""
    return query_rag(request)

app.include_router(router)
