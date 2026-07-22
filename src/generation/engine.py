import sys
import os
from pathlib import Path

# Add project root to Python path so 'src' can be imported when running as a script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.config.settings import get_settings
from src.config.logger import get_logger
from src.database.chroma_manager import ChromaManager

from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.retrievers import BM25Retriever
from langchain_chroma import Chroma
from langchain_core.documents import Document

logger = get_logger(__name__)

class RAGEngine:
    def __init__(self):
        settings = get_settings()
        if "GOOGLE_API_KEY" not in os.environ and settings.GEMINI_API_KEY:
            os.environ["GOOGLE_API_KEY"] = settings.GEMINI_API_KEY
        self.model_name = settings.CHAT_MODEL
        
        # Initialize dependencies
        self.db = ChromaManager()
        
        # Initialize Langchain components
        api_key = os.environ.get("GOOGLE_API_KEY", settings.GEMINI_API_KEY)
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            google_api_key=api_key
        )
        self.llm = ChatGoogleGenerativeAI(
            model=settings.CHAT_MODEL,
            temperature=0.3,
            google_api_key=api_key,
            max_tokens=None,
            timeout=None,
            max_retries=2,
        )
        
        # Reconstruct LangChain Chroma VectorStore from our existing local DB
        self.vector_store = Chroma(
            client=self.db.client,
            collection_name=self.db.collection_name,
            embedding_function=self.embeddings,
        )
        
        # System prompt instructions
        self.system_instruction = """
        You are a helpful and precise assistant for the Enterprise RAG Pipeline. 
        You will be provided with a user's question, and a set of contextual documents retrieved from a local database.
        
        Rules:
        1. Base your answer PRIMARILY on the provided context.
        2. If the context does not contain the answer, politely say "I do not have enough information in my knowledge base to answer that." 
        3. Do not formulate an answer based on your pre-trained knowledge if the context is empty or irrelevant.
        4. If you use information from a specific chunk, cite the `source_url` provided in the metadata.
        """
        
        # BM25 Cache
        self._bm25_retriever = None
        self._bm25_cache_key = None

    def _reciprocal_rank_fusion(self, results_list: list[list[Document]], k: int = 60) -> list[Document]:
        """
        Fuses multiple ranked lists using Reciprocal Rank Fusion.
        RRF_score = sum(1 / (k + rank))
        """
        fused_scores = {}
        doc_map = {}

        for docs in results_list:
            for rank, doc in enumerate(docs):
                # Prefer stable identifiers to avoid collisions across identical text chunks.
                source_url = doc.metadata.get("source_url")
                chunk_index = doc.metadata.get("chunk_index")
                doc_id = f"{source_url}::{chunk_index}" if source_url is not None and chunk_index is not None else doc.page_content
                if doc_id not in fused_scores:
                    fused_scores[doc_id] = 0
                    doc_map[doc_id] = doc
                fused_scores[doc_id] += 1 / (k + rank)

        # Sort documents based on their fused scores internally
        reranked_results = sorted(
            [(score, doc_id) for doc_id, score in fused_scores.items()],
            key=lambda x: x[0],
            reverse=True
        )
        
        # Max possible RRF score is when a document is rank 0 in ALL lists.
        # Since we use 2 retrievers (BM25 and Vector), the absolute max score is (1/60) + (1/60) ≈ 0.0333...
        max_possible_score = len(results_list) * (1 / k)

        for score, doc_id in reranked_results:
            # Normalize the score to a 0-1 range to reflect a true "confidence percentage"
            normalized_score = min(1.0, score / max_possible_score)
            doc_map[doc_id].metadata["rank_score"] = normalized_score

        return [doc_map[doc_id] for _, doc_id in reranked_results]

    def _get_hybrid_results(self, user_question: str, top_k: int = 5) -> tuple[list[Document], float]:
        """Gets results from BM25 and Vector matching and fuses them. Returns tuple of (results, retrieval_time_ms)."""
        import time
        start_time = time.time()
        
        # 1. Setup Vector Retriever
        vector_retriever = self.vector_store.as_retriever(search_kwargs={"k": top_k})
        vector_results = vector_retriever.invoke(user_question)
        
        # 2. Setup BM25 Retriever
        # Fetch only ids to compute a cache key (order-independent hash of exact content state)
        all_ids = self.db.collection.get(include=[])
        current_count = len(all_ids.get("ids", []))
        if current_count == 0:
            retrieval_time_ms = (time.time() - start_time) * 1000
            return vector_results, retrieval_time_ms
            
        # Create a stable hash based on all IDs to detect upserts/updates
        # even if the total count remains the exact same number
        current_cache_key = hash(frozenset(all_ids.get("ids", [])))
            
        if self._bm25_retriever is None or self._bm25_cache_key != current_cache_key:
            # We explicitly ask only for documents and metadatas, rather than the default
            # which might include large embeddings payload causing memory overhead.
            all_data = self.db.collection.get(include=['documents', 'metadatas'])
            if not all_data or not all_data.get('documents'):
                retrieval_time_ms = (time.time() - start_time) * 1000
                return vector_results, retrieval_time_ms
                
            docs = []
            for doc_content, metadata in zip(all_data['documents'], all_data['metadatas']):
                 # Reconstruct Langchain Document objects
                 docs.append(Document(page_content=doc_content, metadata=metadata or {}))
                 
            self._bm25_retriever = BM25Retriever.from_documents(docs)
            self._bm25_cache_key = current_cache_key
            
        self._bm25_retriever.k = top_k
        bm25_results = self._bm25_retriever.invoke(user_question)
        
        # 3. Fuse Results
        fused_results = self._reciprocal_rank_fusion([vector_results, bm25_results])
        
        retrieval_time_ms = (time.time() - start_time) * 1000
        return fused_results[:top_k], retrieval_time_ms

    def _format_context(self, retrieved_docs) -> str:
        """Helper to format LangChain Document output into a readable string for the LLM."""
        if not retrieved_docs:
            return "No relevant context found."
            
        formatted_parts = []
        
        for doc in retrieved_docs:
            source = doc.metadata.get("source_url", "Unknown source")
            formatted_parts.append(f"[Source: {source}]\n{doc.page_content}\n")
            
        return "\n---\n".join(formatted_parts)

    def query(self, user_question: str, top_k: int = 5, temperature: float = 0.3, return_details: bool = False):
        """
        Retrieval-Augmented Generation using custom Hybrid Search.
        If return_details is true, returns (answer, prompt, docs as dicts, response_time_ms, tokens_used, retrieval_time_ms).
        Otherwise just returns the answer as a string.
        """
        import time
        start_time = time.time()
        
        logger.info("rag_query_started", question=user_question)
        
        # 1. Get Hybrid Results
        results, retrieval_time_ms = self._get_hybrid_results(user_question, top_k=top_k)
        
        # 2. Format context
        context_string = self._format_context(results)
        logger.debug("context_retrieved", num_chunks=len(results))
        
        # 4. Construct prompt
        prompt = f"""
        {self.system_instruction}

        Context Information:
        {context_string}
        
        User Question: {user_question}
        """
        
        # 5. Generate response using LangChain LLM (dynamically bind params per-request to avoid singleton pollution)
        response = self.llm.bind(temperature=temperature).invoke(prompt)
        content = response.content
        if isinstance(content, list):
            content = "".join(block.get("text", "") if isinstance(block, dict) else str(block) for block in content)
        else:
            content = str(content)
        
        # Parse usage metadata and document objects
        usage = getattr(response, "usage_metadata", {})
        tokens_used = usage.get("total_tokens", 0) if usage else 0
        
        docs_dicts = [
            {"content": doc.page_content, **doc.metadata}
            for doc in results
        ]
        
        response_time_ms = (time.time() - start_time) * 1000
        
        logger.info("rag_response_generated")
        if return_details:
            return content, prompt, docs_dicts, response_time_ms, tokens_used, retrieval_time_ms
        return content

if __name__ == "__main__":
    # Test script for the engine
    engine = RAGEngine()
    
    # Example question based on what we crawled earlier (detsundekoekken.dk)
    test_question = "How can I order catering?"
    
    print(f"\n--- Question: {test_question} ---\n")
    answer = engine.query(test_question)
    print(f"{answer}\n")