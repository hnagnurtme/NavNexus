# seed_data.py
import json
from datetime import datetime
from typing import List, Dict, Any
from neo4j import GraphDatabase

class KnowledgeNode:
    def __init__(self, data: Dict[str, Any]):
        self.Id = data['Id']
        self.Type = data['Type']
        self.Name = data['Name']
        self.Synthesis = data['Synthesis']
        self.WorkspaceId = data['WorkspaceId']
        self.Level = data['Level']
        self.SourceCount = data['SourceCount']
        self.TotalConfidence = data['TotalConfidence']
        self.CreatedAt = data['CreatedAt']
        self.UpdatedAt = data['UpdatedAt']
        self.ParentId = data.get('ParentId')

class Evidence:
    def __init__(self, data: Dict[str, Any]):
        self.Id = data['Id']
        self.NodeId = data['NodeId']
        self.SourceId = data['SourceId']
        self.SourceName = data['SourceName']
        self.ChunkId = data['ChunkId']
        self.Text = data['Text']
        self.Page = data.get('Page', 0)
        self.Confidence = data.get('Confidence', 0.0)
        self.CreatedAt = data['CreatedAt']
        self.Language = data['Language']
        self.SourceLanguage = data['SourceLanguage']
        self.HierarchyPath = data.get('HierarchyPath', '')
        self.Concepts = data.get('Concepts', [])
        self.KeyClaims = data.get('KeyClaims', [])
        self.QuestionsRaised = data.get('QuestionsRaised', [])
        self.EvidenceStrength = data.get('EvidenceStrength', 0.0)

class GapSuggestion:
    def __init__(self, data: Dict[str, Any]):
        self.Id = data['Id']
        self.NodeId = data['NodeId']
        self.SuggestionText = data['SuggestionText']
        self.TargetNodeId = data['TargetNodeId']
        self.TargetFileId = data.get('TargetFileId', '')
        self.SimilarityScore = data.get('SimilarityScore', 0.0)

class Neo4jConnection:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(
            uri, 
            auth=(user, password),
            max_connection_lifetime=3600,
            max_connection_pool_size=50,
            connection_acquisition_timeout=60
        )
    
    def close(self):
        self.driver.close()
    
    def get_session(self):
        return self.driver.session()

def create_knowledge_node(session, knowledge_node: KnowledgeNode) -> str:
    """Create KnowledgeNode với MERGE để tránh duplicate"""
    result = session.run(
        """
        MERGE (n:KnowledgeNode {id: $id})
        SET n.type = $type,
            n.name = $name,
            n.synthesis = $synthesis,
            n.workspace_id = $workspace_id,
            n.level = $level,
            n.source_count = $source_count,
            n.total_confidence = $total_confidence,
            n.created_at = $created_at,
            n.updated_at = $updated_at
        RETURN n.id
        """,
        id=knowledge_node.Id,
        type=knowledge_node.Type,
        name=knowledge_node.Name,
        synthesis=knowledge_node.Synthesis,
        workspace_id=knowledge_node.WorkspaceId,
        level=knowledge_node.Level,
        source_count=knowledge_node.SourceCount,
        total_confidence=knowledge_node.TotalConfidence,
        created_at=knowledge_node.CreatedAt,
        updated_at=knowledge_node.UpdatedAt
    )
    return result.single()[0]

