import sys
from pathlib import Path

# Add project root to Python path so 'src' can be imported when running as a script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import google.genai as genai
from src.config.settings import get_settings
from src.config.logger import get_logger
from src.embedding.gemini import GeminiEmbedder
from src.database.chroma_manager import ChromaManager

logger = get_logger(__name__)

class RAGEngine:
    def __init__(self):
        settings = get_settings()
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = settings.CHAT_MODEL
        
        # Initialize dependencies
        self.embedder = GeminiEmbedder()
        self.db = ChromaManager()
        
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

    def _format_context(self, retrieved_results) -> str:
        """Helper to format ChromaDB output into a readable string for the LLM."""
        if not retrieved_results or not retrieved_results.get("documents") or not retrieved_results["documents"][0]:
            return "No relevant context found."
            
        formatted_parts = []
        documents = retrieved_results["documents"][0]
        metadatas = retrieved_results["metadatas"][0]
        
        for doc, meta in zip(documents, metadatas):
            source = meta.get("source_url", "Unknown source")
            formatted_parts.append(f"[Source: {source}]\n{doc}\n")
            
        return "\n---\n".join(formatted_parts)

    def query(self, user_question: str, top_k: int = 5) -> str:
        """
        Retrieval-Augmented Generation standard query.
        """
        logger.info("rag_query_started", question=user_question)
        
        # 1. Embed the user's question
        question_embedding = self.embedder.generate_embeddings([user_question])[0]
        
        # 2. Retrieve relevant chunks
        results = self.db.query(query_embeddings=[question_embedding], n_results=top_k)
        
        # 3. Format context
        context_string = self._format_context(results)
        logger.debug("context_retrieved", num_chunks=len(results.get("documents", [[]])[0]))
        
        # 4. Construct prompt
        prompt = f"""
        Context Information:
        {context_string}
        
        User Question: {user_question}
        """
        
        # 5. Generate response
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=self.system_instruction,
                temperature=0.3, # Keep it mostly deterministic
            )
        )
        
        logger.info("rag_response_generated")
        return response.text

if __name__ == "__main__":
    # Test script for the engine
    engine = RAGEngine()
    
    # Example question based on what we crawled earlier (detsundekoekken.dk)
    test_question = "How can I order catering?"
    
    print(f"\n--- Question: {test_question} ---\n")
    answer = engine.query(test_question)
    print(f"{answer}\n")