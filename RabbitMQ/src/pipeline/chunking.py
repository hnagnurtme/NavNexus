"""Enhanced smart chunking module with semantic boundaries"""
import re
from typing import List, Dict


def create_smart_chunks(
    text: str, 
    chunk_size: int = 2000, 
    overlap: int = 400,
    min_chunk_size: int = 200
) -> List[Dict]:
    """
    Create overlapping chunks with semantic boundaries
    
    Args:
        text: Input text to chunk
        chunk_size: Target chunk size in characters
        overlap: Overlap size between chunks
        min_chunk_size: Minimum chunk size to avoid too small chunks
    
    Returns:
        List of chunk dictionaries with text and metadata
    """
    if not text or not text.strip():
        return []
    
    # Normalize text - replace multiple newlines
    text = re.sub(r'\n\s*\n', '\n\n', text.strip())
    
    # Split into paragraphs while preserving boundaries
    paragraphs = []
    for para in re.split(r'(\n\s*\n)', text):
        if para.strip():
            paragraphs.append(para.strip())
    
    if not paragraphs:
        return []
    
    chunks = []
    current_chunk = ""
    chunk_index = 0
    
    i = 0
    while i < len(paragraphs):
        paragraph = paragraphs[i]
        
        # Case 1: Single paragraph is larger than chunk_size
        if len(paragraph) > chunk_size:
            # Split long paragraph into sentences
            sentences = re.split(r'[.!?]+', paragraph)
            sentence_chunk = ""
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                    
                if len(sentence_chunk) + len(sentence) > chunk_size and sentence_chunk:
                    # Save current sentence chunk
                    chunks.append({
                        "index": chunk_index,
                        "text": sentence_chunk.strip(),
                        "overlap_previous": "",
                        "has_more": True
                    })
                    chunk_index += 1
                    
                    # Start new chunk with overlap from previous
                    overlap_text = get_semantic_overlap(sentence_chunk, overlap)
                    sentence_chunk = overlap_text + " " + sentence if overlap_text else sentence
                else:
                    sentence_chunk += " " + sentence if sentence_chunk else sentence
            
            if sentence_chunk:
                current_chunk = sentence_chunk
                i += 1
                
        # Case 2: Add paragraph to current chunk
        elif len(current_chunk) + len(paragraph) <= chunk_size or not current_chunk:
            current_chunk += "\n\n" + paragraph if current_chunk else paragraph
            i += 1
            
        # Case 3: Current chunk is full, save it
        else:
            # Ensure chunk meets minimum size requirement
            if len(current_chunk) >= min_chunk_size:
                chunks.append({
                    "index": chunk_index,
                    "text": current_chunk.strip(),
                    "overlap_previous": get_semantic_overlap(current_chunk, overlap),
                    "has_more": True
                })
                chunk_index += 1
                
                # Start new chunk with overlap from previous
                overlap_text = get_semantic_overlap(current_chunk, overlap)
                current_chunk = overlap_text + "\n\n" + paragraph if overlap_text else paragraph
                i += 1
            else:
                # Continue adding to current chunk even if it exceeds target size
                current_chunk += "\n\n" + paragraph
                i += 1
    
    # Add the final chunk
    if current_chunk and len(current_chunk) >= min_chunk_size:
        chunks.append({
            "index": chunk_index,
            "text": current_chunk.strip(),
            "overlap_previous": get_semantic_overlap(current_chunk, overlap),
            "has_more": False
        })
    
    # Post-process: Ensure chunks aren't too small (merge small chunks)
    chunks = merge_small_chunks(chunks, min_chunk_size)
    
    print(f"✓ Created {len(chunks)} chunks (size={chunk_size}, overlap={overlap})")
    return chunks


def get_semantic_overlap(text: str, overlap_size: int) -> str:
    """
    Extract overlap text that respects semantic boundaries
    
    Args:
        text: Text to extract overlap from
        overlap_size: Target overlap size in characters
    
    Returns:
        Overlap text that ends at sentence/paragraph boundary
    """
    if len(text) <= overlap_size:
        return text
    
    # Try to find sentence boundary
    overlap_candidate = text[-overlap_size:]
    
    # Look for sentence endings within the last 20% of overlap
    search_range = min(overlap_size // 5, 100)
    for i in range(len(overlap_candidate) - search_range, len(overlap_candidate)):
        if i < 0:
            continue
        if overlap_candidate[i] in '.!?':
            return overlap_candidate[:i+1].strip()
    
    # Look for paragraph boundary (double newline)
    double_newline_pos = overlap_candidate.find('\n\n')
    if double_newline_pos != -1:
        return overlap_candidate[double_newline_pos:].strip()
    
    # Look for single newline
    newline_pos = overlap_candidate.find('\n')
    if newline_pos != -1:
        return overlap_candidate[newline_pos:].strip()
    
    # Fallback: return the exact overlap (may cut words)
    return overlap_candidate


def merge_small_chunks(chunks: List[Dict], min_size: int) -> List[Dict]:
    """
    Merge chunks that are too small with their neighbors
    
    Args:
        chunks: List of chunk dictionaries
        min_size: Minimum chunk size requirement
    
    Returns:
        Merged chunks list
    """
    if not chunks:
        return []
    
    merged_chunks = []
    i = 0
    
    while i < len(chunks):
        current_chunk = chunks[i]
        
        # If chunk is large enough, keep it as is
        if len(current_chunk['text']) >= min_size or i == len(chunks) - 1:
            merged_chunks.append(current_chunk)
            i += 1
        else:
            # Merge with next chunk
            if i + 1 < len(chunks):
                next_chunk = chunks[i + 1]
                merged_text = current_chunk['text'] + "\n\n" + next_chunk['text']
                
                merged_chunks.append({
                    "index": current_chunk['index'],
                    "text": merged_text,
                    "overlap_previous": current_chunk['overlap_previous'],
                    "has_more": next_chunk['has_more']
                })
                i += 2  # Skip next chunk since we merged it
            else:
                merged_chunks.append(current_chunk)
                i += 1
    
    # Update indices
    for idx, chunk in enumerate(merged_chunks):
        chunk['index'] = idx
        if idx == len(merged_chunks) - 1:
            chunk['has_more'] = False
    
    return merged_chunks


def calculate_chunk_stats(chunks: List[Dict]) -> Dict:
    """
    Calculate statistics about chunks
    
    Args:
        chunks: List of chunk dictionaries
    
    Returns:
        Dictionary with chunk statistics
    """
    if not chunks:
        return {}
    
    sizes = [len(chunk['text']) for chunk in chunks]
    
    return {
        "total_chunks": len(chunks),
        "avg_size": sum(sizes) / len(sizes),
        "min_size": min(sizes),
        "max_size": max(sizes),
        "total_chars": sum(sizes)
    }