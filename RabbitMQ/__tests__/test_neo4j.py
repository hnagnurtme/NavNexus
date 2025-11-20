"""
test_neo4j.py
Unit tests for Neo4j knowledge graph operations
Tests node creation, merging, relationships, and data retrieval
"""

import os
import sys
import uuid
import pytest
from datetime import datetime, timezone
from typing import Dict, List, Any
from unittest.mock import Mock, MagicMock, patch, call

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.model.KnowledgeNode import KnowledgeNode
from src.model.Evidence import Evidence
from src.model.GapSuggestion import GapSuggestion
from src.pipeline.neo4j_graph import (
    find_best_match,
    create_evidence_node,
    create_gap_suggestion_node,
    create_knowledge_node,
    update_knowledge_node_after_merge,
    create_or_merge_knowledge_node,
    create_parent_child_relationship,
    create_hierarchical_knowledge_graph,
    add_gap_suggestions_to_node,
    get_knowledge_node_with_evidence
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_session():
    """Create a mock Neo4j session"""
    session = Mock()
    return session


@pytest.fixture
def sample_knowledge_node():
    """Create a sample KnowledgeNode for testing"""
    return KnowledgeNode(
        Id="node-123",
        Type="concept",
        Name="Machine Learning",
        Synthesis="Methods for training models to learn from data",
        WorkspaceId="workspace-1",
        Level=2,
        SourceCount=1,
        TotalConfidence=0.95,
        CreatedAt=datetime.now(timezone.utc),
        UpdatedAt=datetime.now(timezone.utc)
    )


@pytest.fixture
def sample_evidence():
    """Create a sample Evidence for testing"""
    return Evidence(
        Id="evidence-123",
        SourceId="doc-123",
        SourceName="ML Guide.pdf",
        ChunkId="chunk-1",
        Text="Machine learning involves training algorithms on data to make predictions.",
        Page=5,
        Confidence=0.95,
        Language="ENG",
        SourceLanguage="ENG",
        HierarchyPath="/AI/Machine Learning",
        Concepts=["supervised learning", "neural networks"],
        KeyClaims=["ML uses data for predictions", "Models improve with training"],
        QuestionsRaised=["What algorithms are best?"],
        EvidenceStrength=0.9
    )


@pytest.fixture
def sample_gap_suggestion():
    """Create a sample GapSuggestion for testing"""
    return GapSuggestion(
        Id="gap-123",
        SuggestionText="Consider adding information about unsupervised learning",
        TargetNodeId="node-123",
        TargetFileId="doc-123",
        SimilarityScore=0.75
    )


@pytest.fixture
def sample_embedding():
    """Create a sample embedding vector"""
    return [0.1] * 768  # Typical embedding dimension


@pytest.fixture
def sample_hierarchical_structure():
    """Create a sample hierarchical structure for testing"""
    return {
        "domain": {
            "name": "Artificial Intelligence",
            "synthesis": "The field of creating intelligent machines and algorithms",
            "level": 1
        },
        "categories": [
            {
                "name": "Machine Learning",
                "synthesis": "Algorithms that learn from data",
                "level": 2,
                "concepts": [
                    {
                        "name": "Supervised Learning",
                        "synthesis": "Learning with labeled training data",
                        "level": 3,
                        "subconcepts": [
                            {
                                "name": "Classification",
                                "synthesis": "Predicting discrete categories",
                                "level": 4,
                                "details": []
                            }
                        ]
                    }
                ]
            }
        ]
    }


# ============================================================================
# TESTS FOR find_best_match
# ============================================================================

class TestFindBestMatch:
    def test_exact_match_found(self, mock_session):
        """Test exact name match returns correctly"""
        # Setup mock to return an exact match
        mock_result = Mock()
        mock_record = {
            'id': 'node-123',
            'name': 'Machine Learning',
            'sim': 1.0,
            'match_type': 'exact'
        }
        mock_result.single.return_value = mock_record
        mock_session.run.return_value = mock_result

        # Test
        result = find_best_match(
            mock_session,
            "workspace-1",
            "Machine Learning",
            [0.1] * 768
        )

        # Assert
        assert result is not None
        assert result['match_type'] == 'exact'
        assert result['sim'] == 1.0
        assert result['name'] == 'Machine Learning'

    def test_very_high_similarity_match(self, mock_session):
        """Test very high similarity match (>0.90)"""
        # Setup mock to return no exact match, then high similarity
        mock_exact_result = Mock()
        mock_exact_result.single.return_value = None

        mock_sim_result = Mock()
        mock_record = {
            'id': 'node-456',
            'name': 'ML Algorithms',
            'sim': 0.92,
            'match_type': 'very_high'
        }
        mock_sim_result.single.return_value = mock_record

        mock_session.run.side_effect = [mock_exact_result, mock_sim_result]

        # Test
        result = find_best_match(
            mock_session,
            "workspace-1",
            "Machine Learning Algorithms",
            [0.1] * 768
        )

        # Assert
        assert result is not None
        assert result['match_type'] == 'very_high'
        assert result['sim'] > 0.90

    def test_no_match_found(self, mock_session):
        """Test when no match is found at any threshold"""
        # Setup mock to return None for all queries
        mock_result = Mock()
        mock_result.single.return_value = None
        mock_session.run.return_value = mock_result

        # Test
        result = find_best_match(
            mock_session,
            "workspace-1",
            "Completely New Concept",
            [0.1] * 768
        )

        # Assert
        assert result is None


# ============================================================================
# TESTS FOR create_evidence_node
# ============================================================================

class TestCreateEvidenceNode:
    def test_create_evidence_node_success(self, mock_session, sample_evidence):
        """Test successful creation of Evidence node"""
        # Setup
        mock_session.run.return_value = None

        # Test
        evidence_id = create_evidence_node(mock_session, sample_evidence)

        # Assert
        assert evidence_id == sample_evidence.Id
        assert mock_session.run.called

        # Verify the Cypher query contains Evidence label
        call_args = mock_session.run.call_args[0][0]
        assert 'CREATE (e:Evidence' in call_args


# ============================================================================
# TESTS FOR create_knowledge_node
# ============================================================================

class TestCreateKnowledgeNode:
    def test_create_knowledge_node_with_evidence(
        self, mock_session, sample_knowledge_node, sample_evidence, sample_embedding
    ):
        """Test creating KnowledgeNode with linked Evidence"""
        # Setup
        mock_session.run.return_value = None

        # Test
        node_id = create_knowledge_node(
            mock_session,
            sample_knowledge_node,
            sample_evidence,
            sample_embedding
        )

        # Assert
        assert node_id == sample_knowledge_node.Id
        assert mock_session.run.call_count >= 3  # Create node, create evidence, create relationship

        # Verify calls contain expected patterns
        calls = [str(call) for call in mock_session.run.call_args_list]
        cypher_queries = [mock_session.run.call_args_list[i][0][0] for i in range(len(calls))]

        assert any('CREATE (n:KnowledgeNode' in query for query in cypher_queries)
        assert any('CREATE (e:Evidence' in query for query in cypher_queries)
        assert any('HAS_EVIDENCE' in query for query in cypher_queries)


# ============================================================================
# TESTS FOR update_knowledge_node_after_merge
# ============================================================================

class TestUpdateKnowledgeNodeAfterMerge:
    def test_update_synthesis_after_merge(self, mock_session):
        """Test updating node synthesis after merging"""
        # Setup
        mock_session.run.return_value = None

        # Test
        update_knowledge_node_after_merge(
            mock_session,
            "node-123",
            "Additional information about ML",
            "New Document.pdf"
        )

        # Assert
        assert mock_session.run.called
        call_args = mock_session.run.call_args[0][0]
        assert 'SET n.synthesis' in call_args
        assert 'n.source_count = n.source_count + 1' in call_args
        assert 'n.updated_at' in call_args


# ============================================================================
# TESTS FOR create_or_merge_knowledge_node
# ============================================================================

class TestCreateOrMergeKnowledgeNode:
    def test_create_new_node_when_no_match(
        self, mock_session, sample_knowledge_node, sample_evidence, sample_embedding
    ):
        """Test creating new node when no match is found"""
        # Setup - no match found
        with patch('src.pipeline.neo4j_graph.find_best_match', return_value=None):
            mock_session.run.return_value = None

            # Test
            node_id = create_or_merge_knowledge_node(
                mock_session,
                "workspace-1",
                sample_knowledge_node,
                sample_evidence,
                sample_embedding
            )

            # Assert
            assert node_id is not None
            assert mock_session.run.called

    def test_merge_with_existing_node(
        self, mock_session, sample_knowledge_node, sample_evidence, sample_embedding
    ):
        """Test merging with existing node when match is found"""
        # Setup - exact match found
        match_result = {
            'id': 'existing-node-123',
            'name': 'Machine Learning',
            'sim': 1.0,
            'match_type': 'exact'
        }

        with patch('src.pipeline.neo4j_graph.find_best_match', return_value=match_result):
            mock_session.run.return_value = None

            # Test
            node_id = create_or_merge_knowledge_node(
                mock_session,
                "workspace-1",
                sample_knowledge_node,
                sample_evidence,
                sample_embedding
            )

            # Assert
            assert node_id == 'existing-node-123'
            assert mock_session.run.called

    def test_skip_node_with_empty_name(
        self, mock_session, sample_knowledge_node, sample_evidence, sample_embedding
    ):
        """Test skipping node creation when name is empty"""
        # Setup
        sample_knowledge_node.Name = ""

        # Test
        node_id = create_or_merge_knowledge_node(
            mock_session,
            "workspace-1",
            sample_knowledge_node,
            sample_evidence,
            sample_embedding
        )

        # Assert
        assert node_id is None

    def test_skip_node_with_no_embedding(
        self, mock_session, sample_knowledge_node, sample_evidence
    ):
        """Test skipping node creation when embedding is missing"""
        # Test
        node_id = create_or_merge_knowledge_node(
            mock_session,
            "workspace-1",
            sample_knowledge_node,
            sample_evidence,
            []  # Empty embedding
        )

        # Assert
        assert node_id is None


# ============================================================================
# TESTS FOR create_parent_child_relationship
# ============================================================================

class TestCreateParentChildRelationship:
    def test_domain_to_category_relationship(self, mock_session):
        """Test creating domain to category relationship"""
        # Setup
        mock_session.run.return_value = None

        # Test
        create_parent_child_relationship(
            mock_session,
            "domain-123",
            "category-456",
            "domain_to_category"
        )

        # Assert
        assert mock_session.run.called
        call_args = mock_session.run.call_args[0][0]
        assert 'HAS_SUBCATEGORY' in call_args

    def test_category_to_concept_relationship(self, mock_session):
        """Test creating category to concept relationship"""
        # Setup
        mock_session.run.return_value = None

        # Test
        create_parent_child_relationship(
            mock_session,
            "category-123",
            "concept-456",
            "category_to_concept"
        )

        # Assert
        assert mock_session.run.called
        call_args = mock_session.run.call_args[0][0]
        assert 'CONTAINS_CONCEPT' in call_args

    def test_concept_to_subconcept_relationship(self, mock_session):
        """Test creating concept to subconcept relationship"""
        # Setup
        mock_session.run.return_value = None

        # Test
        create_parent_child_relationship(
            mock_session,
            "concept-123",
            "subconcept-456",
            "concept_to_subconcept"
        )

        # Assert
        assert mock_session.run.called
        call_args = mock_session.run.call_args[0][0]
        assert 'HAS_DETAIL' in call_args


# ============================================================================
# TESTS FOR create_hierarchical_knowledge_graph
# ============================================================================

class TestCreateHierarchicalKnowledgeGraph:
    def test_create_graph_from_structure(
        self, mock_session, sample_hierarchical_structure
    ):
        """Test creating hierarchical graph from structure"""
        # Setup
        mock_result = Mock()
        mock_result.single.return_value = {'initial_count': 0, 'total': 4}
        mock_session.run.return_value = mock_result

        # Create embeddings cache
        embeddings_cache = {
            "Artificial Intelligence": [0.1] * 768,
            "Machine Learning": [0.2] * 768,
            "Supervised Learning": [0.3] * 768,
            "Classification": [0.4] * 768
        }

        with patch('src.pipeline.neo4j_graph.find_best_match', return_value=None):
            # Test
            stats = create_hierarchical_knowledge_graph(
                mock_session,
                "workspace-1",
                sample_hierarchical_structure,
                "file-123",
                "AI Guide.pdf",
                embeddings_cache
            )

            # Assert
            assert stats is not None
            assert 'nodes_created' in stats
            assert 'evidence_created' in stats
            assert 'final_count' in stats
            assert stats['evidence_created'] >= 0

    def test_handle_missing_embeddings(
        self, mock_session, sample_hierarchical_structure
    ):
        """Test handling of missing embeddings in cache"""
        # Setup
        mock_result = Mock()
        mock_result.single.return_value = {'initial_count': 0, 'total': 0}
        mock_session.run.return_value = mock_result

        # Empty embeddings cache
        embeddings_cache = {}

        # Test
        stats = create_hierarchical_knowledge_graph(
            mock_session,
            "workspace-1",
            sample_hierarchical_structure,
            "file-123",
            "AI Guide.pdf",
            embeddings_cache
        )

        # Assert - should handle gracefully
        assert stats is not None
        assert stats['nodes_created'] == 0


# ============================================================================
# TESTS FOR add_gap_suggestions_to_node
# ============================================================================

class TestAddGapSuggestionsToNode:
    def test_add_single_gap_suggestion(
        self, mock_session, sample_gap_suggestion
    ):
        """Test adding a single gap suggestion to a node"""
        # Setup
        mock_session.run.return_value = None

        # Test
        add_gap_suggestions_to_node(
            mock_session,
            "node-123",
            [sample_gap_suggestion]
        )

        # Assert
        assert mock_session.run.called

    def test_add_multiple_gap_suggestions(self, mock_session):
        """Test adding multiple gap suggestions"""
        # Setup
        suggestions = [
            GapSuggestion(
                SuggestionText=f"Suggestion {i}",
                TargetNodeId="node-123",
                TargetFileId="file-123",
                SimilarityScore=0.7 + i * 0.05
            )
            for i in range(3)
        ]
        mock_session.run.return_value = None

        # Test
        add_gap_suggestions_to_node(
            mock_session,
            "node-123",
            suggestions
        )

        # Assert
        assert mock_session.run.call_count == 3


# ============================================================================
# TESTS FOR get_knowledge_node_with_evidence
# ============================================================================

class TestGetKnowledgeNodeWithEvidence:
    def test_retrieve_node_with_evidence(self, mock_session):
        """Test retrieving a node with its evidence"""
        # Setup
        mock_node_data = {
            'id': 'node-123',
            'type': 'concept',
            'name': 'Machine Learning',
            'synthesis': 'ML methods and techniques',
            'workspace_id': 'workspace-1',
            'level': 2,
            'source_count': 2,
            'total_confidence': 0.95,
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc)
        }

        mock_evidence_data = [{
            'id': 'evidence-1',
            'source_id': 'doc-1',
            'source_name': 'ML Guide.pdf',
            'chunk_id': 'chunk-1',
            'text': 'ML explanation text',
            'page': 5,
            'confidence': 0.9,
            'created_at': datetime.now(timezone.utc),
            'language': 'ENG',
            'source_language': 'ENG',
            'hierarchy_path': '/AI/ML',
            'concepts': ['supervised', 'unsupervised'],
            'key_claims': ['claim1'],
            'questions_raised': ['question1'],
            'evidence_strength': 0.85
        }]

        mock_result = Mock()
        mock_record = {'n': mock_node_data, 'evidences': mock_evidence_data}
        mock_result.single.return_value = mock_record
        mock_session.run.return_value = mock_result

        # Test
        result = get_knowledge_node_with_evidence(mock_session, "node-123")

        # Assert
        assert result is not None
        node, evidences = result
        assert isinstance(node, KnowledgeNode)
        assert node.Name == 'Machine Learning'
        assert len(evidences) == 1
        assert isinstance(evidences[0], Evidence)

    def test_retrieve_nonexistent_node(self, mock_session):
        """Test retrieving a node that doesn't exist"""
        # Setup
        mock_result = Mock()
        mock_result.single.return_value = None
        mock_session.run.return_value = mock_result

        # Test
        result = get_knowledge_node_with_evidence(mock_session, "nonexistent-node")

        # Assert
        assert result is None


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    def test_full_workflow_create_and_retrieve(
        self, mock_session, sample_knowledge_node, sample_evidence, sample_embedding
    ):
        """Test full workflow: create node and then retrieve it"""
        # Setup for creation
        with patch('src.pipeline.neo4j_graph.find_best_match', return_value=None):
            mock_session.run.return_value = None

            # Create node
            node_id = create_or_merge_knowledge_node(
                mock_session,
                "workspace-1",
                sample_knowledge_node,
                sample_evidence,
                sample_embedding
            )

            assert node_id is not None

            # Setup for retrieval
            mock_node_data = {
                'id': node_id,
                'type': sample_knowledge_node.Type,
                'name': sample_knowledge_node.Name,
                'synthesis': sample_knowledge_node.Synthesis,
                'workspace_id': sample_knowledge_node.WorkspaceId,
                'level': sample_knowledge_node.Level,
                'source_count': sample_knowledge_node.SourceCount,
                'total_confidence': sample_knowledge_node.TotalConfidence,
                'created_at': sample_knowledge_node.CreatedAt,
                'updated_at': sample_knowledge_node.UpdatedAt
            }

            mock_result = Mock()
            mock_record = {'n': mock_node_data, 'evidences': []}
            mock_result.single.return_value = mock_record
            mock_session.run.return_value = mock_result

            # Retrieve node
            result = get_knowledge_node_with_evidence(mock_session, node_id)

            # Assert
            assert result is not None
            retrieved_node, evidences = result
            assert retrieved_node.Name == sample_knowledge_node.Name


