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
        response = requests.post(clova_embedding_url, json=data, headers=headers, timeout=10)
        if response.status_code == 200:
            result = response.json()
            embedding = result.get("embedding", [])
            
            if len(embedding) >= 384:
                step = len(embedding) // 384
                reduced = [embedding[i] for i in range(0, len(embedding), step)][:384]
                
                norm = sum(x*x for x in reduced) ** 0.5
                if norm > 0:
                    reduced = [x / norm for x in reduced]
                
                return reduced
            
            return embedding
    
    except Exception as e:
        print(f"⚠ Embedding API error: {e}")
    
    return create_hash_embedding(text)


def create_hash_embedding(text: str, dim: int = 384) -> List[float]:
    """Fallback: Deterministic embedding from text hash"""
    hashes = []
    for i in range(dim // 32 + 1):
        h = hashlib.sha256(f"{text}_{i}".encode()).digest()
        hashes.extend(h)
    
    embedding = [(b / 127.5) - 1.0 for b in hashes[:dim]]
    
    norm = sum(x*x for x in embedding) ** 0.5
    if norm > 0:
        embedding = [x / norm for x in embedding]
    
    return embedding


def calculate_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Cosine similarity"""
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
