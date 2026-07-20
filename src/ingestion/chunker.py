# CHUNKER - TEXT SPLITTING AND CHUNKING
import asyncio
import re
import uuid
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Dict



class TextChunker:
    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

        # Corrected spelling of separators and removed duplicates
        self.separators = ["\n\n", "\n", " ", ""]
        
        # Initialize the production-ready splitter engine
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.overlap,
            separators=self.separators
        )

    def _clean_text(self, text: str) -> str:
        """
        A professional, language-agnostic layout filter.
        Removes structural website noise (headers/footers) based on text density
        and punctuation markers rather than hardcoded word lists.
        """
        if not text:
            return ""
        
        lines = text.split("\n")
        cleaned_lines = []
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
                
            # 1. Structural Filter: Drop single-word or tiny lines that don't end in punctuation.
            # (Captures standard navigation links like "Home", "Pricing", "About Us")
            words = stripped.split()
            has_punctuation = any(char in stripped for char in {'.', '?', '!', ':', ','})
            
            if len(words) <= 3 and not has_punctuation:
                continue
                
            # 2. Ratio Filter: Real conversational/informative text has an average word length.
            # Stray layout pieces are often long combined strings or weird character symbols.
            if len(stripped) > 100 and len(words) < 4:
                continue
                
            cleaned_lines.append(stripped)
            
        # Reconstruct as plain flowing text to avoid escaped newlines in JSON output.
        normalized_text = " ".join(cleaned_lines)
        # Collapse all repeated whitespace (spaces/tabs/newlines) to one space.
        normalized_text = re.sub(r"\s+", " ", normalized_text)
        
        return normalized_text.strip()

    def _generate_chunk_id(self, source_url: str, chunk_index: int) -> str:
        """Generates a stable deterministic UUID based on the URL and chunk index."""
        # Using uuid5 with a namespace ensures that the same URL + index combination
        # always generates the exact same UUID string.
        unique_string = f"{source_url}::chunk::{chunk_index}"
        return str(uuid.uuid5(uuid.NAMESPACE_URL, unique_string))

    def split_text(self, text: str) -> List[str]:
        """Splits a single text string into chunks using the LangChain engine."""
        cleaned_text = self._clean_text(text)
        # Leverage the native splitter directly instead of using a custom loop
        return self.text_splitter.split_text(cleaned_text)
    
    def process_crawled_data(self, crawled_results: Dict[str, str]) -> List[dict]:
        """
        Processes the raw crawler map.
        Returns a flat list of highly structured chunks ready for embedding.
        """
        all_processed_chunks = []

        for url, raw_text in crawled_results.items():
            if not raw_text.strip():
                continue  # Skip empty or whitespace-only text

            text_chunks = self.split_text(raw_text)

            for index, chunk_text in enumerate(text_chunks):
                all_processed_chunks.append({
                    "chunk_id": self._generate_chunk_id(url, index),
                    "chunk_index": index,
                    "source_url": url,
                    "content": chunk_text,
                    "token_estimate": len(chunk_text) // 4  # Rough estimate: 1 token ≈ 4 characters
                })
        return all_processed_chunks
    
if __name__ == "__main__":
    try:
        from src.ingestion.crawler import AsyncCrawler
    except ModuleNotFoundError:
        # Allows running from within src/ingestion as: python chunker.py
        from crawler import AsyncCrawler

    async def local_pipeline_test():
        target_site = "https://detsundekoekken.dk"
        print(f"--- STEP 1: Crawling target site: {target_site} ---")

        crawler = AsyncCrawler(target_site, max_depth=3, max_concurrency=5)
        raw_crawled_data = await crawler.crawl()

        print(f"\n--- STEP 2: Chunking crawled data ---")
        # Using small constraints to test chunking splits locally
        chunker = TextChunker(chunk_size=500, overlap=50)
        chunked_output = chunker.process_crawled_data(raw_crawled_data)

        print(f"Total pages crawled: {len(raw_crawled_data)}")
        print(f"Total database-ready chunks created: {len(chunked_output)}")

        if chunked_output:
            print("\n--- SAMPLE CHUNK METADATA AND CONTENT INSPECTION ---")
            import json
            print(json.dumps(chunked_output[0], indent=2, ensure_ascii=False))

    asyncio.run(local_pipeline_test())