"""Enhanced Evidence Processing Pipeline

Complete pipeline that:
1. Chunks documents with position tracking
2. Optimizes evidence using LLM (KeyClaims, QuestionsRaised)
3. Creates Evidence objects with all fields
4. Stores in Qdrant (1 evidence = 1 point)
"""

import os
from typing import List, Dict
from datetime import datetime, timezone
import uuid

from src.pipeline.chunking import create_smart_chunks
from src.pipeline.evidence_optimizer import EvidenceOptimizer
from src.model.Evidence import Evidence
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct


class EnhancedEvidencePipeline:
    """Complete pipeline for processing documents into optimized evidence"""

    def __init__(
        self,
        qdrant_client: QdrantClient,
        collection_name: str = "evidence_collection",
        embedding_dim: int = 1024,
        anthropic_api_key: str = None
    ):
        """
        Initialize pipeline

        Args:
            qdrant_client: Qdrant client instance
            collection_name: Name of Qdrant collection
            embedding_dim: Dimension of embedding vectors
            anthropic_api_key: API key for Claude
        """
        self.qdrant = qdrant_client
        self.collection_name = collection_name
        self.embedding_dim = embedding_dim
        self.optimizer = EvidenceOptimizer(api_key=anthropic_api_key)

        # Ensure collection exists
        self._ensure_collection()

    def _ensure_collection(self):
        """Create Qdrant collection if it doesn't exist"""
        try:
            collections = self.qdrant.get_collections().collections
            collection_names = [c.name for c in collections]

            if self.collection_name not in collection_names:
                print(f"📦 Creating collection: {self.collection_name}")
                self.qdrant.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dim,
                        distance=Distance.COSINE
                    )
                )
                print(f"✓ Collection created successfully")
        except Exception as e:
            print(f"⚠️  Error ensuring collection: {e}")

    def process_document(
        self,
        document: Dict,
        chunk_size: int = 2000,
        overlap: int = 400,
        optimize_with_llm: bool = True,
        embedding_function=None
    ) -> List[Evidence]:
        """
        Process a document through the complete pipeline

        Args:
            document: Document dict with keys:
                - id: Document ID
                - title: Document title
                - source: Source file/URL
                - content: Full text content
                - language: Language code (optional)
                - page: Page number (optional)
            chunk_size: Target chunk size
            overlap: Overlap between chunks
            optimize_with_llm: Whether to use LLM for optimization
            embedding_function: Function to generate embeddings

        Returns:
            List of Evidence objects created
        """
        print(f"\n{'='*80}")
        print(f"📄 Processing document: {document.get('title', 'Untitled')}")
        print(f"{'='*80}\n")

        # Step 1: Chunk with position tracking
        print("🔪 Step 1: Chunking with position tracking...")
        chunks = create_smart_chunks(
            text=document["content"],
            chunk_size=chunk_size,
            overlap=overlap
        )
        print(f"  ✓ Created {len(chunks)} chunks\n")

        # Step 2: Optimize with LLM (optional)
        if optimize_with_llm:
            print("🤖 Step 2: Optimizing evidence with LLM...")
            source_info = {
                "title": document.get("title", ""),
                "source": document.get("source", ""),
                "type": document.get("type", "document")
            }
            optimized_chunks = self.optimizer.batch_optimize(
                chunks=chunks,
                source_info=source_info,
                show_progress=True
            )
            print(f"  ✓ Optimized {len(optimized_chunks)} chunks\n")
        else:
            print("⏭️  Step 2: Skipping LLM optimization\n")
            optimized_chunks = chunks
            # Add empty fields if not optimized
            for chunk in optimized_chunks:
                chunk["optimized_text"] = chunk["text"]
                chunk["key_claims"] = []
                chunk["questions_raised"] = []

        # Step 3: Create Evidence objects
        print("📝 Step 3: Creating Evidence objects...")
        evidences = []
        for chunk in optimized_chunks:
            evidence = Evidence(
                Id=f"{document['id']}_CHUNK_{chunk['index']}",
                SourceId=document["id"],
                SourceName=document.get("title", ""),
                ChunkId=str(chunk["index"]),
                Text=chunk["optimized_text"],
                Page=document.get("page", 0),
                Language=document.get("language", "ENG"),
                SourceLanguage=document.get("language", "ENG"),

                # Position tracking
                StartPos=chunk["start_pos"],
                EndPos=chunk["end_pos"],
                ChunkIndex=chunk["index"],
                HasMore=chunk["has_more"],
                OverlapLength=len(chunk.get("overlap_previous", "")),

                # LLM-generated fields
                KeyClaims=chunk.get("key_claims", []),
                QuestionsRaised=chunk.get("questions_raised", []),

                # Metadata
                Confidence=1.0 if optimize_with_llm else 0.8,
                EvidenceStrength=0.0,  # Can be calculated later
                CreatedAt=datetime.now(timezone.utc)
            )
            evidences.append(evidence)

        print(f"  ✓ Created {len(evidences)} Evidence objects\n")

        # Step 4: Store in Qdrant
        if embedding_function:
            print("💾 Step 4: Storing in Qdrant...")
            self._store_evidences(evidences, embedding_function)
            print(f"  ✓ Stored {len(evidences)} evidences in Qdrant\n")
        else:
            print("⏭️  Step 4: Skipping Qdrant storage (no embedding function)\n")

        print(f"{'='*80}")
        print(f"✅ Pipeline completed successfully!")
        print(f"{'='*80}\n")

        return evidences

    def _store_evidences(self, evidences: List[Evidence], embedding_function):
        """Store evidences in Qdrant as points"""
        points = []

        for evidence in evidences:
            # Generate embedding
            embedding = embedding_function(evidence.Text)

            # Create payload with all fields
            payload = {
                "id": evidence.Id,
                "source_id": evidence.SourceId,
                "source_name": evidence.SourceName,
                "chunk_id": evidence.ChunkId,
                "text": evidence.Text,
                "page": evidence.Page,
                "confidence": evidence.Confidence,
                "language": evidence.Language,
                "source_language": evidence.SourceLanguage,
                "hierarchy_path": evidence.HierarchyPath,

                # Position fields
                "start_pos": evidence.StartPos,
                "end_pos": evidence.EndPos,
                "chunk_index": evidence.ChunkIndex,
                "has_more": evidence.HasMore,
                "overlap_length": evidence.OverlapLength,

                # LLM-generated fields
                "key_claims": evidence.KeyClaims,
                "questions_raised": evidence.QuestionsRaised,
                "concepts": evidence.Concepts,

                # Metadata
                "evidence_strength": evidence.EvidenceStrength,
                "created_at": evidence.CreatedAt.isoformat()
            }

            # Create point
            point = PointStruct(
                id=str(uuid.uuid4()),  # Qdrant point ID
                vector=embedding,
                payload=payload
            )
            points.append(point)

        # Batch upsert to Qdrant
        self.qdrant.upsert(
            collection_name=self.collection_name,
            points=points
        )

        print(f"  ✓ Uploaded {len(points)} points to Qdrant")

    def search_evidences(
        self,
        query: str,
        embedding_function,
        limit: int = 5,
        filter_conditions: Dict = None
    ) -> List[Dict]:
        """
        Search for evidences using semantic search

        Args:
            query: Search query
            embedding_function: Function to embed query
            limit: Max number of results
            filter_conditions: Qdrant filter conditions

        Returns:
            List of evidence results with scores
        """
        query_vector = embedding_function(query)

        results = self.qdrant.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit,
            query_filter=filter_conditions
        )

        return [
            {
                "score": hit.score,
                "evidence": hit.payload,
                "position": {
                    "start": hit.payload.get("start_pos", 0),
                    "end": hit.payload.get("end_pos", 0)
                }
            }
            for hit in results
        ]


