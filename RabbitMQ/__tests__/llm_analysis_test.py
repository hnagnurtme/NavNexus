"""
llm_analysis_test.py
Test Enhanced LLM analysis module for node merging
"""

import os
import sys
import json
from typing import List, Dict, Any


from ..src.pipeline.chunking import create_smart_chunks
from ..src.pipeline.llm_analysis import (
    extract_deep_merge_structure,
    analyze_chunks_for_merging,
    identify_merge_candidates,
    apply_merge_candidates,
    extract_json_from_text,
    validate_structure_depth
)

# -------------------------------
# CONFIG
# -------------------------------
CLOVA_MODEL = "HCX-005"
CLOVA_API_URL = f"https://clovastudio.stream.ntruss.com/v3/chat-completions/{CLOVA_MODEL}"
CLOVA_API_KEY = os.getenv("CLOVA_API_KEY", "")

# Mock config for testing
class MockConfig:
    CLOVA_API_KEY = CLOVA_API_KEY
    CLOVA_API_URL = CLOVA_API_URL
    CLOVA_API_TIMEOUT = 30
    BATCH_SIZE = 3
    MAX_CHUNK_TEXT_LENGTH = 500

# Replace actual config with mock for testing
# -------------------------------
# SAMPLE DOCUMENTS
# -------------------------------

SAMPLE_DOCUMENT_1 = """
Machine Learning Fundamentals

Supervised learning involves training models on labeled data. Common algorithms include linear regression, logistic regression, and support vector machines. These are used for prediction and classification tasks.

Deep learning uses neural networks with multiple layers. Convolutional Neural Networks (CNNs) are excellent for image processing, while Recurrent Neural Networks (RNNs) work well for sequential data.

Data preprocessing is crucial for model performance. This includes handling missing values, feature scaling, and encoding categorical variables. Proper preprocessing can significantly improve accuracy.

Model evaluation metrics include accuracy, precision, recall, and F1-score. Cross-validation helps ensure model generalization to unseen data.

Hyperparameter tuning optimizes model performance. Techniques include grid search and random search. More advanced methods like Bayesian optimization can be more efficient.

Deployment considerations include model serving, monitoring, and continuous integration. MLOps practices help manage the machine learning lifecycle.
""" * 8  # Repeat to create longer text

SAMPLE_DOCUMENT_2 = """
Artificial Intelligence and Neural Networks

Neural networks consist of layers of interconnected nodes. Forward propagation passes data through the network, while backpropagation adjusts weights based on error.

Optimization algorithms like gradient descent, Adam, and RMSprop help minimize loss functions. Learning rate scheduling can improve convergence.

Computer vision applications include object detection, image segmentation, and facial recognition. Transfer learning allows using pre-trained models for new tasks.

Natural language processing covers text classification, sentiment analysis, and machine translation. Transformer architectures like BERT and GPT have revolutionized the field.

Reinforcement learning involves agents learning through interaction with environments. Q-learning and policy gradients are common approaches.

Ethical considerations in AI include bias mitigation, fairness, and explainability. Model interpretability techniques help understand model decisions.
""" * 8

# -------------------------------
# TEST UTILITY FUNCTIONS
# -------------------------------

def test_json_extraction():
    """Test JSON extraction from various response formats"""
    print("🧪 Testing JSON extraction...")
    
    test_cases = [
        # Case 1: Clean JSON
        ('{"name": "test", "value": 123}', {"name": "test", "value": 123}),
        
        # Case 2: JSON in markdown
        ('```json\n{"name": "test"}\n```', {"name": "test"}),
        
        # Case 3: Text with JSON
        ('Some text\n{"array": [1,2,3]}\nMore text', {"array": [1, 2, 3]}),
        
        # Case 4: Multiple JSON objects
        ('First: {"a": 1} Second: {"b": 2}', {"a": 1}),
    ]
    
    for i, (input_text, expected) in enumerate(test_cases):
        result = extract_json_from_text(input_text)
        print(f"  Case {i+1}: {result == expected} - Expected: {expected}, Got: {result}")
    
    print("✅ JSON extraction tests completed\n")

