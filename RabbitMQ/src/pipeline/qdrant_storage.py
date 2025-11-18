"""Qdrant vector storage module"""
from urllib.parse import quote
from typing import List, Tuple
from dataclasses import asdict

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct, PayloadSchemaType

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
        print(f"✓ Created collection: {collection_name}")
    
    return collection_name


def store_chunks_in_qdrant(qdrant_client: QdrantClient, workspace_id: str, 
                          chunks_with_embeddings: List[Tuple[QdrantChunk, List[float]]]):
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