def create_mock_embedding(text: str) -> List[float]:
    """Mock embedding function for testing (replace with real embeddings)"""
    import hashlib
    import numpy as np

    # Generate deterministic embedding based on text hash
    hash_obj = hashlib.md5(text.encode())
    seed = int(hash_obj.hexdigest(), 16) % (2**32)
    np.random.seed(seed)

    return np.random.rand(1024).tolist()


# Example usage
if __name__ == "__main__":
    # Initialize pipeline
    qdrant_client = QdrantClient(host="localhost", port=6333)
    pipeline = EnhancedEvidencePipeline(
        qdrant_client=qdrant_client,
        collection_name="evidence_test",
        embedding_dim=1024
    )

    # Sample document
    document = {
        "id": "DOC_2024_001",
        "title": "Economic Report 2024",
        "source": "report.pdf",
        "type": "report",
        "language": "VIE",
        "page": 1,
        "content": """Tổng quan kinh tế năm 2024

Trong năm 2024, nền kinh tế Việt Nam đã đạt được nhiều thành tựu đáng kể. GDP tăng trưởng 6.5% so với năm trước, vượt mục tiêu đề ra.

Lạm phát được kiểm soát ở mức 3.2%, thấp hơn dự báo ban đầu. Điều này cho thấy hiệu quả của các chính sách tiền tệ.

Kim ngạch xuất khẩu đạt 400 tỷ USD, tăng 8% so với cùng kỳ năm trước."""
    }

    # Process document
    evidences = pipeline.process_document(
        document=document,
        chunk_size=300,
        overlap=80,
        optimize_with_llm=True,
        embedding_function=create_mock_embedding
    )

    # Print results
    print("\n📊 EVIDENCE RESULTS:\n")
    for i, evidence in enumerate(evidences, 1):
        print(f"Evidence {i}:")
        print(f"  ID: {evidence.Id}")
        print(f"  Position: [{evidence.StartPos}:{evidence.EndPos}]")
        print(f"  Text: {evidence.Text[:100]}...")
        print(f"  KeyClaims: {len(evidence.KeyClaims)}")
        print(f"  Questions: {len(evidence.QuestionsRaised)}")
        print()