def create_evidence_node(session, evidence: Evidence) -> str:
    """Create Evidence node với MERGE để tránh duplicate"""
    result = session.run(
        """
        MERGE (e:Evidence {id: $id})
        SET e.source_id = $source_id,
            e.source_name = $source_name,
            e.chunk_id = $chunk_id,
            e.text = $text,
            e.page = $page,
            e.confidence = $confidence,
            e.created_at = $created_at,
            e.language = $language,
            e.source_language = $source_language,
            e.hierarchy_path = $hierarchy_path,
            e.concepts = $concepts,
            e.key_claims = $key_claims,
            e.questions_raised = $questions_raised,
            e.evidence_strength = $evidence_strength
        WITH e
        MATCH (n:KnowledgeNode {id: $node_id})
        MERGE (n)-[:HAS_EVIDENCE]->(e)
        RETURN e.id
        """,
        id=evidence.Id,
        source_id=evidence.SourceId,
        source_name=evidence.SourceName,
        chunk_id=evidence.ChunkId,
        text=evidence.Text,
        page=evidence.Page,
        confidence=evidence.Confidence,
        created_at=evidence.CreatedAt,
        language=evidence.Language,
        source_language=evidence.SourceLanguage,
        hierarchy_path=evidence.HierarchyPath,
        concepts=evidence.Concepts,
        key_claims=evidence.KeyClaims,
        questions_raised=evidence.QuestionsRaised,
        evidence_strength=evidence.EvidenceStrength,
        node_id=evidence.NodeId
    )
    return result.single()[0]

def create_gap_suggestion_node(session, gap_suggestion: GapSuggestion):
    """Create GapSuggestion node với MERGE để tránh duplicate"""
    session.run(
        """
        MERGE (g:GapSuggestion {id: $id})
        SET g.suggestion_text = $suggestion_text,
            g.target_node_id = $target_node_id,
            g.target_file_id = $target_file_id,
            g.similarity_score = $similarity_score
        WITH g
        MATCH (n:KnowledgeNode {id: $node_id})
        MERGE (n)-[:HAS_SUGGESTION]->(g)
        """,
        id=gap_suggestion.Id,
        suggestion_text=gap_suggestion.SuggestionText,
        target_node_id=gap_suggestion.TargetNodeId,
        target_file_id=gap_suggestion.TargetFileId,
        similarity_score=gap_suggestion.SimilarityScore,
        node_id=gap_suggestion.NodeId
    )

def create_parent_child_relationship(session, parent_id: str, child_id: str, relationship_type: str = "HAS_SUBCATEGORY"):
    """Create hierarchical relationship với MERGE để tránh duplicate"""
    
    # Map relationship types dựa trên level hoặc type
    relationship_map = {
        'domain_to_category': 'HAS_SUBCATEGORY',
        'category_to_concept': 'CONTAINS_CONCEPT', 
        'concept_to_subconcept': 'HAS_DETAIL'
    }
    
    cypher_relationship = relationship_map.get(relationship_type, 'HAS_SUBCATEGORY')
    
    session.run(
        f"""
        MATCH (parent:KnowledgeNode {{id: $parent_id}})
        MATCH (child:KnowledgeNode {{id: $child_id}})
        MERGE (parent)-[:{cypher_relationship}]->(child)
        """,
        parent_id=parent_id,
        child_id=child_id
    )

def determine_relationship_type(parent_level: int, child_level: int) -> str:
    """Xác định relationship type dựa trên levels"""
    if parent_level == 0 and child_level == 1:
        return 'domain_to_category'
    elif parent_level == 1 and child_level == 2:
        return 'category_to_concept'
    elif parent_level == 2 and child_level == 3:
        return 'concept_to_subconcept'
    else:
        return 'HAS_SUBCATEGORY'

def check_existing_data(session) -> bool:
    """Kiểm tra xem đã có dữ liệu trong database chưa"""
    result = session.run("MATCH (n:KnowledgeNode) RETURN count(n) as count")
    count = result.single()["count"]
    return count > 0

