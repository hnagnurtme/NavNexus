#!/usr/bin/env python3
"""
Test Quality Filter - Demo Script

This script demonstrates the quality filtering improvements in worker.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.recursive_expander import NodeData
from datetime import datetime, timezone

# Simulate the quality filter function from worker.py
def is_valid_node(node):
    """
    Validate node quality before inserting to Neo4j

    Returns:
        True if node meets quality standards, False otherwise
    """
    # Rule 1: Name must be meaningful (not generic)
    if not node.name or len(node.name) < 3:
        print(f"  ❌ Filtered '{node.name}': name too short")
        return False

    # Rule 2: Synthesis must have substance
    min_synthesis_length = {
        0: 50,   # domain: 50+ chars
        1: 40,   # category: 40+ chars
        2: 30,   # concept: 30+ chars
        3: 20,   # subconcept: 20+ chars
    }
    required_length = min_synthesis_length.get(node.level, 20)
    if not node.synthesis or len(node.synthesis) < required_length:
        print(f"  ❌ Filtered '{node.name}': synthesis too short ({len(node.synthesis)} < {required_length})")
        return False

    # Rule 3: Must have evidence positions (except root domain)
    if node.level > 0 and (not node.evidence_positions or len(node.evidence_positions) == 0):
        print(f"  ❌ Filtered '{node.name}': no evidence positions")
        return False

    # Rule 4: Must have evidence content extracted
    if node.level > 0 and (not node.evidence_content or len(node.evidence_content) == 0):
        print(f"  ❌ Filtered '{node.name}': no evidence content extracted")
        return False

    # Rule 5: Avoid generic/templated names
    generic_keywords = ['child', 'node', 'item', 'concept 1', 'category 1', 'unknown', 'untitled']
    if any(keyword in node.name.lower() for keyword in generic_keywords):
        print(f"  ❌ Filtered '{node.name}': generic name")
        return False

    print(f"  ✅ Passed '{node.name}'")
    return True


def test_quality_filter():
    """Test the quality filter with various node examples"""

    print("\n" + "="*80)
    print("🧪 TESTING QUALITY FILTER")
    print("="*80)

    # Good nodes
    print("\n📊 TESTING GOOD NODES (should pass):\n")

    good_nodes = [
        NodeData(
            id="domain-1",
            name="Satellite Energy Management",
            synthesis="Comprehensive study of energy management systems for low-earth orbit satellites using deep reinforcement learning techniques",
            level=0,
            type="domain",
            evidence_positions=[[0, 10]],
            evidence_content=[{"text": "Sample evidence", "position_range": [0, 10]}]
        ),
        NodeData(
            id="cat-1",
            name="Dueling DQN Architecture",
            synthesis="Neural network architecture separating value and advantage streams for better Q-learning",
            level=1,
            type="category",
            evidence_positions=[[5, 8]],
            evidence_content=[{"text": "Sample evidence", "position_range": [5, 8]}]
        ),
        NodeData(
            id="concept-1",
            name="Value Stream Network",
            synthesis="Dense neural network estimating state values",
            level=2,
            type="concept",
            evidence_positions=[[2, 4]],
            evidence_content=[{"text": "Sample evidence", "position_range": [2, 4]}]
        ),
    ]

    passed = sum(1 for node in good_nodes if is_valid_node(node))
    print(f"\n✅ Result: {passed}/{len(good_nodes)} good nodes passed")

    # Bad nodes
    print("\n" + "="*80)
    print("📊 TESTING BAD NODES (should be filtered):\n")

    bad_nodes = [
        NodeData(
            id="bad-1",
            name="X",  # Too short
            synthesis="This is a very comprehensive and detailed synthesis of the concept with sufficient length",
            level=1,
            type="category",
            evidence_positions=[[0, 5]],
            evidence_content=[{"text": "Sample", "position_range": [0, 5]}]
        ),
        NodeData(
            id="bad-2",
            name="Good Name Here",
            synthesis="Short",  # Too short for level
            level=1,
            type="category",
            evidence_positions=[[0, 5]],
            evidence_content=[{"text": "Sample", "position_range": [0, 5]}]
        ),
        NodeData(
            id="bad-3",
            name="Great Concept",
            synthesis="This is a comprehensive synthesis with enough characters to pass",
            level=2,
            type="concept",
            evidence_positions=[],  # No evidence positions
            evidence_content=[{"text": "Sample", "position_range": [0, 5]}]
        ),
        NodeData(
            id="bad-4",
            name="Another Concept",
            synthesis="This is also a comprehensive synthesis with enough characters",
            level=2,
            type="concept",
            evidence_positions=[[0, 5]],
            evidence_content=[]  # No evidence content
        ),
        NodeData(
            id="bad-5",
            name="Child 1",  # Generic name
            synthesis="This is a comprehensive synthesis with enough characters to pass the length check",
            level=2,
            type="concept",
            evidence_positions=[[0, 5]],
            evidence_content=[{"text": "Sample", "position_range": [0, 5]}]
        ),
    ]

    filtered = sum(1 for node in bad_nodes if not is_valid_node(node))
    print(f"\n✅ Result: {filtered}/{len(bad_nodes)} bad nodes filtered out")

    # Summary
    print("\n" + "="*80)
    print("📈 SUMMARY")
    print("="*80)
    total_nodes = len(good_nodes) + len(bad_nodes)
    total_passed = passed
    total_filtered = len(bad_nodes)
    quality_rate = round((total_passed / len(good_nodes)) * 100, 1)

    print(f"Total nodes tested: {total_nodes}")
    print(f"Good nodes (should pass): {len(good_nodes)}")
    print(f"Bad nodes (should filter): {len(bad_nodes)}")
    print(f"\nActual passed: {total_passed}")
    print(f"Actual filtered: {total_filtered}")
    print(f"Quality pass rate: {quality_rate}%")
    print("="*80 + "\n")


if __name__ == "__main__":
    test_quality_filter()
