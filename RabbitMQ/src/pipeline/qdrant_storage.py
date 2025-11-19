"""Enhanced Qdrant vector storage with robust operations"""
from urllib.parse import quote
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import asdict
import time

from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams, Distance, PointStruct, PayloadSchemaType,
    Filter, FieldCondition, MatchValue, SearchRequest
)
from qdrant_client.http.exceptions import UnexpectedResponse

from ..model.QdrantChunk import QdrantChunk


def ensure_collection_exists(
    qdrant_client: QdrantClient, 
    workspace_id: str,
    vector_size: int = 384
) -> str:
    """
    Ensure Qdrant collection exists with proper configuration
    
    Args:
        qdrant_client: Qdrant client instance
        workspace_id: Workspace identifier
        vector_size: Expected vector dimension
    
    Returns:
        Collection name
    """
    collection_name = f"workspace_{quote(workspace_id)}"
    
    try:
        # Check if collection exists and has correct configuration
        collection_exists = qdrant_client.collection_exists(collection_name)
        
        if not collection_exists:
            # Create new collection
            qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
                timeout=60
            )
            
            # Create payload indexes for efficient filtering
            qdrant_client.create_payload_index(
                collection_name=collection_name,
                field_name="workspace_id",
                field_schema=PayloadSchemaType.KEYWORD
            )
            
            qdrant_client.create_payload_index(
                collection_name=collection_name,
                field_name="paper_id", 
                field_schema=PayloadSchemaType.KEYWORD
            )
            
            qdrant_client.create_payload_index(
                collection_name=collection_name,
                field_name="chunk_index",
                field_schema=PayloadSchemaType.INTEGER
            )
            
            print(f"✓ Created collection: {collection_name} (dim={vector_size})")
            
        else:
            # Verify collection configuration
            collection_info = qdrant_client.get_collection(collection_name)
            current_size = getattr(collection_info.config.params.vectors, 'size', None)
            if current_size is None:
                raise ValueError(f"Collection {collection_name} does not have a valid vector size configuration")
            
            if current_size != vector_size:
                print(f"⚠️  Collection {collection_name} has wrong vector size: {current_size} != {vector_size}")
                # In production, you might want to recreate the collection
                # For now, we'll proceed with a warning
        
        return collection_name
        
    except Exception as e:
        raise RuntimeError(f"Failed to ensure collection exists: {e}")


def validate_embedding(embedding: List[float], expected_size: int = 384) -> bool:
    """Validate embedding dimensions and values"""
    if not embedding:
        return False
    
    if len(embedding) != expected_size:
        print(f"⚠️  Invalid embedding dimension: {len(embedding)} != {expected_size}")
        return False
    
    # Check for all-zero vectors (likely errors)
    if all(abs(x) < 1e-6 for x in embedding):
        print("⚠️  Warning: All-zero embedding vector")
        return False
    
    return True


def store_chunks_in_qdrant(
    qdrant_client: QdrantClient, 
    workspace_id: str, 
    chunks_with_embeddings: List[Tuple[QdrantChunk, List[float]]],
    batch_size: int = 100,
    max_retries: int = 3
) -> Dict[str, Any]:
    """
    Store chunks with embeddings in Qdrant with enhanced error handling
    
    Args:
        qdrant_client: Qdrant client instance
        workspace_id: Workspace identifier  
        chunks_with_embeddings: List of (chunk, embedding) tuples
        batch_size: Number of points to upsert in one batch
        max_retries: Maximum number of retry attempts
    
    Returns:
        Dictionary with operation results and statistics
    """
    if not chunks_with_embeddings:
        return {"success": False, "error": "No chunks provided", "stored_count": 0}
    
    collection_name = ensure_collection_exists(qdrant_client, workspace_id)
    
    stats = {
        "total_chunks": len(chunks_with_embeddings),
        "valid_embeddings": 0,
        "invalid_embeddings": 0,
        "stored_count": 0,
        "failed_count": 0,
        "batches_processed": 0
    }
    
    # Prepare points with validation
    points = []
    invalid_chunks = []
    
    for chunk, embedding in chunks_with_embeddings:
        if validate_embedding(embedding):
            points.append(PointStruct(
                id=chunk.chunk_id,
                vector=embedding,
                payload=asdict(chunk)
            ))
            stats["valid_embeddings"] += 1
        else:
            invalid_chunks.append(chunk.chunk_id)
            stats["invalid_embeddings"] += 1
    
    if not points:
        return {"success": False, "error": "No valid embeddings", "stats": stats}
    
    # Batch processing with retry logic
    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        
        for attempt in range(max_retries):
            try:
                operation_info = qdrant_client.upsert(
                    collection_name=collection_name,
                    points=batch,
                    wait=True  # Wait for commit
                )
                
                stats["stored_count"] += len(batch)
                stats["batches_processed"] += 1
                print(f"✓ Batch {batch_num}: Stored {len(batch)} chunks")
                break
                
            except Exception as e:
                print(f"⚠️  Batch {batch_num} attempt {attempt + 1} failed: {e}")
                
                if attempt == max_retries - 1:
                    stats["failed_count"] += len(batch)
                    print(f"❌ Failed to store batch {batch_num} after {max_retries} attempts")
                else:
                    # Exponential backoff
                    time.sleep(2 ** attempt)
    
    success = stats["stored_count"] > 0
    if invalid_chunks:
        print(f"⚠️  {len(invalid_chunks)} chunks had invalid embeddings and were skipped")
    
    return {
        "success": success,
        "stats": stats,
        "collection": collection_name
    }