def load_seed_data(json_file_path: str, connection: Neo4jConnection):
    """Load seed data từ JSON file vào Neo4j - chỉ thêm mới, không xóa cũ"""
    
    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"❌ JSON file not found: {json_file_path}")
        return
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON file: {e}")
        return
    
    session = connection.get_session()
    
    try:
        # Kiểm tra dữ liệu hiện có
        existing_data = check_existing_data(session)
        if existing_data:
            print("📊 Database đã có dữ liệu, chỉ thêm mới...")
        else:
            print("🆕 Database trống, bắt đầu import...")
        
        # First pass: Create all KnowledgeNodes
        print("📝 Creating/Updating KnowledgeNodes...")
        knowledge_nodes = []
        node_dict = {}  # Để lưu nodes theo ID để tìm relationship
        
        for node_data in data['nodes']:
            knowledge_node = KnowledgeNode(node_data)
            node_id = create_knowledge_node(session, knowledge_node)
            knowledge_nodes.append(knowledge_node)
            node_dict[knowledge_node.Id] = knowledge_node
            print(f"  ✅ Created/Updated node: {knowledge_node.Name} (Level {knowledge_node.Level})")
        
        # Second pass: Create parent-child relationships với đúng types
        print("🔗 Creating relationships...")
        relationships_created = 0
        for node in knowledge_nodes:
            if node.ParentId and node.ParentId in node_dict:
                parent_node = node_dict[node.ParentId]
                relationship_type = determine_relationship_type(parent_node.Level, node.Level)
                create_parent_child_relationship(session, node.ParentId, node.Id, relationship_type)
                relationships_created += 1
                print(f"  ✅ Created {relationship_type}: {node.ParentId} -> {node.Id}")
        
        print(f"  📈 Created {relationships_created} relationships")
        
        # Third pass: Create Evidence nodes với đầy đủ fields
        print("📄 Creating Evidence nodes...")
        for evidence_data in data['evidences']:
            evidence = Evidence(evidence_data)
            evidence_id = create_evidence_node(session, evidence)
            print(f"  ✅ Created/Updated evidence: {evidence_id} for node: {evidence.NodeId}")
        
        # Fourth pass: Create GapSuggestion nodes với đầy đủ fields
        print("💡 Creating GapSuggestion nodes...")
        for gap_data in data['gapSuggestions']:
            gap_suggestion = GapSuggestion(gap_data)
            create_gap_suggestion_node(session, gap_suggestion)
            print(f"  ✅ Created/Updated gap suggestion for node: {gap_suggestion.NodeId}")
        
        print("🎉 Seed data imported/updated successfully!")
        print(f"📊 Summary:")
        print(f"   - Nodes: {len(knowledge_nodes)}")
        print(f"   - Relationships: {relationships_created}")
        print(f"   - Evidences: {len(data['evidences'])}")
        print(f"   - Gap Suggestions: {len(data['gapSuggestions'])}")
        
    except Exception as e:
        print(f"❌ Error importing seed data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

def test_connection(connection: Neo4jConnection):
    """Test Neo4j connection"""
    session = connection.get_session()
    try:
        result = session.run("RETURN 'Connection successful' AS message")
        message = result.single()["message"]
        print(f"✅ {message}")
        return True
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False
    finally:
        session.close()

def main():
    # Neo4j Aura connection configuration
    NEO4J_URI = "neo4j+ssc://daa013e6.databases.neo4j.io"
    NEO4J_USER = "neo4j"
    NEO4J_PASSWORD = "DTG0IyhifivaD2GwRoyIz4VPapRF0JdjoVsMfT9ggiY"
    
    # JSON file path - bạn có thể thay đổi file ở đây
    JSON_FILE_PATH = "mock/data4.json"  # Thay đổi thành data2.json hoặc data3.json tùy ý
    
    print("🔌 Testing Neo4j Aura connection...")
    
    # Create connection
    connection = Neo4jConnection(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    
    try:
        # Test connection first
        if test_connection(connection):
            print("🚀 Starting seed data import (insert only, no deletion)...")
            load_seed_data(JSON_FILE_PATH, connection)
        else:
            print("💥 Cannot proceed due to connection issues")
    except Exception as e:
        print(f"💥 Fatal error: {e}")
    finally:
        connection.close()
        print("🔚 Connection closed")

if __name__ == "__main__":
    main()