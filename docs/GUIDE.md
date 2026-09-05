# Trace RAG Pipeline Architecture & Guide

This guide provides a deeper overview of the design patterns, data flow, and usage of the Trace RAG Pipeline.

## 1. System Architecture

The pipeline is built as a single unified FastAPI application (`src/main.py` -> `src/api/routes.py`) that handles both real-time data ingestion and RAG querying.

```mermaid
graph TD
    A[Client User] -->|WebSocket /ws/ingest| B[Streaming Ingestion Pipeline]
    A -->|POST /query| C[Retrieval & Generation Engine]
    
    subgraph Ingestion [Streaming Data Ingestion]
        B --> D[Async Crawler (Playwright)]
        D -->|Raw HTML/Text| E[Text Chunker]
        E -->|Text Chunks| F[Gemini Embedder]
        F -->|Vectors & Metadata| G[(ChromaDB Vector Store)]
    end
    
    subgraph Querying [RAG Engine]
        C --> H[Query Embedder]
        H -->|Query Vector| G
        G -->|Top-K Chunks| I[Context Formatter]
        I --> J[Gemini LLM]
        J -->|Synthesized Answer| C
    end
```

### Key Components

- **Streaming Ingestion worker map:** Crawling, chunking, and embedding happen concurrently using asynchronous queues. As pages are crawled, they are immediately chunked, batched, embedded, and saved to the database. We use WebSockets to stream the exact state back to the UI in real time.
- **Async Playwright Crawler (`src/ingestion/crawler.py`):** Downloads web pages dynamically (including Javascript-rendered sites), extracts the core readable text, and returns content.
- **Local Vector Database (`src/database/chroma_manager.py`):** Uses ChromaDB on the local disk (`data/knowledge_base/`). It does not require a secondary remote server.

## 2. Using the Dashboard

The recommended way to interact with the pipeline is via the included React web user interface. Assuming both servers are running (`make dev`), navigate to: 

**`http://localhost:5173/`**

### Ingesting Data

1. Navigate to the **Database Ingestion** tab.
2. Enter a valid target URL (e.g., `https://example.com`) in the **Ingestion Configuration**.
3. Specify your crawl configurations:
   - **Crawl Depth:** How many link-hops away from the original URL the crawler will go. (Setting to 1 only crawls the given URL. Max 3).
   - **Chunk Size / Overlap:** Determines how text is partitioned before it is embedded. (Max Chunk Size 1000, Overlap 100).
4. Click **Run Pipeline**. A live feed of the ingestion background workers will output below via WebSocket.

### Querying Data

1. Once data is verified to be inside the vector database via the logs, switch over to the **RAG Engine** tab at the top.
2. Enter your question, adjust the API connection Temperature, and set your preferred Top-K amount (max 5) representing how many database chunks to retrieve for context.
3. Click "Generate Insights". The response will return the final LLM-synthesized answer rendered in Markdown, along with the raw chunks used to generate that answer (for verification).
4. **Dev Mode:** You can toggle the "Dev Mode" switch inside the Query Intelligence Engine to reveal the raw formatted instruction payloads hitting the LLM API.

### Cost & Telemetry

1. Navigate to the **Dashboard Overview** tab.
2. Here you can view dynamic charts representing the total amount of standard chat tokens saved by using Trace RAG. Real system token counts natively display how much data your indexing and generation actually consumed compared to standard chat footprints.

## 3. Working With The Local Vector DB

The default configuration saves the ChromaDB indexes in the `data/` directory at the root of the project.

- To completely reset the Vector Database and delete all documents, delete the `data/knowledge_base/` folder.
- If you run the project in Docker, the `data/` folder is volume-mounted so the index persists between container restarts.

## 4. API Endpoints Reference

Currently, the primary exposed systems from the FastAPI Backend are:

- `WS /ws/ingest` - WebSocket connection handling live streaming web crawling & embedding pipeline.
- `POST /api/v1/query` - Provide `{ "question": "...", "top_k": 5, "temperature": 0.3 }` to execute the full retrieval, format the prompt, and execute the Gemini LLM. Returns LLM answer alongside retrieved citation chunks, response time, and token counts.
- `GET /api/v1/stats` - Returns a comprehensive summary payload containing stats for total queries, average response times, UI database stats and total combined model token counts (both embedding and generation).