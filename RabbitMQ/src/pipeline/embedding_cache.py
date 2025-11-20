"""Embedding cache module for batch processing and deduplication"""
from typing import Dict, List, Set
from .embedding import create_embedding_via_clova


def extract_all_concept_names(structure: Dict) -> List[str]:
    """
    Extract all unique concept names from hierarchical structure
    
    Args:
        structure: Hierarchical structure dict with domain, categories, concepts, subconcepts
    
    Returns:
        List of unique concept names
    """
    names = set()
    
    # Domain
    domain = structure.get("domain", {})
    if domain.get("name"):
        names.add(domain["name"])
    
    # Categories
    for cat in structure.get("categories", []):
        if cat.get("name"):
            names.add(cat["name"])
        
        # Concepts
        for concept in cat.get("concepts", []):
            if concept.get("name"):
                names.add(concept["name"])
            
            # Subconcepts
            for sub in concept.get("subconcepts", []):
                if sub.get("name"):
                    names.add(sub["name"])
    
    return list(names)


def batch_create_embeddings(
    texts: List[str], 
    clova_api_key: str, 
    clova_embedding_url: str,
    batch_size: int = 50
) -> Dict[str, List[float]]:
    """
    Create embeddings for multiple texts in batches with deduplication
    
    Args:
        texts: List of text strings to embed
        clova_api_key: API key for CLOVA
        clova_embedding_url: URL for embedding API
        batch_size: Number of texts to process at once (default 50)
    
    Returns:
        Dictionary mapping text -> embedding vector
    """
    # Enhanced deduplication (case-insensitive)
    unique_texts = []
    seen = set()
    
    for text in texts:
        if text and text.strip():
            normalized = text.strip().lower()
            if normalized not in seen:
                unique_texts.append(text)
                seen.add(normalized)
    
    print(f"📊 Embedding cache: {len(texts)} texts → {len(unique_texts)} unique")
    
    embeddings_cache = {}
    failed_count = 0
    
    # Process in batches
    for i in range(0, len(unique_texts), batch_size):
        batch = unique_texts[i:i+batch_size]
        batch_end = min(i + batch_size, len(unique_texts))
        
        print(f"  ⚡ Batch {i//batch_size + 1}: Embedding {i+1}-{batch_end} of {len(unique_texts)}")
        
        for text in batch:
            try:
                embedding = create_embedding_via_clova(text, clova_api_key, clova_embedding_url)
                if embedding and len(embedding) == 384:
                    embeddings_cache[text] = embedding
                else:
                    print(f"  ⚠️  Invalid embedding for '{text[:50]}...'")
                    failed_count += 1
                    embeddings_cache[text] = [0.0] * 384
            except Exception as e:
                print(f"  ⚠️  Failed to embed '{text[:50]}...': {e}")
                failed_count += 1
                embeddings_cache[text] = [0.0] * 384
    
    success_count = len(embeddings_cache) - failed_count
    print(f"✓ Created {success_count} embeddings, {failed_count} failed")
    
    return embeddings_cache