# ============================================================================
# PERFORMANCE AND EDGE CASE TESTS
# ============================================================================

class TestEdgeCases:
    def test_very_long_synthesis_text(
        self, mock_session, sample_knowledge_node, sample_evidence, sample_embedding
    ):
        """Test handling very long synthesis text"""
        # Setup
        sample_knowledge_node.Synthesis = "x" * 10000  # Very long text

        with patch('src.pipeline.neo4j_graph.find_best_match', return_value=None):
            mock_session.run.return_value = None

            # Test
            node_id = create_or_merge_knowledge_node(
                mock_session,
                "workspace-1",
                sample_knowledge_node,
                sample_evidence,
                sample_embedding
            )

            # Assert - should handle without error
            assert node_id is not None

    def test_special_characters_in_node_name(
        self, mock_session, sample_knowledge_node, sample_evidence, sample_embedding
    ):
        """Test handling special characters in node names"""
        # Setup
        sample_knowledge_node.Name = "ML & AI: A \"Comprehensive\" Guide (2024)"

        with patch('src.pipeline.neo4j_graph.find_best_match', return_value=None):
            mock_session.run.return_value = None

            # Test
            node_id = create_or_merge_knowledge_node(
                mock_session,
                "workspace-1",
                sample_knowledge_node,
                sample_evidence,
                sample_embedding
            )

            # Assert - should handle without error
            assert node_id is not None

    def test_unicode_text_in_evidence(
        self, mock_session, sample_knowledge_node, sample_evidence, sample_embedding
    ):
        """Test handling unicode text in evidence"""
        # Setup
        sample_evidence.Text = "機械学習とは、データから学習するアルゴリズムです。"

        with patch('src.pipeline.neo4j_graph.find_best_match', return_value=None):
            mock_session.run.return_value = None

            # Test
            node_id = create_or_merge_knowledge_node(
                mock_session,
                "workspace-1",
                sample_knowledge_node,
                sample_evidence,
                sample_embedding
            )

            # Assert - should handle without error
            assert node_id is not None


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
