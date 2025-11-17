"""
Test script for LLM API calls (HyperCLOVA X)
Tests both regular chat completions and web search functionality
Note: Uses system environment variables only (not .env file)
"""
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.pipeline.llm_analysis import call_llm_compact, extract_hierarchical_structure_compact
from src.pipeline.resource_discovery import call_hyperclova_with_web_search

# Get API configuration from environment variables
CLOVA_API_KEY = os.getenv("CLOVA_API_KEY", "")
CLOVA_MODEL = os.getenv("CLOVA_MODEL", "HCX-005")
CLOVA_API_URL = os.getenv("CLOVA_API_URL", "") or f"https://clovastudio.stream.ntruss.com/v3/chat-completions/{CLOVA_MODEL}"
CLOVA_EMBEDDING_URL = os.getenv("CLOVA_EMBEDDING_URL", "https://clovastudio.stream.ntruss.com/testapp/v1/api-tools/embedding/clir-emb-dolphin")
def test_basic_llm_call():
    """Test basic LLM call without web search"""
    print("\n" + "="*80)
    print("TEST 1: Basic LLM Call (No Web Search)")
    print("="*80)
    
    if not CLOVA_API_KEY:
        print("❌ ERROR: CLOVA_API_KEY is not set in environment variables")
        return False
    
    print(f"✓ API Key found: {CLOVA_API_KEY[:10]}...{CLOVA_API_KEY[-5:]}")
    print(f"✓ API URL: {CLOVA_API_URL}")
    
    prompt = "What is machine learning? Answer in one sentence."
    
    print(f"\n📤 Sending request...")
    print(f"   Prompt: {prompt}")
    
    try:
        result = call_llm_compact(
            prompt=prompt,
            max_tokens=200,
            clova_api_key=CLOVA_API_KEY,
            clova_api_url=CLOVA_API_URL,
            use_tton=True
        )
        
        if result:
            print(f"\n✅ SUCCESS!")
            print(f"   Response type: {type(result).__name__}")
            print(f"   Response: {result}")
            return True
        else:
            print(f"\n❌ FAILED: Empty response")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_hierarchical_structure_extraction():
    """Test hierarchical structure extraction"""
    print("\n" + "="*80)
    print("TEST 2: Hierarchical Structure Extraction")
    print("="*80)
    
    if not CLOVA_API_KEY:
        print("❌ ERROR: CLOVA_API_KEY is not set")
        return False
    
    # Sample text
    sample_text = """
    Machine Learning is a subset of artificial intelligence that enables systems to learn from data.
    There are three main types: supervised learning, unsupervised learning, and reinforcement learning.
    Supervised learning uses labeled data to train models. Unsupervised learning finds patterns in unlabeled data.
    Reinforcement learning uses rewards to guide learning.
    """
    
    print(f"\n📤 Extracting structure from sample text...")
    print(f"   Text length: {len(sample_text)} chars")
    
    try:
        structure = extract_hierarchical_structure_compact(
            full_text=sample_text,
            file_name="test_document.pdf",
            lang="en",
            clova_api_key=CLOVA_API_KEY,
            clova_api_url=CLOVA_API_URL,
            max_synthesis_length=100
        )
        
        if structure and isinstance(structure, dict):
            print(f"\n✅ SUCCESS!")
            print(f"   Structure keys: {list(structure.keys())}")
            if 'domain' in structure:
                print(f"   Domain: {structure['domain'].get('name', 'N/A')}")
            if 'categories' in structure:
                print(f"   Categories: {len(structure.get('categories', []))}")
            print(f"   Full structure: {structure}")
            return True
        else:
            print(f"\n❌ FAILED: Invalid structure")
            print(f"   Type: {type(structure)}")
            print(f"   Value: {structure}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_web_search():
    """Test HyperCLOVA X web search functionality"""
    print("\n" + "="*80)
    print("TEST 3: HyperCLOVA X Web Search")
    print("="*80)
    
    if not CLOVA_API_KEY:
        print("❌ ERROR: CLOVA_API_KEY is not set")
        return False
    
    prompt = """Search the internet for recent academic papers about machine learning.
    Find 2 papers from IEEE Xplore or Google Scholar.
    
    Return JSON:
    [
      {
        "topic_index": 1,
        "resources": [
          {"title": "Paper Title", "url": "https://ieeexplore.ieee.org/...", "source": "IEEE"},
          {"title": "Another Paper", "url": "https://scholar.google.com/...", "source": "Scholar"}
        ]
      }
    ]
    """
    
    print(f"\n📤 Testing web search...")
    print(f"   Prompt length: {len(prompt)} chars")
    
    try:
        result = call_hyperclova_with_web_search(
            prompt=prompt,
            max_tokens=2000,
            api_key=CLOVA_API_KEY,
            api_url=CLOVA_API_URL,
            enable_web_search=True
        )
        
        if result:
            print(f"\n✅ SUCCESS!")
            print(f"   Response type: {type(result).__name__}")
            if isinstance(result, list):
                print(f"   Found {len(result)} items")
                for i, item in enumerate(result[:3], 1):
                    print(f"   Item {i}: {item}")
            else:
                print(f"   Response: {result}")
            return True
        else:
            print(f"\n❌ FAILED: Empty response")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_web_search_without_tool():
    """Test HyperCLOVA X without web search tool (fallback)"""
    print("\n" + "="*80)
    print("TEST 4: HyperCLOVA X Without Web Search Tool")
    print("="*80)
    
    if not CLOVA_API_KEY:
        print("❌ ERROR: CLOVA_API_KEY is not set")
        return False
    
    prompt = "What is machine learning? Provide a brief explanation."
    
    print(f"\n📤 Testing without web search tool...")
    
    try:
        result = call_hyperclova_with_web_search(
            prompt=prompt,
            max_tokens=200,
            api_key=CLOVA_API_KEY,
            api_url=CLOVA_API_URL,
            enable_web_search=False  # Disable web search
        )
        
        if result:
            print(f"\n✅ SUCCESS!")
            print(f"   Response: {result}")
            return True
        else:
            print(f"\n❌ FAILED: Empty response")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("🧪 LLM API TEST SUITE")
    print("="*80)
    print(f"\n📋 Configuration:")
    print(f"   API Key: {'✓ Set' if CLOVA_API_KEY else '❌ Not set'}")
    print(f"   API URL: {CLOVA_API_URL}")
    print(f"   Embedding URL: {CLOVA_EMBEDDING_URL}")
    
    if not CLOVA_API_KEY:
        print("\n❌ ERROR: CLOVA_API_KEY is required!")
        print("   Please set it in your .env file or environment variables")
        return
    
    results = []
    
    # Run tests
    results.append(("Basic LLM Call", test_basic_llm_call()))
    results.append(("Structure Extraction", test_hierarchical_structure_extraction()))
    results.append(("Web Search (with tool)", test_web_search()))
    results.append(("Web Search (without tool)", test_web_search_without_tool()))
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"   {status}: {test_name}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    print(f"\n   Total: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed")


if __name__ == "__main__":
    main()

