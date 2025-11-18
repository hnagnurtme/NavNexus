"""Optimized Qdrant vector storage with smart fallback search"""
from urllib.parse import quote
from typing import List, Tuple, Dict, Any
from dataclasses import asdict

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct, PayloadSchemaType, Filter, FieldCondition, MatchText

from ..model.QdrantChunk import QdrantChunk


def ensure_collection_exists(qdrant_client: QdrantClient, workspace_id: str):
    """Ensure Qdrant collection exists for workspace"""
    collection_name = f"workspace_{quote(workspace_id)}"
    
    if not qdrant_client.collection_exists(collection_name):
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )
        
        qdrant_client.create_payload_index(
            collection_name=collection_name,
            field_name="workspace_id",
            field_schema=PayloadSchemaType.KEYWORD
        )
        
        qdrant_client.create_payload_index(
            collection_name=collection_name,
            field_name="text",
            field_schema=PayloadSchemaType.TEXT
        )
        
        print(f"✓ Created collection: {collection_name}")
    
    return collection_name


def store_chunks_in_qdrant(
    qdrant_client: QdrantClient, 
    workspace_id: str, 
    chunks_with_embeddings: List[Tuple[QdrantChunk, List[float]]]
):
    """Store chunks with embeddings in Qdrant"""
    
    collection_name = ensure_collection_exists(qdrant_client, workspace_id)
    
    # Batch upload
    points = []
    for chunk, embedding in chunks_with_embeddings:
        points.append(PointStruct(
            id=chunk.chunk_id,
            vector=embedding,
            payload=asdict(chunk)
        ))
    
    if points:
        qdrant_client.upsert(collection_name, points=points)
        print(f"✓ Stored {len(points)} chunks in Qdrant")
    
    return len(points)


def smart_search_with_fallback(
    qdrant_client: QdrantClient,
    collection_name: str,
    query_vector: List[float],
    query_text: str = "",
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Multi-stage search with graceful degradation
    
    STRATEGY:
    1. High confidence: threshold 0.75
    2. Medium confidence: threshold 0.60
    3. Low confidence: threshold 0.40
    4. Fallback: Return top N by any similarity
    5. Last resort: Keyword search on query_text
    
    Args:
        qdrant_client: Qdrant client instance
        collection_name: Name of the collection to search
        query_vector: Query embedding vector
        query_text: Original query text for keyword fallback
        limit: Number of results to return
    
    Returns:
        List of results with score, payload, and confidence level
    """
    
    # Check if collection exists
    try:
        if not qdrant_client.collection_exists(collection_name):
            print(f"⚠️  Collection '{collection_name}' does not exist")
            return []
    except Exception as e:
        print(f"⚠️  Error checking collection: {e}")
        return []
    
    # Stage 1: High confidence (threshold 0.75)
    try:
        results = qdrant_client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            score_threshold=0.75
        )
        
        if len(results) >= 3:  # Got enough good results
            return [{
                'score': r.score,
                'payload': r.payload,
                'confidence': 'high'
            } for r in results]
    except Exception as e:
        print(f"  ⚠️  High confidence search error: {e}")
    
    # Stage 2: Medium confidence (threshold 0.60)
    try:
        results = qdrant_client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            score_threshold=0.60
        )
        
        if len(results) >= 2:
            return [{
                'score': r.score,
                'payload': r.payload,
                'confidence': 'medium'
            } for r in results]
    except Exception as e:
        print(f"  ⚠️  Medium confidence search error: {e}")
    
    # Stage 3: Low confidence (threshold 0.40)
    try:
        results = qdrant_client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            score_threshold=0.40
        )
        
        if len(results) >= 1:
            return [{
                'score': r.score,
                'payload': r.payload,
                'confidence': 'low'
            } for r in results]
    except Exception as e:
        print(f"  ⚠️  Low confidence search error: {e}")
    
    # Stage 4: No threshold - just return top N
    try:
        results = qdrant_client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit * 2  # Double the limit for fallback
        )
        
        if results:
            return [{
                'score': r.score,
                'payload': r.payload,
                'confidence': 'fallback'
            } for r in results[:limit]]
    except Exception as e:
        print(f"  ⚠️  Fallback search error: {e}")
    
    # Stage 5: Last resort - keyword search
    if query_text:
        try:
            # Extract keywords (simple word splitting)
            keywords = [w.strip() for w in query_text.split() if len(w.strip()) > 3][:5]
            
            if keywords:
                # Try scrolling with filter on text field
                scroll_result = qdrant_client.scroll(
                    collection_name=collection_name,
                    limit=limit,
                    with_payload=True,
                    with_vectors=False
                )
                
                points, _ = scroll_result
                
                if points:
                    # Simple keyword matching in payloads
                    matched = []
                    for point in points:
                        payload_text = str(point.payload.get('text', '')).lower()
                        summary_text = str(point.payload.get('summary', '')).lower()
                        combined = payload_text + ' ' + summary_text
                        
                        # Check if any keyword appears
                        if any(kw.lower() in combined for kw in keywords):
                            matched.append({
                                'score': 0.3,  # Low artificial score
                                'payload': point.payload,
                                'confidence': 'keyword'
                            })
                        
                        if len(matched) >= limit:
                            break
                    
                    if matched:
                        return matched[:limit]
        except Exception as e:
            print(f"  ⚠️  Keyword search error: {e}")
    
    # Absolute last resort: Return empty with warning
    print(f"⚠️  WARNING: No results found for query, returning empty")
    return []
