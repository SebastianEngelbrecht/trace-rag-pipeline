import sys
from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import asyncio
import traceback
import time

# Ensure src can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.ingestion.crawler import AsyncCrawler
from src.ingestion.chunker import TextChunker
from src.embedding.gemini import GeminiEmbedder
from src.database.chroma_manager import ChromaManager
from src.generation.engine import RAGEngine
from src.api.models import templates, GenerationResponse

app = FastAPI(title="Trace RAG Pipeline")
router = APIRouter(prefix="/api/v1", tags=["RAG"])

engine = RAGEngine()

class CrawlRequest(BaseModel):
    url: str
    max_depth: int = 1

class QueryRequest(BaseModel):
    question: str
    top_k: int = 5
    
@app.get("/", response_class=HTMLResponse)
async def get_ui(request: Request):
    """Serve the advanced UI dashboard."""
    return templates.TemplateResponse("index.html", {"request": request})

async def chunking_worker(page_queue: asyncio.Queue, chunk_queue: asyncio.Queue, chunker: TextChunker, websocket: WebSocket = None):
    """Worker that reads crawled pages, chunks them, and passes them to the chunk_queue."""
    while True:
        item = await page_queue.get()
        if item is None:
            await chunk_queue.put(None)
            page_queue.task_done()
            break
            
        url, text = item
        if websocket:
            await websocket.send_json({"status": "running", "message": f"Crawled & Chunking: {url} ({len(text)} chars)"})
            
        chunks = chunker.process_crawled_data({url: text})
        for chunk in chunks:
            await chunk_queue.put(chunk)
            
        page_queue.task_done()

async def embedding_worker(chunk_queue: asyncio.Queue, embedder: GeminiEmbedder, db_manager: ChromaManager, batch_size: int = 20, websocket: WebSocket = None):
    """Worker that reads chunks, embeds them in batches, and saves to DB."""
    batch = []
    loop = asyncio.get_running_loop()
    
    async def process_batch(current_batch):
        if not current_batch: return
        chunk_texts = [c["content"] for c in current_batch]
        embeddings = await loop.run_in_executor(None, embedder.generate_embeddings, chunk_texts)
        await loop.run_in_executor(None, db_manager.add_chunks, current_batch, embeddings)
        if websocket:
            await websocket.send_json({"status": "running", "message": f"Indexed batch of {len(current_batch)} chunks. Total DB size: {db_manager.count()}"})

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


@app.websocket("/ws/ingest")
async def websocket_ingest(websocket: WebSocket):
    """WebSocket endpoint for real-time streaming ingestion logging and control."""
    await websocket.accept(); start_time = time.time()
    try:
        # Receive configuration from client
        config_data = await websocket.receive_json()
        target_url = config_data.get("url")
        chunk_size = int(config_data.get("chunk_size", 500))
        overlap = int(config_data.get("overlap", 50))
        max_depth = int(config_data.get("max_depth", 1))

        await websocket.send_json({"status": "running", "message": f"Starting streaming crawler on {target_url} (depth={max_depth})..."})
        
        page_queue = asyncio.Queue()
        chunk_queue = asyncio.Queue()
        
        crawler = AsyncCrawler(target_url, max_depth=max_depth, max_concurrency=3)
        chunker = TextChunker(chunk_size=chunk_size, overlap=overlap)
        
        # Start consumer tasks
        chunk_task = asyncio.create_task(chunking_worker(page_queue, chunk_queue, chunker, websocket))
        embed_task = asyncio.create_task(embedding_worker(chunk_queue, engine.embedder, engine.db, 20, websocket))
        
        # Run crawling
        await crawler.crawl(out_queue=page_queue)
        
        # Signal crawling complete
        await websocket.send_json({"status": "running", "message": "Crawling finished. Waiting for chunking and embedding to complete..."})
        await page_queue.put(None)
        
        # Wait for pipelines to flush
        await chunk_task
        await embed_task

        end_time = time.time(); elapsed_time = round(end_time - start_time, 2); await websocket.send_json({"status": "complete", "message": f"Pipeline run complete in {elapsed_time}s."})
        
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        traceback.print_exc()
        await websocket.send_json({"status": "error", "message": str(e)})


@app.post("/query/advanced", response_model=GenerationResponse)
def query_rag_advanced(request: QueryRequest):
    import time
    start_time = time.time()
    """Hits the vector database, formats chunks, asks LLM, and returns full context (Prompt, Chunks, Answer)."""
    try:
        question_embedding = engine.embedder.generate_embeddings([request.question])[0]
        results = engine.db.query(query_embeddings=[question_embedding], n_results=request.top_k)
        
        ui_chunks = []
        if results and results.get("documents") and results["documents"][0]:
            for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
                ui_chunks.append({
                    "content": doc,
                    "source_url": meta.get("source_url", "Unknown"),
                    "chunk_index": meta.get("chunk_index", 0)
                })

        context_string = engine._format_context(results)
        
        prompt = f"""
        Context Information:
        {context_string}
        
        User Question: {request.question}
        """

        response = engine.client.models.generate_content(
            model=engine.model_name,
            contents=prompt,
            config=engine.client.types.GenerateContentConfig(
                system_instruction=engine.system_instruction,
                temperature=0.3,
            )
        )
        
        answer_text = response.text
        tokens = 0
        end_time = time.time()
        elapsed_time = round((end_time - start_time) * 1000, 2)



        return GenerationResponse(answer=answer_text, chunks=ui_chunks, prompt=prompt, response_time_ms=elapsed_time, tokens_used=tokens)

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

async def process_crawl_task(url: str, max_depth: int):
    try:
        page_queue = asyncio.Queue()
        chunk_queue = asyncio.Queue()
        
        crawler = AsyncCrawler(url, max_depth=max_depth)
        chunker = TextChunker()
        
        chunk_task = asyncio.create_task(chunking_worker(page_queue, chunk_queue, chunker))
        embed_task = asyncio.create_task(embedding_worker(chunk_queue, engine.embedder, engine.db, 20))
        
        await crawler.crawl(out_queue=page_queue)
        await page_queue.put(None)
        
        await chunk_task
        await embed_task
    except Exception as e:
        print(f"Error in background crawl task: {str(e)}")


@router.post("/crawl")
async def trigger_crawl(req: CrawlRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(process_crawl_task, req.url, req.max_depth)
    return {"message": f"Streaming background crawl started for {req.url}"}

@router.post("/query")
async def query_documents(req: QueryRequest):
    try:
        # Compatibility redirect for the simpler route if anyone uses it
        return query_rag_advanced(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_stats():
    try:
        count = engine.db.count()
        return {"total_documents": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.include_router(router)
