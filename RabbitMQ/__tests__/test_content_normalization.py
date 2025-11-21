"""
Unit tests for content_normalization module
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from pipeline.content_normalization import (
    normalize_text,
    remove_invalid_chars,
    fix_pdf_ligatures,
    normalize_whitespace,
    clean_reference_markers,
    extract_clean_paragraphs,
    calculate_text_quality_score
)


def test_remove_invalid_chars():
    """Test removing invalid characters"""
    print("\n=== Test: remove_invalid_chars ===")
    
    # Test with various invalid characters
    text = "This\x00is\ufffdtext\u200bwith\ufeffinvalid chars"
    cleaned = remove_invalid_chars(text)
    
    print(f"Original: {repr(text)}")
    print(f"Cleaned: {repr(cleaned)}")
    assert '\x00' not in cleaned, "Null bytes should be removed"
    assert '\ufffd' not in cleaned, "Replacement char should be removed"
    assert '\u200b' not in cleaned, "Zero-width space should be removed"
    print("✓ Invalid characters removed")


def test_fix_pdf_ligatures():
    """Test fixing PDF ligatures"""
    print("\n=== Test: fix_pdf_ligatures ===")
    
    # Test with ligatures
    text = "This has ﬁligatures and ﬂother issues"
    fixed = fix_pdf_ligatures(text)
    
    print(f"Original: {text}")
    print(f"Fixed: {fixed}")
    assert 'fi' in fixed and 'ﬁ' not in fixed, "fi ligature should be fixed"
    assert 'fl' in fixed and 'ﬂ' not in fixed, "fl ligature should be fixed"
    print("✓ Ligatures fixed")


def test_normalize_whitespace():
    """Test normalizing whitespace"""
    print("\n=== Test: normalize_whitespace ===")
    
    # Test 1: Preserve paragraphs
    text = "First   paragraph\n\n\n\nSecond   paragraph  with   spaces"
    normalized = normalize_whitespace(text, preserve_paragraphs=True)
    
    print(f"Original: {repr(text)}")
    print(f"Normalized: {repr(normalized)}")
    assert '\n\n' in normalized, "Double newlines should be preserved"
    assert '   ' not in normalized, "Multiple spaces should be collapsed"
    print("✓ Whitespace normalized with paragraph preservation")
    
    # Test 2: Collapse all
    collapsed = normalize_whitespace(text, preserve_paragraphs=False)
    
    print(f"Collapsed: {repr(collapsed)}")
    assert '\n' not in collapsed, "No newlines should remain"
    assert '  ' not in collapsed, "No multiple spaces should remain"
    print("✓ Whitespace fully collapsed")


def test_clean_reference_markers():
    """Test cleaning reference markers"""
    print("\n=== Test: clean_reference_markers ===")
    
    # Test 1: Remove markers
    text = "This is text [1] with [2] references [3] scattered around."
    cleaned = clean_reference_markers(text, remove=True)
    
    print(f"Original: {text}")
    print(f"Cleaned: {cleaned}")
    assert '[1]' not in cleaned, "Reference [1] should be removed"
    assert '[2]' not in cleaned, "Reference [2] should be removed"
    print("✓ Reference markers removed")
    
    # Test 2: Just normalize spacing
    normalized = clean_reference_markers(text, remove=False)
    
    print(f"Normalized: {normalized}")
    assert '[1]' in normalized, "Reference should still exist"
    print("✓ Reference markers normalized")


def test_normalize_text():
    """Test complete normalization"""
    print("\n=== Test: normalize_text ===")
    
    # Test with multiple issues
    text = "This  is\x00text\ufffd  with\n\n\nﬁligatures and [1] references"
    normalized = normalize_text(text)
    
    print(f"Original: {repr(text)}")
    print(f"Normalized: {repr(normalized)}")
    assert '\x00' not in normalized, "Null bytes removed"
    assert '\ufffd' not in normalized, "Invalid unicode removed"
    assert 'fi' in normalized or 'ﬁ' not in normalized, "Ligatures fixed"
    assert '  ' not in normalized.replace('\n\n', ''), "Whitespace normalized"
    print("✓ Complete normalization works")


def test_extract_clean_paragraphs():
    """Test extracting clean paragraphs"""
    print("\n=== Test: extract_clean_paragraphs ===")
    
    text = """
    First paragraph with enough content to pass minimum length test.
    
    Short para
    
    Second paragraph that is long enough to be included in results.
    
    Third valid paragraph with substantial content here.
    """
    
    paragraphs = extract_clean_paragraphs(text, min_length=20)
    
    print(f"Input text length: {len(text)}")
    print(f"Extracted paragraphs: {len(paragraphs)}")
    for i, para in enumerate(paragraphs):
        print(f"  [{i}] {para[:50]}... ({len(para)} chars)")
    
    assert len(paragraphs) >= 2, "Should extract at least 2 valid paragraphs"
    assert all(len(p) >= 20 for p in paragraphs), "All paragraphs should meet minimum length"
    print("✓ Paragraph extraction works")


def test_calculate_text_quality_score():
    """Test text quality scoring"""
    print("\n=== Test: calculate_text_quality_score ===")
    
    # Test 1: High quality text
    good_text = """
    This is a well-formed paragraph with proper sentences. It has good structure.
    Another sentence here. And another one. This demonstrates quality text.
    """
    good_score = calculate_text_quality_score(good_text)
    
    print(f"Good text score: {good_score:.2f}")
    assert good_score > 0.7, f"Good text should score > 0.7, got {good_score:.2f}"
    print("✓ High quality text scored well")
    
    # Test 2: Low quality text (garbled)
    bad_text = "\x00\ufffd\ufffd\x00  \ufffd  \x00"
    bad_score = calculate_text_quality_score(bad_text)
    
    print(f"Bad text score: {bad_score:.2f}")
    assert bad_score < 0.5, f"Bad text should score < 0.5, got {bad_score:.2f}"
    print("✓ Low quality text scored poorly")
    
    # Test 3: Empty text
    empty_score = calculate_text_quality_score("")
    
    print(f"Empty text score: {empty_score:.2f}")
    assert empty_score == 0.0, f"Empty text should score 0.0, got {empty_score:.2f}"
    print("✓ Empty text handled")


if __name__ == "__main__":
    print("=" * 60)
    print("Content Normalization Module Tests")
    print("=" * 60)
    
    try:
        test_remove_invalid_chars()
        test_fix_pdf_ligatures()
        test_normalize_whitespace()
        test_clean_reference_markers()
        test_normalize_text()
        test_extract_clean_paragraphs()
        test_calculate_text_quality_score()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