def search_similar_chunks(
    qdrant_client: QdrantClient,
    workspace_id: str,
    query_embedding: List[float],
    limit: int = 10,
    score_threshold: float = 0.7,
    filter_by_paper_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Search for similar chunks in Qdrant
    
    Args:
        qdrant_client: Qdrant client instance
        workspace_id: Workspace identifier
        query_embedding: Query embedding vector
        limit: Maximum number of results
        score_threshold: Minimum similarity score
        filter_by_paper_id: Optional paper ID filter
    
    Returns:
        List of search results with scores and payloads
    """
    if not validate_embedding(query_embedding):
        return []
    
    collection_name = f"workspace_{quote(workspace_id)}"
    
    try:
        # Build filter
        filter_conditions: List[FieldCondition] = [
            FieldCondition(
                key="workspace_id",
                match=MatchValue(value=workspace_id)
            )
        ]
        
        if filter_by_paper_id:
            filter_conditions.append(
                FieldCondition(
                    key="paper_id",
                    match=MatchValue(value=filter_by_paper_id)
                )
            )
        
        search_filter = Filter(must=list(filter_conditions)) if filter_conditions else None
        
        # Perform search
        search_results = qdrant_client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            query_filter=search_filter,
            limit=limit,
            score_threshold=score_threshold
        )
        
        # Convert to readable format
        results = []
        for hit in search_results:
            results.append({
                "id": hit.id,
                "score": hit.score,
                "payload": hit.payload,
                "vector": hit.vector
            })
        
        return results
        
    except Exception as e:
        print(f"❌ Search failed: {e}")
        return []


def get_collection_stats(
    qdrant_client: QdrantClient,
    workspace_id: str
) -> Dict[str, Any]:
    """
    Get statistics for a workspace collection
    
    Args:
        qdrant_client: Qdrant client instance
        workspace_id: Workspace identifier
    
    Returns:
        Collection statistics
    """
    collection_name = f"workspace_{quote(workspace_id)}"
    
    try:
        if not qdrant_client.collection_exists(collection_name):
            return {"error": "Collection does not exist"}
        
        collection_info = qdrant_client.get_collection(collection_name)
        counts = qdrant_client.count(collection_name)
        
        return {
            "collection_name": collection_name,
            "vectors_count": counts.count,
            "vectors_dimension": getattr(collection_info.config.params.vectors, 'size', None),
            "distance_metric": str(getattr(collection_info.config.params.vectors, 'distance', 'unknown')),
            "status": collection_info.status
        }
        
    except Exception as e:
        return {"error": f"Failed to get stats: {e}"}


def delete_workspace_collection(
    qdrant_client: QdrantClient,
    workspace_id: str
) -> bool:
    """
    Delete a workspace collection
    
    Args:
        qdrant_client: Qdrant client instance
        workspace_id: Workspace identifier
    
    Returns:
        Success status
    """
    collection_name = f"workspace_{quote(workspace_id)}"
    
    try:
        if qdrant_client.collection_exists(collection_name):
            qdrant_client.delete_collection(collection_name)
            print(f"✓ Deleted collection: {collection_name}")
            return True
        else:
            print(f"ℹ️  Collection {collection_name} does not exist")
            return True
            
    except Exception as e:
        print(f"❌ Failed to delete collection: {e}")
        return False