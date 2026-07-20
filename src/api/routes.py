from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from functools import lru_cache
from src.generation.engine import RAGEngine
import traceback
import asyncio
from src.ingestion.crawler import AsyncCrawler
from src.ingestion.chunker import TextChunker
from src.api.models import templates, GenerationResponse

app = FastAPI(title="Trace RAG Pipeline")

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
        chunk_size = config_data.get("chunk_size", 500)
        overlap = config_data.get("overlap", 50)
        max_depth = config_data.get("max_depth", 1)

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
        print("Client disconnected")
    except Exception as e:
        traceback.print_exc()
        await websocket.send_json({"status": "error", "message": str(e)})

@app.post("/query/advanced", response_model=GenerationResponse)
def query_rag_advanced(request: QueryRequest):
    """Hits the vector database, formats chunks, asks LLM, and returns full context (Prompt, Chunks, Answer)."""
    try:
        engine = get_engine()
        # Retrieve
        question_embedding = engine.embedder.generate_embeddings([request.question])[0]
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
        context_string = engine._format_context(results)
        
        # Reconstruct Prompt (for observability)
        prompt = f"""
        Context Information:
        {context_string}
        
        User Question: {request.question}
        """

        # Generate
        answer = engine.client.models.generate_content(
            model=engine.model_name,
            contents=prompt,
            config=engine.client.types.GenerateContentConfig( # Ensure this uses the correct SDK types
                system_instruction=engine.system_instruction,
                temperature=0.3,
            )
        ).text

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
        return {"status": "ok", "db_count": engine.db.count()}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