def test_structure_validation():
    """Test structure depth validation"""
    print("🧪 Testing structure validation...")
    
    # Valid deep structure
    valid_structure = {
        "domain": {"name": "Test Domain", "synthesis": "Test domain synthesis", "level": 1},
        "categories": [
            {
                "name": "Category 1", 
                "synthesis": "Category synthesis", 
                "level": 2,
                "concepts": [
                    {
                        "name": "Concept 1",
                        "synthesis": "Concept synthesis",
                        "level": 3,
                        "subconcepts": [
                            {
                                "name": "Subconcept 1",
                                "synthesis": "Subconcept synthesis",
                                "level": 4,
                                "details": [
                                    {"name": "Detail 1", "synthesis": "Detail synthesis", "level": 5},
                                    {"name": "Detail 2", "synthesis": "Detail synthesis", "level": 5}
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }
    
    stats = validate_structure_depth(valid_structure)
    print(f"  Valid structure stats: {stats}")
    assert stats['validation_passed'] == True, "Valid structure should pass validation"
    
    # Invalid shallow structure
    shallow_structure = {
        "domain": {"name": "Test", "synthesis": "Test", "level": 1},
        "categories": [
            {"name": "Cat 1", "synthesis": "Test", "level": 2}
        ]
    }
    
    stats = validate_structure_depth(shallow_structure)
    print(f"  Shallow structure stats: {stats}")
    assert stats['validation_passed'] == False, "Shallow structure should fail validation"
    
    print("✅ Structure validation tests completed\n")

# -------------------------------
# MAIN TEST FUNCTIONS
# -------------------------------

def test_structure_extraction():
    """Test deep hierarchical structure extraction"""
    print("🧪 Testing structure extraction...")
    
    try:
        structure = extract_deep_merge_structure(
            full_text=SAMPLE_DOCUMENT_1,
            file_name="test_ml_document.pdf",
            lang="en",
            clova_api_key=CLOVA_API_KEY,
            clova_api_url=CLOVA_API_URL,
            validate=True
        )
        
        if structure:
            print("✅ Structure extraction successful")
            print(f"   Domain: {structure.get('domain', {}).get('name', 'N/A')}")
            print(f"   Categories: {len(structure.get('categories', []))}")
            
            # Print structure summary
            total_concepts = 0
            total_subconcepts = 0
            total_details = 0
            
            for category in structure.get('categories', []):
                total_concepts += len(category.get('concepts', []))
                for concept in category.get('concepts', []):
                    total_subconcepts += len(concept.get('subconcepts', []))
                    for subconcept in concept.get('subconcepts', []):
                        total_details += len(subconcept.get('details', []))
            
            print(f"   Concepts: {total_concepts}")
            print(f"   Subconcepts: {total_subconcepts}")
            print(f"   Details: {total_details}")
            
            # Save for later use
            with open('test_structure_1.json', 'w', encoding='utf-8') as f:
                json.dump(structure, f, indent=2, ensure_ascii=False)
            
            return structure
        else:
            print("❌ Structure extraction failed - empty result")
            return None
            
    except Exception as e:
        print(f"❌ Structure extraction error: {e}")
        return None

def test_chunk_analysis():
    """Test chunk analysis for merging"""
    print("🧪 Testing chunk analysis...")
    
    # First create chunks
    chunks = create_smart_chunks(
        text=SAMPLE_DOCUMENT_1,
        chunk_size=400,
        overlap=50,
        min_chunk_size=200
    )
    
    print(f"   Created {len(chunks)} chunks")
    
    # Create a structure for analysis (or use existing one)
    structure = {
        "domain": {"name": "Machine Learning", "synthesis": "Test domain", "level": 1},
        "categories": [
            {
                "name": "Learning Algorithms", 
                "synthesis": "Test category", 
                "level": 2,
                "concepts": [
                    {
                        "name": "Supervised Learning",
                        "synthesis": "Test concept",
                        "level": 3,
                        "subconcepts": [
                            {
                                "name": "Regression Models",
                                "synthesis": "Test subconcept",
                                "level": 4,
                                "details": [
                                    {"name": "Linear Regression", "synthesis": "Test detail", "level": 5}
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }
    
    try:
        analysis = analyze_chunks_for_merging(
            chunks=chunks[:6],  # Test with first 6 chunks
            structure=structure,
            clova_api_key=CLOVA_API_KEY,
            clova_api_url=CLOVA_API_URL
        )
        
        if analysis and 'analysis_results' in analysis:
            print(f"✅ Chunk analysis successful - analyzed {len(analysis['analysis_results'])} chunks")
            
            # Print analysis summary
            stats = analysis.get('statistics', {})
            print(f"   High potential: {stats.get('high_potential', 0)}")
            print(f"   Medium potential: {stats.get('medium_potential', 0)}")
            print(f"   Low potential: {stats.get('low_potential', 0)}")
            
            # Show first few results
            for i, result in enumerate(analysis['analysis_results'][:3]):
                print(f"   Chunk {i}: {result.get('primary_concept')} - {result.get('merge_potential')}")
            
            return analysis
        else:
            print("❌ Chunk analysis failed - empty result")
            return None
            
    except Exception as e:
        print(f"❌ Chunk analysis error: {e}")
        return None

def test_merge_candidates():
    """Test merge candidate identification"""
    print("🧪 Testing merge candidate identification...")
    
    # Create two sample structures
    structure1 = test_structure_extraction()
    if not structure1:
        print("❌ Need structure1 for merge testing")
        return None
    
    # Create second structure from different document
    try:
        structure2 = extract_deep_merge_structure(
            full_text=SAMPLE_DOCUMENT_2,
            file_name="test_ai_document.pdf",
            lang="en",
            clova_api_key=CLOVA_API_KEY,
            clova_api_url=CLOVA_API_URL,
            validate=False  # Skip validation for speed
        )
        
        if structure2:
            with open('test_structure_2.json', 'w', encoding='utf-8') as f:
                json.dump(structure2, f, indent=2, ensure_ascii=False)
        else:
            print("❌ Could not create second structure for merge testing")
            return None
            
    except Exception as e:
        print(f"❌ Second structure creation error: {e}")
        # Use a simple mock structure for testing
        structure2 = {
            "domain": {"name": "Artificial Intelligence", "synthesis": "AI methods and applications", "level": 1},
            "categories": [
                {
                    "name": "Neural Networks", 
                    "synthesis": "Deep learning architectures", 
                    "level": 2,
                    "concepts": [
                        {
                            "name": "Optimization Methods",
                            "synthesis": "Algorithms for training neural networks",
                            "level": 3,
                            "subconcepts": [
                                {
                                    "name": "Gradient Descent",
                                    "synthesis": "Optimization through gradient computation",
                                    "level": 4,
                                    "details": [
                                        {"name": "Learning Rate", "synthesis": "Step size for parameter updates", "level": 5}
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    
    try:
        merge_candidates = identify_merge_candidates(
            structures=[structure1, structure2],
            similarity_threshold=0.7,
            clova_api_key=CLOVA_API_KEY,
            clova_api_url=CLOVA_API_URL
        )
        
        print(f"✅ Found {len(merge_candidates)} merge candidates")
        
        for i, candidate in enumerate(merge_candidates[:5]):
            print(f"   Candidate {i+1}: {candidate.get('merged_name')} (score: {candidate.get('similarity_score', 0):.2f})")
            print(f"      Nodes: {len(candidate.get('nodes', []))}")
            print(f"      Rationale: {candidate.get('merge_rationale', '')}")
        
        return merge_candidates
        
    except Exception as e:
        print(f"❌ Merge candidate identification error: {e}")
        return None

def test_merge_application():
    """Test applying merge candidates to structures"""
    print("🧪 Testing merge application...")
    
    merge_candidates = test_merge_candidates()
    if not merge_candidates:
        print("❌ Need merge candidates for application test")
        return None
    
    # Load or create structures
    try:
        with open('test_structure_1.json', 'r', encoding='utf-8') as f:
            structure1 = json.load(f)
        with open('test_structure_2.json', 'r', encoding='utf-8') as f:
            structure2 = json.load(f)
    except:
        print("❌ Could not load test structures")
        return None
    
    try:
        merged_structures = apply_merge_candidates(
            structures=[structure1, structure2],
            merge_candidates=merge_candidates,
            min_confidence=0.8
        )
        
        print(f"✅ Merge application successful")
        print(f"   Applied {len(merge_candidates)} candidates to {len(merged_structures)} structures")
        
        for i, structure in enumerate(merged_structures):
            print(f"   Structure {i+1}: {structure.get('_applied_merges', 0)} merges applied")
        
        return merged_structures
        
    except Exception as e:
        print(f"❌ Merge application error: {e}")
        return None

# -------------------------------
# PERFORMANCE TESTING
# -------------------------------

def test_performance():
    """Test performance with larger datasets"""
    print("🧪 Testing performance...")
    
    import time
    
    # Create larger document
    large_text = SAMPLE_DOCUMENT_1 * 3
    
    # Test chunking performance
    start_time = time.time()
    chunks = create_smart_chunks(
        text=large_text,
        chunk_size=500,
        overlap=100,
        min_chunk_size=200
    )
    chunking_time = time.time() - start_time
    
    print(f"   Chunking: {len(chunks)} chunks in {chunking_time:.2f}s")
    
    # Test with smaller batch for performance
    test_chunks = chunks[:10]  # Use first 10 chunks
    
    # Mock structure for performance test
    mock_structure = {
        "domain": {"name": "Test Domain", "synthesis": "Test", "level": 1},
        "categories": [
            {
                "name": "Test Category", 
                "synthesis": "Test", 
                "level": 2,
                "concepts": [
                    {
                        "name": "Test Concept",
                        "synthesis": "Test",
                        "level": 3,
                        "subconcepts": [
                            {
                                "name": "Test Subconcept",
                                "synthesis": "Test",
                                "level": 4,
                                "details": [
                                    {"name": "Test Detail", "synthesis": "Test", "level": 5}
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }
    
    # Test analysis performance
    start_time = time.time()
    try:
        analysis = analyze_chunks_for_merging(
            chunks=test_chunks,
            structure=mock_structure,
            clova_api_key=CLOVA_API_KEY,
            clova_api_url=CLOVA_API_URL
        )
        analysis_time = time.time() - start_time
        
        if analysis:
            print(f"   Analysis: {len(analysis['analysis_results'])} chunks in {analysis_time:.2f}s")
        else:
            print("   Analysis: Failed")
            
    except Exception as e:
        print(f"   Analysis error: {e}")

# -------------------------------
# MAIN TEST RUNNER
# -------------------------------

def run_all_tests():
    """Run all tests"""
    print("🚀 Starting Enhanced LLM Analysis Tests")
    print("=" * 50)
    
    # Test utility functions
    test_json_extraction()
    test_structure_validation()
    
    # Test core functionality
    structure = test_structure_extraction()
    analysis = test_chunk_analysis()
    merge_candidates = test_merge_candidates()
    merged_structures = test_merge_application()
    
    # Performance test
    test_performance()
    
    print("=" * 50)
    print("🎉 All tests completed!")
    
    # Summary
    results = {
        "structure_extraction": bool(structure),
        "chunk_analysis": bool(analysis),
        "merge_candidates": bool(merge_candidates),
        "merge_application": bool(merged_structures)
    }
    
    print(f"📊 Test Summary: {sum(results.values())}/{len(results)} passed")
    
    for test, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {test}")

if __name__ == "__main__":
    # Check if API key is available
    if not CLOVA_API_KEY or CLOVA_API_KEY == "test-key":
        print("⚠️  Warning: CLOVA_API_KEY not set. Some tests may fail.")
        print("   Set environment variable: export CLOVA_API_KEY='your-key'")
    
    run_all_tests()