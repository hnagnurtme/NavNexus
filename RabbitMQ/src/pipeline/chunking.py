"""Smart chunking module"""
import re
from typing import List, Dict


def create_smart_chunks(text: str, chunk_size: int = 2000, overlap: int = 400) -> List[Dict]:
    """Create overlapping chunks with semantic boundaries"""
    chunks = []
    chunk_index = 0
    
    paragraphs = re.split(r'\n\s*\n', text)
    current_chunk = ""
    overlap_buffer = ""
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        if len(current_chunk) + len(para) > chunk_size and current_chunk:
            chunks.append({
                "index": chunk_index,
                "text": current_chunk,
                "overlap_previous": overlap_buffer,
                "has_more": True
            })
            
            overlap_buffer = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
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
    
    print(f"✓ Created {len(chunks)} chunks (size={chunk_size}, overlap={overlap})")
    return chunks
