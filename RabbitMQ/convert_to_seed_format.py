# convert_to_seed_format.py
import json
from typing import Dict, List, Any

def extract_nodes_and_relationships(data: Dict[str, Any]) -> Dict[str, List]:
    """Extract nodes, evidences, and gap suggestions from nested structure"""
    
    nodes = []
    evidences = []
    gap_suggestions = []
    
    def process_node(node: Dict[str, Any], parent_id: str = None):
        """Recursively process node and its children"""
        
        # Extract node data without children, evidences, and gap suggestions
        node_data = {
            "Id": node["Id"],
            "Type": node["Type"],
            "Name": node["Name"],
            "Synthesis": node["Synthesis"],
            "WorkspaceId": node["WorkspaceId"],
            "Level": node["Level"],
            "SourceCount": node["SourceCount"],
            "TotalConfidence": node["TotalConfidence"],
            "CreatedAt": node["CreatedAt"],
            "UpdatedAt": node["UpdatedAt"],
            "ParentId": parent_id
        }
        nodes.append(node_data)
        
        # Process evidences for this node
        if "Evidences" in node:
            for evidence in node["Evidences"]:
                evidence_data = evidence.copy()
                evidence_data["NodeId"] = node["Id"]
                evidences.append(evidence_data)
        
        # Process gap suggestions for this node
        if "GapSuggestions" in node:
            for gap in node["GapSuggestions"]:
                gap_data = gap.copy()
                gap_data["NodeId"] = node["Id"]
                gap_suggestions.append(gap_data)
        
        # Process children recursively
        if "Children" in node:
            for child in node["Children"]:
                process_node(child, node["Id"])
    
    # Start processing from root
    process_node(data)
    
    return {
        "nodes": nodes,
        "evidences": evidences,
        "gapSuggestions": gap_suggestions
    }

def main():
    # Read the nested JSON file
    with open('mock/data.json', 'r', encoding='utf-8') as f:
        nested_data = json.load(f)
    
    # Convert to seed format
    seed_data = extract_nodes_and_relationships(nested_data)
    
    # Write the converted data
    with open('mock/data2.json', 'w', encoding='utf-8') as f:
        json.dump(seed_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Converted successfully!")
    print(f"📊 Statistics:")
    print(f"   - Nodes: {len(seed_data['nodes'])}")
    print(f"   - Evidences: {len(seed_data['evidences'])}")
    print(f"   - Gap Suggestions: {len(seed_data['gapSuggestions'])}")

if __name__ == "__main__":
    main()