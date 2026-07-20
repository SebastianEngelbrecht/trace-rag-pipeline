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
        os.environ["GOOGLE_API_KEY"] = settings.GEMINI_API_KEY
        self.model_name = settings.CHAT_MODEL
        
        # Initialize dependencies
        self.db = ChromaManager()
        
        # Initialize Langchain components
        self.embeddings = GoogleGenerativeAIEmbeddings(model=settings.EMBEDDING_MODEL)
        self.llm = ChatGoogleGenerativeAI(
            model=settings.CHAT_MODEL,
            temperature=0.3,
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

        return [doc_map[doc_id] for _, doc_id in reranked_results]

    def _get_hybrid_results(self, user_question: str, top_k: int = 5) -> list[Document]:
        """Gets results from BM25 and Vector matching and fuses them."""
        
        # 1. Setup Vector Retriever
        vector_retriever = self.vector_store.as_retriever(search_kwargs={"k": top_k})
        vector_results = vector_retriever.invoke(user_question)
        
        # 2. Setup BM25 Retriever
        all_data = self.db.collection.get()
        if not all_data or not all_data.get('documents'):
            return vector_results
            
        docs = []
        for doc_content, metadata in zip(all_data['documents'], all_data['metadatas']):
             # Reconstruct Langchain Document objects
             docs.append(Document(page_content=doc_content, metadata=metadata or {}))
             
        bm25_retriever = BM25Retriever.from_documents(docs)
        bm25_retriever.k = top_k
        bm25_results = bm25_retriever.invoke(user_question)
        
        # 3. Fuse Results
        fused_results = self._reciprocal_rank_fusion([vector_results, bm25_results])
        return fused_results[:top_k]

    def _format_context(self, retrieved_docs) -> str:
        """Helper to format LangChain Document output into a readable string for the LLM."""
        if not retrieved_docs:
            return "No relevant context found."
            
        formatted_parts = []
        
        for doc in retrieved_docs:
            source = doc.metadata.get("source_url", "Unknown source")
            formatted_parts.append(f"[Source: {source}]\n{doc.page_content}\n")
            
        return "\n---\n".join(formatted_parts)

    def query(self, user_question: str, top_k: int = 5) -> str:
        """
        Retrieval-Augmented Generation using custom Hybrid Search.
        """
        logger.info("rag_query_started", question=user_question)
        
        # 1. Get Hybrid Results
        results = self._get_hybrid_results(user_question, top_k=top_k)
        
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
        
        # 5. Generate response using LangChain LLM
        response = self.llm.invoke(prompt)
        content = response.content
        if isinstance(content, list):
            content = "".join(block.get("text", "") if isinstance(block, dict) else str(block) for block in content)
        else:
            content = str(content)
        
        logger.info("rag_response_generated")
        return content

if __name__ == "__main__":
    # Test script for the engine
    engine = RAGEngine()
    
    # Example question based on what we crawled earlier (detsundekoekken.dk)
    test_question = "How can I order catering?"
    
    print(f"\n--- Question: {test_question} ---\n")
    answer = engine.query(test_question)
    print(f"{answer}\n")