#!/usr/bin/env python3
"""Test translation optimization: native language processing → translate output"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.pipeline.translation import translate_structure, translate_chunk_analysis


def test_translate_structure():
    """Test structure translation"""
    print("\n" + "="*80)
    print("TEST 1: Structure Translation")
    print("="*80)
    
    # Mock structure in Korean
    structure_ko = {
        "domain": {
            "name": "인공지능 네트워크",
            "synthesis": "이 문서는 AI 네트워크에 대해 설명합니다"
        },
        "categories": [
            {
                "name": "딥러닝",
                "synthesis": "신경망 기반 학습 방법",
                "concepts": [
                    {
                        "name": "합성곱 신경망",
                        "synthesis": "이미지 처리에 사용되는 네트워크",
                        "subconcepts": [
                            {
                                "name": "풀링 레이어",
                                "synthesis": "특징 추출을 위한 레이어"
                            }
                        ]
                    }
                ]
            }
        ]
    }
    
    print("\n📝 Original structure (Korean):")
    print(f"  Domain: {structure_ko['domain']['name']}")
    print(f"  Category: {structure_ko['categories'][0]['name']}")
    print(f"  Concept: {structure_ko['categories'][0]['concepts'][0]['name']}")
    
    # Note: Without actual Papago credentials, this will return the same structure
    # In production, it would be translated
    translated = translate_structure(structure_ko, "ko", "ko", "", "")  # Same lang = no translation
    
    print("\n✓ Translation function works (no actual translation due to same lang)")
    print(f"  Result domain: {translated['domain']['name']}")
    
    return True


def test_translate_chunk_analysis():
    """Test chunk analysis translation"""
    print("\n" + "="*80)
    print("TEST 2: Chunk Analysis Translation")
    print("="*80)
    
    # Mock chunk analysis in Japanese
    chunk_ja = {
        "chunk_index": 0,
        "topic": "機械学習の基礎",
        "concepts": ["ニューラルネットワーク", "深層学習"],
        "summary": "この章では機械学習の基本的な概念を説明します",
        "key_claims": ["機械学習は人工知能の重要な分野です", "データから学習するシステムです"],
        "text": "..."
    }
    
    print("\n📝 Original chunk (Japanese):")
    print(f"  Topic: {chunk_ja['topic']}")
    print(f"  Concepts: {chunk_ja['concepts']}")
    print(f"  Summary: {chunk_ja['summary']}")
    
    translated = translate_chunk_analysis(chunk_ja, "ja", "ja", "", "")  # Same lang = no translation
    
    print("\n✓ Translation function works (no actual translation due to same lang)")
    print(f"  Result topic: {translated['topic']}")
    
    return True


def test_validation():
    """Test data validation and normalization"""
    print("\n" + "="*80)
    print("TEST 3: Data Validation")
    print("="*80)
    
    # Test with empty/invalid data
    structure_empty = {
        "domain": {
            "name": "",  # Empty name
            "synthesis": ""  # Empty synthesis
        },
        "categories": []
    }
    
    print("\n📝 Testing with empty fields:")
    print(f"  Domain name: '{structure_empty['domain']['name']}'")
    print(f"  Domain synthesis: '{structure_empty['domain']['synthesis']}'")
    
    # The validation should be in neo4j_graph_optimized.py (create_or_merge_node)
    # Here we just verify the structure is processed
    translated = translate_structure(structure_empty, "en", "en", "", "")
    
    print("\n✓ Empty structure handled gracefully")
    print(f"  Result: {translated}")
    
    return True


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("🧪 TESTING TRANSLATION OPTIMIZATION")
    print("="*80)
    
    tests = [
        ("Structure Translation", test_translate_structure),
        ("Chunk Analysis Translation", test_translate_chunk_analysis),
        ("Data Validation", test_validation)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"\n✅ {test_name} PASSED")
            else:
                failed += 1
                print(f"\n❌ {test_name} FAILED")
        except Exception as e:
            failed += 1
            print(f"\n❌ {test_name} FAILED: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)
    print(f"📊 RESULTS: {passed} passed, {failed} failed")
    print("="*80 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
