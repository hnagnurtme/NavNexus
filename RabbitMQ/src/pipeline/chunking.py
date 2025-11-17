"""Smart chunking module"""
import re
from typing import List, Dict


def create_smart_chunks(text: str, chunk_size: int = 2000, overlap: int = 200) -> List[Dict]:
    """
    OPTIMIZED: Create overlapping chunks with semantic boundaries
    Reduced overlap from 400 to 200 (50% reduction) for better efficiency
    
    OPTIMIZATIONS:
    - Reduced overlap: 200 chars (was 400) - 50% reduction
    - Smart paragraph boundary detection
    - Preserves semantic context with minimal redundancy
    """
    chunks = []
    chunk_index = 0
    
    # Split by paragraphs and sentences for better boundaries
    paragraphs = re.split(r'\n\s*\n', text)
    current_chunk = ""
    overlap_buffer = ""
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        # Check if adding this paragraph would exceed chunk size
        if len(current_chunk) + len(para) > chunk_size and current_chunk:
            chunks.append({
                "index": chunk_index,
                "text": current_chunk,
                "overlap_previous": overlap_buffer,
                "has_more": True
            })
            
            # OPTIMIZED: Use last N chars as overlap (reduced from 400 to 200)
            # Extract last sentence or last overlap chars, whichever is shorter
            if len(current_chunk) > overlap:
                # Try to get last sentence for better semantic continuity
                sentences = re.split(r'[.!?]\s+', current_chunk)
                if len(sentences) > 1:
                    # Use last 1-2 sentences as overlap
                    overlap_buffer = '. '.join(sentences[-2:])[:overlap]
                else:
                    overlap_buffer = current_chunk[-overlap:]
            else:
                overlap_buffer = current_chunk
            
            current_chunk = para
            chunk_index += 1
        else:
            current_chunk += "\n\n" + para if current_chunk else para
    
    if current_chunk:
        chunks.append({
            "index": chunk_index,
            "text": current_chunk,
            "overlap_previous": overlap_buffer,
            "has_more": False
        })
    
    print(f"✓ Created {len(chunks)} chunks (size={chunk_size}, overlap={overlap} - optimized)")
    return chunks
