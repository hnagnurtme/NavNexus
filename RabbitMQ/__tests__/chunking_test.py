"""
chunking_test.py
Test script for Enhanced Smart Chunking Module
"""

import os
from datetime import datetime
from typing import List, Dict

# Import the chunking module
from ..src.pipeline.chunking import create_smart_chunks, calculate_chunk_stats

def load_test_text(file_path: str) -> str:
    """
    Load a test text file for chunking.
    If file is PDF, use a PDF extractor (here we simulate with .txt)
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def test_chunking(text: str):
    """
    Run smart chunking on the input text and display results
    """
    print(f"\n📄 Running smart chunking test ({len(text)} characters)...")
    
    chunks: List[Dict] = create_smart_chunks(
        text=text,
        chunk_size=2000,
        overlap=400,
        min_chunk_size=200
    )
    
    stats = calculate_chunk_stats(chunks)
    
    print(f"\n📊 Chunking Summary:")
    print(f"   - Total chunks: {stats.get('total_chunks', 0)}")
    print(f"   - Avg chunk size: {stats.get('avg_size', 0):.0f} chars")
    print(f"   - Min chunk size: {stats.get('min_size', 0)} chars")
    print(f"   - Max chunk size: {stats.get('max_size', 0)} chars")
    print(f"   - Total chars: {stats.get('total_chars', 0)}")
    
    # Print first few chunks
    print("\n📝 Sample chunks:")
    for chunk in chunks[:3]:
        print(f"--- Chunk {chunk['index']} (len={len(chunk['text'])}) ---")
        print(chunk['text'][:500].replace('\n', ' '))
        print("...")


def main():
    # Example: test with a sample text file
    test_file = "/Users/anhnon/NavNexus/RabbitMQ/__tests__/GAP_extracted_text.txt"  # Replace with your PDF converted to text
    text = load_test_text(test_file)
    
    start_time = datetime.now()
    test_chunking(text)
    end_time = datetime.now()
    
    print(f"\n⏱️  Chunking test completed in {(end_time - start_time).total_seconds():.2f} seconds.")


if __name__ == "__main__":
    main()
