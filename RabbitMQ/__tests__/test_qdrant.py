"""
test_qdrant.py
Unit tests for Qdrant vector storage operations
Tests collection management, chunk storage, search, and validation
"""

import os
import sys
import uuid
import pytest
from typing import List, Tuple, Dict, Any
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.model.QdrantChunk import QdrantChunk
from src.pipeline.qdrant_storage import (
    ensure_collection_exists,
    validate_embedding,
    store_chunks_in_qdrant,
    search_similar_chunks,
    get_collection_stats,
    delete_workspace_collection
)
from qdrant_client.models import (
    VectorParams, Distance, PointStruct, CollectionInfo,
    CollectionStatus, Filter, FieldCondition, MatchValue
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_qdrant_client():
    """Create a mock Qdrant client"""
    client = Mock()
    return client


@pytest.fixture
def sample_workspace_id():
    """Sample workspace ID for testing"""
    return "test-workspace-123"


@pytest.fixture
def sample_embedding():
    """Create a sample embedding vector (384 dimensions)"""
    return [0.1] * 384


@pytest.fixture
def sample_embedding_wrong_size():
    """Create an embedding with wrong dimensions"""
    return [0.1] * 512


@pytest.fixture
def sample_zero_embedding():
    """Create an all-zero embedding"""
    return [0.0] * 384


@pytest.fixture
def sample_qdrant_chunk():
    """Create a sample QdrantChunk for testing"""
    return QdrantChunk(
        chunk_id="chunk-123",
        paper_id="paper-456",
        page=5,
        text="This is a sample text chunk about machine learning algorithms.",
        summary="Machine learning algorithms overview",
        concepts=["machine learning", "algorithms", "neural networks"],
        topic="Machine Learning",
        workspace_id="test-workspace-123",
        language="ENG",
        source_language="ENG",
        created_at=datetime.now().isoformat(),
        hierarchy_path="/AI/Machine Learning/Algorithms",
        chunk_index=0,
        prev_chunk_id="",
        next_chunk_id="chunk-124",
        semantic_similarity_prev=0.0,
        overlap_with_prev="",
        key_claims=["ML algorithms can learn from data"],
        questions_raised=["What are the best algorithms for classification?"],
        evidence_strength=0.85
    )


@pytest.fixture
def sample_chunks_with_embeddings(sample_qdrant_chunk, sample_embedding):
    """Create a list of chunks with embeddings"""
    chunks = []
    for i in range(5):
        chunk = QdrantChunk(
            chunk_id=f"chunk-{i}",
            paper_id="paper-456",
            page=i + 1,
            text=f"Sample text chunk {i}",
            summary=f"Summary {i}",
            concepts=["concept1", "concept2"],
            topic="Test Topic",
            workspace_id="test-workspace-123",
            language="ENG",
            source_language="ENG",
            created_at=datetime.now().isoformat(),
            hierarchy_path="/Test/Path",
            chunk_index=i,
            prev_chunk_id=f"chunk-{i-1}" if i > 0 else "",
            next_chunk_id=f"chunk-{i+1}" if i < 4 else "",
            semantic_similarity_prev=0.8 if i > 0 else 0.0,
            overlap_with_prev="",
            key_claims=[f"Claim {i}"],
            questions_raised=[],
            evidence_strength=0.9
        )
        # Vary embeddings slightly
        embedding = [0.1 + i * 0.01] * 384
        chunks.append((chunk, embedding))
    return chunks


# ============================================================================
# TESTS FOR ensure_collection_exists
# ============================================================================

class TestEnsureCollectionExists:
    def test_create_new_collection(self, mock_qdrant_client, sample_workspace_id):
        """Test creating a new collection when it doesn't exist"""
        # Setup
        mock_qdrant_client.collection_exists.return_value = False
        mock_qdrant_client.create_collection.return_value = None
        mock_qdrant_client.create_payload_index.return_value = None

        # Test
        collection_name = ensure_collection_exists(
            mock_qdrant_client,
            sample_workspace_id,
            vector_size=384
        )

        # Assert
        assert collection_name == f"workspace_{sample_workspace_id}"
        mock_qdrant_client.collection_exists.assert_called_once()
        mock_qdrant_client.create_collection.assert_called_once()

        # Verify collection was created with correct parameters
        create_call = mock_qdrant_client.create_collection.call_args
        assert create_call[1]['collection_name'] == f"workspace_{sample_workspace_id}"

        # Verify payload indexes were created
        assert mock_qdrant_client.create_payload_index.call_count == 3

    def test_use_existing_collection_with_correct_size(
        self, mock_qdrant_client, sample_workspace_id
    ):
        """Test using existing collection with correct vector size"""
        # Setup
        mock_qdrant_client.collection_exists.return_value = True

        # Mock collection info
        mock_vectors_config = Mock()
        mock_vectors_config.size = 384

        mock_params = Mock()
        mock_params.vectors = mock_vectors_config

        mock_config = Mock()
        mock_config.params = mock_params

        mock_collection_info = Mock()
        mock_collection_info.config = mock_config

        mock_qdrant_client.get_collection.return_value = mock_collection_info

        # Test
        collection_name = ensure_collection_exists(
            mock_qdrant_client,
            sample_workspace_id,
            vector_size=384
        )

        # Assert
        assert collection_name == f"workspace_{sample_workspace_id}"
        mock_qdrant_client.collection_exists.assert_called_once()
        mock_qdrant_client.get_collection.assert_called_once()
        mock_qdrant_client.create_collection.assert_not_called()

    def test_existing_collection_with_wrong_size(
        self, mock_qdrant_client, sample_workspace_id
    ):
        """Test warning when existing collection has wrong vector size"""
        # Setup
        mock_qdrant_client.collection_exists.return_value = True

        # Mock collection info with wrong size
        mock_vectors_config = Mock()
        mock_vectors_config.size = 512  # Wrong size

        mock_params = Mock()
        mock_params.vectors = mock_vectors_config

        mock_config = Mock()
        mock_config.params = mock_params

        mock_collection_info = Mock()
        mock_collection_info.config = mock_config

        mock_qdrant_client.get_collection.return_value = mock_collection_info

        # Test - should proceed with warning
        collection_name = ensure_collection_exists(
            mock_qdrant_client,
            sample_workspace_id,
            vector_size=384
        )

        # Assert
        assert collection_name == f"workspace_{sample_workspace_id}"

    def test_collection_creation_failure(
        self, mock_qdrant_client, sample_workspace_id
    ):
        """Test handling of collection creation failure"""
        # Setup
        mock_qdrant_client.collection_exists.return_value = False
        mock_qdrant_client.create_collection.side_effect = Exception("Creation failed")

        # Test
        with pytest.raises(RuntimeError, match="Failed to ensure collection exists"):
            ensure_collection_exists(
                mock_qdrant_client,
                sample_workspace_id,
                vector_size=384
            )


# ============================================================================
# TESTS FOR validate_embedding
# ============================================================================

class TestValidateEmbedding:
    def test_valid_embedding(self, sample_embedding):
        """Test validation of a valid embedding"""
        assert validate_embedding(sample_embedding, expected_size=384) is True

    def test_empty_embedding(self):
        """Test validation of empty embedding"""
        assert validate_embedding([], expected_size=384) is False

    def test_wrong_dimension(self, sample_embedding_wrong_size):
        """Test validation of embedding with wrong dimensions"""
        assert validate_embedding(sample_embedding_wrong_size, expected_size=384) is False

    def test_all_zero_embedding(self, sample_zero_embedding):
        """Test validation of all-zero embedding"""
        assert validate_embedding(sample_zero_embedding, expected_size=384) is False

    def test_none_embedding(self):
        """Test validation of None embedding"""
        assert validate_embedding(None, expected_size=384) is False

    def test_custom_dimension_size(self):
        """Test validation with custom dimension size"""
        embedding_768 = [0.1] * 768
        assert validate_embedding(embedding_768, expected_size=768) is True
        assert validate_embedding(embedding_768, expected_size=384) is False


# ============================================================================
# TESTS FOR store_chunks_in_qdrant
# ============================================================================

class TestStoreChunksInQdrant:
    def test_store_chunks_successfully(
        self, mock_qdrant_client, sample_workspace_id, sample_chunks_with_embeddings
    ):
        """Test successful storage of chunks with embeddings"""
        # Setup
        mock_qdrant_client.collection_exists.return_value = True

        # Mock collection info
        mock_vectors_config = Mock()
        mock_vectors_config.size = 384
        mock_params = Mock()
        mock_params.vectors = mock_vectors_config
        mock_config = Mock()
        mock_config.params = mock_params
        mock_collection_info = Mock()
        mock_collection_info.config = mock_config
        mock_qdrant_client.get_collection.return_value = mock_collection_info

        mock_qdrant_client.upsert.return_value = Mock()

        # Test
        result = store_chunks_in_qdrant(
            mock_qdrant_client,
            sample_workspace_id,
            sample_chunks_with_embeddings,
            batch_size=100
        )

        # Assert
        assert result["success"] is True
        assert result["stats"]["total_chunks"] == 5
        assert result["stats"]["valid_embeddings"] == 5
        assert result["stats"]["invalid_embeddings"] == 0
        assert result["stats"]["stored_count"] == 5
        assert result["stats"]["failed_count"] == 0
        mock_qdrant_client.upsert.assert_called_once()

    def test_store_empty_chunks_list(
        self, mock_qdrant_client, sample_workspace_id
    ):
        """Test storing empty list of chunks"""
        # Test
        result = store_chunks_in_qdrant(
            mock_qdrant_client,
            sample_workspace_id,
            [],
            batch_size=100
        )

        # Assert
        assert result["success"] is False
        assert result["error"] == "No chunks provided"
        assert result["stored_count"] == 0

    def test_store_chunks_with_invalid_embeddings(
        self, mock_qdrant_client, sample_workspace_id, sample_qdrant_chunk
    ):
        """Test storing chunks where some have invalid embeddings"""
        # Setup
        chunks_with_embeddings = [
            (sample_qdrant_chunk, [0.1] * 384),  # Valid
            (sample_qdrant_chunk, [0.0] * 384),  # Invalid (all zeros)
            (sample_qdrant_chunk, [0.1] * 512),  # Invalid (wrong size)
        ]

        mock_qdrant_client.collection_exists.return_value = True
        mock_vectors_config = Mock()
        mock_vectors_config.size = 384
        mock_params = Mock()
        mock_params.vectors = mock_vectors_config
        mock_config = Mock()
        mock_config.params = mock_params
        mock_collection_info = Mock()
        mock_collection_info.config = mock_config
        mock_qdrant_client.get_collection.return_value = mock_collection_info
        mock_qdrant_client.upsert.return_value = Mock()

        # Test
        result = store_chunks_in_qdrant(
            mock_qdrant_client,
            sample_workspace_id,
            chunks_with_embeddings,
            batch_size=100
        )

        # Assert
        assert result["success"] is True
        assert result["stats"]["total_chunks"] == 3
        assert result["stats"]["valid_embeddings"] == 1
        assert result["stats"]["invalid_embeddings"] == 2
        assert result["stats"]["stored_count"] == 1

    def test_batch_processing(
        self, mock_qdrant_client, sample_workspace_id, sample_chunks_with_embeddings
    ):
        """Test batch processing with small batch size"""
        # Setup
        mock_qdrant_client.collection_exists.return_value = True
        mock_vectors_config = Mock()
        mock_vectors_config.size = 384
        mock_params = Mock()
        mock_params.vectors = mock_vectors_config
        mock_config = Mock()
        mock_config.params = mock_params
        mock_collection_info = Mock()
        mock_collection_info.config = mock_config
        mock_qdrant_client.get_collection.return_value = mock_collection_info
        mock_qdrant_client.upsert.return_value = Mock()

        # Test with batch size of 2
        result = store_chunks_in_qdrant(
            mock_qdrant_client,
            sample_workspace_id,
            sample_chunks_with_embeddings,
            batch_size=2
        )

        # Assert - should have 3 batches (5 chunks / 2 batch_size = 3 batches)
        assert result["success"] is True
        assert result["stats"]["batches_processed"] == 3
        assert mock_qdrant_client.upsert.call_count == 3

    def test_retry_on_failure(
        self, mock_qdrant_client, sample_workspace_id, sample_chunks_with_embeddings
    ):
        """Test retry logic on upsert failure"""
        # Setup
        mock_qdrant_client.collection_exists.return_value = True
        mock_vectors_config = Mock()
        mock_vectors_config.size = 384
        mock_params = Mock()
        mock_params.vectors = mock_vectors_config
        mock_config = Mock()
        mock_config.params = mock_params
        mock_collection_info = Mock()
        mock_collection_info.config = mock_config
        mock_qdrant_client.get_collection.return_value = mock_collection_info

        # Fail twice, then succeed
        mock_qdrant_client.upsert.side_effect = [
            Exception("Temporary error"),
            Exception("Temporary error"),
            Mock()  # Success on third attempt
        ]

        # Test
        result = store_chunks_in_qdrant(
            mock_qdrant_client,
            sample_workspace_id,
            sample_chunks_with_embeddings,
            batch_size=100,
            max_retries=3
        )

        # Assert
        assert result["success"] is True
        assert mock_qdrant_client.upsert.call_count == 3

    def test_max_retries_exceeded(
        self, mock_qdrant_client, sample_workspace_id, sample_chunks_with_embeddings
    ):
        """Test when max retries are exceeded"""
        # Setup
        mock_qdrant_client.collection_exists.return_value = True
        mock_vectors_config = Mock()
        mock_vectors_config.size = 384
        mock_params = Mock()
        mock_params.vectors = mock_vectors_config
        mock_config = Mock()
        mock_config.params = mock_params
        mock_collection_info = Mock()
        mock_collection_info.config = mock_config
        mock_qdrant_client.get_collection.return_value = mock_collection_info

        # Always fail
        mock_qdrant_client.upsert.side_effect = Exception("Persistent error")

        # Test
        result = store_chunks_in_qdrant(
            mock_qdrant_client,
            sample_workspace_id,
            sample_chunks_with_embeddings,
            batch_size=100,
            max_retries=3
        )

        # Assert
        assert result["success"] is False
        assert result["stats"]["failed_count"] == 5
        assert result["stats"]["stored_count"] == 0


# ============================================================================
# TESTS FOR search_similar_chunks
# ============================================================================

class TestSearchSimilarChunks:
    def test_search_success(
        self, mock_qdrant_client, sample_workspace_id, sample_embedding
    ):
        """Test successful search for similar chunks"""
        # Setup mock search results
        mock_hit1 = Mock()
        mock_hit1.id = "chunk-1"
        mock_hit1.score = 0.95
        mock_hit1.payload = {"text": "Result 1", "paper_id": "paper-1"}
        mock_hit1.vector = [0.1] * 384

        mock_hit2 = Mock()
        mock_hit2.id = "chunk-2"
        mock_hit2.score = 0.88
        mock_hit2.payload = {"text": "Result 2", "paper_id": "paper-1"}
        mock_hit2.vector = [0.2] * 384

        mock_qdrant_client.search.return_value = [mock_hit1, mock_hit2]

        # Test
        results = search_similar_chunks(
            mock_qdrant_client,
            sample_workspace_id,
            sample_embedding,
            limit=10,
            score_threshold=0.7
        )

        # Assert
        assert len(results) == 2
        assert results[0]["id"] == "chunk-1"
        assert results[0]["score"] == 0.95
        assert results[1]["id"] == "chunk-2"
        assert results[1]["score"] == 0.88
        mock_qdrant_client.search.assert_called_once()

    def test_search_with_paper_filter(
        self, mock_qdrant_client, sample_workspace_id, sample_embedding
    ):
        """Test search with paper ID filter"""
        # Setup
        mock_qdrant_client.search.return_value = []

        # Test
        results = search_similar_chunks(
            mock_qdrant_client,
            sample_workspace_id,
            sample_embedding,
            limit=10,
            score_threshold=0.7,
            filter_by_paper_id="paper-123"
        )

        # Assert
        mock_qdrant_client.search.assert_called_once()
        call_args = mock_qdrant_client.search.call_args

        # Verify filter was applied
        assert call_args[1]['query_filter'] is not None

    def test_search_with_invalid_embedding(
        self, mock_qdrant_client, sample_workspace_id
    ):
        """Test search with invalid embedding returns empty results"""
        # Test with all-zero embedding
        results = search_similar_chunks(
            mock_qdrant_client,
            sample_workspace_id,
            [0.0] * 384,
            limit=10,
            score_threshold=0.7
        )

        # Assert
        assert results == []
        mock_qdrant_client.search.assert_not_called()

    def test_search_failure(
        self, mock_qdrant_client, sample_workspace_id, sample_embedding
    ):
        """Test handling of search failure"""
        # Setup
        mock_qdrant_client.search.side_effect = Exception("Search failed")

        # Test
        results = search_similar_chunks(
            mock_qdrant_client,
            sample_workspace_id,
            sample_embedding,
            limit=10,
            score_threshold=0.7
        )

        # Assert
        assert results == []

    def test_search_no_results(
        self, mock_qdrant_client, sample_workspace_id, sample_embedding
    ):
        """Test search with no matching results"""
        # Setup
        mock_qdrant_client.search.return_value = []

        # Test
        results = search_similar_chunks(
            mock_qdrant_client,
            sample_workspace_id,
            sample_embedding,
            limit=10,
            score_threshold=0.95  # High threshold
        )

        # Assert
        assert results == []


# ============================================================================
# TESTS FOR get_collection_stats
# ============================================================================

class TestGetCollectionStats:
    def test_get_stats_success(self, mock_qdrant_client, sample_workspace_id):
        """Test successful retrieval of collection statistics"""
        # Setup
        mock_qdrant_client.collection_exists.return_value = True

        # Mock collection info
        mock_vectors_config = Mock()
        mock_vectors_config.size = 384
        mock_vectors_config.distance = Distance.COSINE

        mock_params = Mock()
        mock_params.vectors = mock_vectors_config

        mock_config = Mock()
        mock_config.params = mock_params

        mock_collection_info = Mock()
        mock_collection_info.config = mock_config
        mock_collection_info.status = CollectionStatus.GREEN

        mock_qdrant_client.get_collection.return_value = mock_collection_info

        # Mock count
        mock_count_result = Mock()
        mock_count_result.count = 150
        mock_qdrant_client.count.return_value = mock_count_result

        # Test
        stats = get_collection_stats(mock_qdrant_client, sample_workspace_id)

        # Assert
        assert stats["collection_name"] == f"workspace_{sample_workspace_id}"
        assert stats["vectors_count"] == 150
        assert stats["vectors_dimension"] == 384
        assert stats["status"] == CollectionStatus.GREEN

    def test_get_stats_collection_not_exists(
        self, mock_qdrant_client, sample_workspace_id
    ):
        """Test getting stats for non-existent collection"""
        # Setup
        mock_qdrant_client.collection_exists.return_value = False

        # Test
        stats = get_collection_stats(mock_qdrant_client, sample_workspace_id)

        # Assert
        assert "error" in stats
        assert stats["error"] == "Collection does not exist"

    def test_get_stats_failure(self, mock_qdrant_client, sample_workspace_id):
        """Test handling of stats retrieval failure"""
        # Setup
        mock_qdrant_client.collection_exists.side_effect = Exception("Connection error")

        # Test
        stats = get_collection_stats(mock_qdrant_client, sample_workspace_id)

        # Assert
        assert "error" in stats
        assert "Failed to get stats" in stats["error"]


# ============================================================================
# TESTS FOR delete_workspace_collection
# ============================================================================

class TestDeleteWorkspaceCollection:
    def test_delete_existing_collection(
        self, mock_qdrant_client, sample_workspace_id
    ):
        """Test deleting an existing collection"""
        # Setup
        mock_qdrant_client.collection_exists.return_value = True
        mock_qdrant_client.delete_collection.return_value = None

        # Test
        result = delete_workspace_collection(mock_qdrant_client, sample_workspace_id)

        # Assert
        assert result is True
        mock_qdrant_client.delete_collection.assert_called_once()

    def test_delete_nonexistent_collection(
        self, mock_qdrant_client, sample_workspace_id
    ):
        """Test deleting a collection that doesn't exist"""
        # Setup
        mock_qdrant_client.collection_exists.return_value = False

        # Test
        result = delete_workspace_collection(mock_qdrant_client, sample_workspace_id)

        # Assert
        assert result is True
        mock_qdrant_client.delete_collection.assert_not_called()

    def test_delete_collection_failure(
        self, mock_qdrant_client, sample_workspace_id
    ):
        """Test handling of collection deletion failure"""
        # Setup
        mock_qdrant_client.collection_exists.return_value = True
        mock_qdrant_client.delete_collection.side_effect = Exception("Deletion failed")

        # Test
        result = delete_workspace_collection(mock_qdrant_client, sample_workspace_id)

        # Assert
        assert result is False


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    def test_full_workflow_store_and_search(
        self, mock_qdrant_client, sample_workspace_id,
        sample_chunks_with_embeddings, sample_embedding
    ):
        """Test full workflow: store chunks and then search"""
        # Setup for storage
        mock_qdrant_client.collection_exists.return_value = True
        mock_vectors_config = Mock()
        mock_vectors_config.size = 384
        mock_params = Mock()
        mock_params.vectors = mock_vectors_config
        mock_config = Mock()
        mock_config.params = mock_params
        mock_collection_info = Mock()
        mock_collection_info.config = mock_config
        mock_qdrant_client.get_collection.return_value = mock_collection_info
        mock_qdrant_client.upsert.return_value = Mock()

        # Store chunks
        store_result = store_chunks_in_qdrant(
            mock_qdrant_client,
            sample_workspace_id,
            sample_chunks_with_embeddings,
            batch_size=100
        )

        assert store_result["success"] is True

        # Setup for search
        mock_hit = Mock()
        mock_hit.id = "chunk-0"
        mock_hit.score = 0.95
        mock_hit.payload = {"text": "Sample text chunk 0"}
        mock_hit.vector = sample_embedding

        mock_qdrant_client.search.return_value = [mock_hit]

        # Search
        search_results = search_similar_chunks(
            mock_qdrant_client,
            sample_workspace_id,
            sample_embedding,
            limit=10,
            score_threshold=0.7
        )

        # Assert
        assert len(search_results) > 0
        assert search_results[0]["id"] == "chunk-0"


# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================

class TestEdgeCases:
    def test_very_large_batch(
        self, mock_qdrant_client, sample_workspace_id, sample_qdrant_chunk, sample_embedding
    ):
        """Test handling very large batch of chunks"""
        # Create 1000 chunks
        large_batch = [
            (sample_qdrant_chunk, sample_embedding) for _ in range(1000)
        ]

        # Setup
        mock_qdrant_client.collection_exists.return_value = True
        mock_vectors_config = Mock()
        mock_vectors_config.size = 384
        mock_params = Mock()
        mock_params.vectors = mock_vectors_config
        mock_config = Mock()
        mock_config.params = mock_params
        mock_collection_info = Mock()
        mock_collection_info.config = mock_config
        mock_qdrant_client.get_collection.return_value = mock_collection_info
        mock_qdrant_client.upsert.return_value = Mock()

        # Test
        result = store_chunks_in_qdrant(
            mock_qdrant_client,
            sample_workspace_id,
            large_batch,
            batch_size=100
        )

        # Assert
        assert result["success"] is True
        assert result["stats"]["total_chunks"] == 1000
        # Should have 10 batches (1000 / 100)
        assert result["stats"]["batches_processed"] == 10

    def test_unicode_in_chunk_text(
        self, mock_qdrant_client, sample_workspace_id, sample_embedding
    ):
        """Test handling unicode characters in chunk text"""
        # Create chunk with unicode text (using French with special chars and emojis)
        unicode_chunk = QdrantChunk(
            chunk_id="unicode-chunk",
            paper_id="paper-unicode",
            page=1,
            text="Machine learning with special characters: emojis and symbols",
            summary="Resume with accents",
            concepts=["apprentissage", "AI"],
            topic="Technology",
            workspace_id=sample_workspace_id,
            language="FRA",
            source_language="FRA",
            created_at=datetime.now().isoformat(),
            hierarchy_path="/Technology/AI",
            chunk_index=0,
            evidence_strength=0.9
        )

        # Setup
        mock_qdrant_client.collection_exists.return_value = True
        mock_vectors_config = Mock()
        mock_vectors_config.size = 384
        mock_params = Mock()
        mock_params.vectors = mock_vectors_config
        mock_config = Mock()
        mock_config.params = mock_params
        mock_collection_info = Mock()
        mock_collection_info.config = mock_config
        mock_qdrant_client.get_collection.return_value = mock_collection_info
        mock_qdrant_client.upsert.return_value = Mock()

        # Test
        result = store_chunks_in_qdrant(
            mock_qdrant_client,
            sample_workspace_id,
            [(unicode_chunk, sample_embedding)],
            batch_size=100
        )

        # Assert - should handle without error
        assert result["success"] is True

    def test_special_characters_in_workspace_id(self, mock_qdrant_client):
        """Test handling special characters in workspace ID"""
        special_workspace_id = "test-workspace-@#$%"

        # Setup
        mock_qdrant_client.collection_exists.return_value = False
        mock_qdrant_client.create_collection.return_value = None
        mock_qdrant_client.create_payload_index.return_value = None

        # Test
        collection_name = ensure_collection_exists(
            mock_qdrant_client,
            special_workspace_id,
            vector_size=384
        )

        # Assert - should handle URL encoding
        assert "workspace_" in collection_name


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
