"""Embedding generation module"""
import hashlib
import requests
import numpy as np
from typing import List


def create_embedding_via_clova(text: str, clova_api_key: str, clova_embedding_url: str) -> List[float]:
    """Create 384-dim embedding using CLOVA API"""
    if not text or not text.strip():
        text = "empty"
    
    text = text[:2000]
    
    headers = {
        "X-NCP-CLOVASTUDIO-API-KEY": clova_api_key,
        "X-NCP-APIGW-API-KEY": clova_api_key,
        "Content-Type": "application/json"
    }
    
    data = {"text": text}
    
    try:
        response = requests.post(clova_embedding_url, json=data, headers=headers, timeout=15)
        if response.status_code == 200:
            result = response.json()
            embedding = result.get("embedding", [])
            
            if not embedding:
                return create_hash_embedding(text)
            
            # Fixed dimension reduction using mean pooling
            if len(embedding) > 384:
                # Use mean pooling instead of sampling
                pool_size = len(embedding) // 384
                reduced = []
                for i in range(384):
                    start = i * pool_size
                    end = min((i + 1) * pool_size, len(embedding))
                    chunk = embedding[start:end]
                    reduced.append(sum(chunk) / len(chunk))
                embedding = reduced
            elif len(embedding) < 384:
                # Pad with zeros
                embedding = embedding + [0.0] * (384 - len(embedding))
            
            # Normalize
            norm = sum(x*x for x in embedding) ** 0.5
            if norm > 0:
                embedding = [x / norm for x in embedding]
            
            return embedding
    
    except Exception as e:
        print(f"⚠️ Embedding API error: {e}")
    
    return create_hash_embedding(text)


def create_hash_embedding(text: str, dim: int = 384) -> List[float]:
    """Fallback: Deterministic embedding from text hash"""
    # Enhanced hash embedding with multiple hash functions
    vectors = []
    
    # Hash 1: Full text
    h1 = hashlib.sha256(text.encode()).digest()
    v1 = [(b / 127.5) - 1.0 for b in h1[:dim//3]]
    
    # Hash 2: Normalized text
    clean_text = text.lower().strip()
    h2 = hashlib.sha256(clean_text.encode()).digest()
    v2 = [(b / 127.5) - 1.0 for b in h2[:dim//3]]
    
    # Hash 3: Text length based
    h3 = hashlib.sha256(str(len(text)).encode()).digest()
    v3 = [(b / 127.5) - 1.0 for b in h3[:dim//3]]
    
    # Combine
    embedding = v1 + v2 + v3
    if len(embedding) < dim:
        embedding += [0.0] * (dim - len(embedding))
    else:
        embedding = embedding[:dim]
    
    # Normalize
    norm = sum(x*x for x in embedding) ** 0.5
    if norm > 0:
        embedding = [x / norm for x in embedding]
    
    return embedding


def calculate_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Cosine similarity"""
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    dot_product = np.dot(v1, v2)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return float(dot_product / (norm1 * norm2))