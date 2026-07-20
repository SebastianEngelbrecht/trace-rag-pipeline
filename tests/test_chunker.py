import pytest
from src.ingestion.chunker import TextChunker

def test_clean_text():
    chunker = TextChunker()
    # Test basic cleaning
    raw_text = "This is a   sentence.\n\n\nIt has  too much whitespace."
    clean_text = chunker._clean_text(raw_text)
    assert clean_text == "This is a sentence. It has too much whitespace."

def test_split_text():
    chunker = TextChunker(chunk_size=10, overlap=2)
    text = "This is a long sentence that should be split."
    chunks = chunker.split_text(text)
    
    assert len(chunks) > 1
    assert "This is a" in chunks[0]

def test_process_crawled_data():
    chunker = TextChunker(chunk_size=50, overlap=0)
    mock_data = {
        "https://example.com": "This is valid text that needs chunking. A lot of good information here."
    }
    
    processed = chunker.process_crawled_data(mock_data)
    
    assert len(processed) > 0
    assert processed[0]["source_url"] == "https://example.com"
    assert "content" in processed[0]
    assert "chunk_id" in processed[0]
    assert "chunk_index" in processed[0]
    assert processed[0]["chunk_index"] == 0