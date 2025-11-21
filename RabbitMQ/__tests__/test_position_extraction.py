"""
Unit tests for position_extraction module
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from pipeline.position_extraction import (
    extract_content_from_positions,
    convert_relative_to_absolute,
    validate_positions,
    clamp_positions_to_range,
    split_text_to_paragraphs,
    merge_overlapping_ranges,
    get_position_coverage
)


def test_extract_content_from_positions():
    """Test extracting content from paragraph positions"""
    print("\n=== Test: extract_content_from_positions ===")
    
    paragraphs = [
        "Paragraph 0: First paragraph",
        "Paragraph 1: Second paragraph",
        "Paragraph 2: Third paragraph",
        "Paragraph 3: Fourth paragraph",
        "Paragraph 4: Fifth paragraph"
    ]
    
    # Test 1: Extract ranges
    positions = [[0, 1], [3, 4]]
    result = extract_content_from_positions(positions, paragraphs)
    
    print(f"Positions: {positions}")
    print(f"Result count: {len(result)}")
    assert len(result) == 2, "Should extract 2 items"
    assert result[0]['paragraph_count'] == 2, "First item should have 2 paragraphs"
    assert result[1]['paragraph_count'] == 2, "Second item should have 2 paragraphs"
    print("✓ Range extraction works")
    
    # Test 2: Extract single positions
    single_positions = [1, 3]
    result = extract_content_from_positions(single_positions, paragraphs)
    
    print(f"Single positions: {single_positions}")
    print(f"Result count: {len(result)}")
    assert len(result) == 2, "Should extract 2 items"
    assert result[0]['paragraph_count'] == 1, "Each item should have 1 paragraph"
    print("✓ Single position extraction works")
    
    # Test 3: With parent range (relative to absolute)
    parent_range = [1, 4]  # Paragraphs 1-4
    relative_positions = [[0, 1], [2, 3]]  # Relative to parent
    result = extract_content_from_positions(relative_positions, paragraphs, parent_range)
    
    print(f"Parent range: {parent_range}, Relative: {relative_positions}")
    print(f"Absolute positions: {[r['position_range'] for r in result]}")
    assert result[0]['position_range'] == [1, 2], "First should be [1, 2]"
    assert result[1]['position_range'] == [3, 4], "Second should be [3, 4]"
    print("✓ Relative to absolute conversion works")


def test_convert_relative_to_absolute():
    """Test converting relative positions to absolute"""
    print("\n=== Test: convert_relative_to_absolute ===")
    
    parent_range = [12, 25]
    
    # Test 1: Range positions
    relative = [[2, 8], [10, 15]]
    absolute = convert_relative_to_absolute(relative, parent_range)
    
    print(f"Parent: {parent_range}, Relative: {relative}")
    print(f"Absolute: {absolute}")
    assert absolute == [[14, 20], [22, 27]], f"Expected [[14, 20], [22, 27]], got {absolute}"
    print("✓ Range conversion works")
    
    # Test 2: Single positions
    relative_single = [3, 7, 12]
    absolute_single = convert_relative_to_absolute(relative_single, parent_range)
    
    print(f"Single relative: {relative_single}")
    print(f"Single absolute: {absolute_single}")
    assert absolute_single == [15, 19, 24], f"Expected [15, 19, 24], got {absolute_single}"
    print("✓ Single position conversion works")


def test_validate_positions():
    """Test position validation"""
    print("\n=== Test: validate_positions ===")
    
    paragraph_count = 20
    
    # Test 1: Valid positions
    positions = [[0, 5], [10, 15]]
    is_valid, errors = validate_positions(positions, paragraph_count)
    
    print(f"Valid positions: {positions}, Paragraph count: {paragraph_count}")
    print(f"Valid: {is_valid}, Errors: {errors}")
    assert is_valid, "Should be valid"
    assert len(errors) == 0, "Should have no errors"
    print("✓ Valid positions pass")
    
    # Test 2: Invalid positions (out of range)
    invalid_positions = [[0, 25], [30, 35]]
    is_valid, errors = validate_positions(invalid_positions, paragraph_count)
    
    print(f"Invalid positions: {invalid_positions}")
    print(f"Valid: {is_valid}, Errors: {len(errors)}")
    assert not is_valid, "Should be invalid"
    assert len(errors) > 0, "Should have errors"
    print("✓ Invalid positions detected")
    
    # Test 3: Negative positions
    negative_positions = [[-1, 5], [10, 15]]
    is_valid, errors = validate_positions(negative_positions, paragraph_count)
    
    print(f"Negative positions: {negative_positions}")
    print(f"Valid: {is_valid}, Errors: {len(errors)}")
    assert not is_valid, "Should be invalid"
    print("✓ Negative positions detected")


def test_clamp_positions_to_range():
    """Test clamping positions to valid range"""
    print("\n=== Test: clamp_positions_to_range ===")
    
    paragraph_count = 20
    
    # Test 1: Positions out of range
    positions = [[0, 25], [30, 35]]
    clamped = clamp_positions_to_range(positions, paragraph_count)
    
    print(f"Original: {positions}, Paragraph count: {paragraph_count}")
    print(f"Clamped: {clamped}")
    assert clamped == [[0, 19], [19, 19]], f"Expected [[0, 19], [19, 19]], got {clamped}"
    print("✓ Range clamping works")
    
    # Test 2: Single positions out of range
    single_positions = [30, 35, 5]
    clamped_single = clamp_positions_to_range(single_positions, paragraph_count)
    
    print(f"Single original: {single_positions}")
    print(f"Single clamped: {clamped_single}")
    assert clamped_single == [19, 19, 5], f"Expected [19, 19, 5], got {clamped_single}"
    print("✓ Single position clamping works")


def test_split_text_to_paragraphs():
    """Test splitting text into paragraphs"""
    print("\n=== Test: split_text_to_paragraphs ===")
    
    text = "Paragraph 1\n\nParagraph 2\n\n\nParagraph 3\n\nParagraph 4"
    paragraphs = split_text_to_paragraphs(text)
    
    print(f"Text: {repr(text[:50])}...")
    print(f"Paragraph count: {len(paragraphs)}")
    assert len(paragraphs) == 4, f"Expected 4 paragraphs, got {len(paragraphs)}"
    assert paragraphs[0] == "Paragraph 1", f"Expected 'Paragraph 1', got '{paragraphs[0]}'"
    print("✓ Text splitting works")


def test_merge_overlapping_ranges():
    """Test merging overlapping ranges"""
    print("\n=== Test: merge_overlapping_ranges ===")
    
    # Test 1: Overlapping ranges
    ranges = [[0, 5], [3, 8], [10, 12]]
    merged = merge_overlapping_ranges(ranges)
    
    print(f"Original: {ranges}")
    print(f"Merged: {merged}")
    assert merged == [[0, 8], [10, 12]], f"Expected [[0, 8], [10, 12]], got {merged}"
    print("✓ Overlapping merge works")
    
    # Test 2: Adjacent ranges
    adjacent = [[0, 5], [6, 10], [11, 15]]
    merged_adjacent = merge_overlapping_ranges(adjacent)
    
    print(f"Adjacent: {adjacent}")
    print(f"Merged: {merged_adjacent}")
    assert merged_adjacent == [[0, 15]], f"Expected [[0, 15]], got {merged_adjacent}"
    print("✓ Adjacent merge works")


def test_get_position_coverage():
    """Test calculating position coverage"""
    print("\n=== Test: get_position_coverage ===")
    
    # Test 1: Partial coverage
    positions = [[0, 4], [8, 9]]
    paragraph_count = 20
    coverage = get_position_coverage(positions, paragraph_count)
    
    print(f"Positions: {positions}, Total: {paragraph_count}")
    print(f"Coverage: {coverage:.2%}")
    assert 0.30 <= coverage <= 0.40, f"Expected ~35%, got {coverage:.2%}"
    print("✓ Coverage calculation works")
    
    # Test 2: Full coverage
    full_positions = [[0, 19]]
    full_coverage = get_position_coverage(full_positions, paragraph_count)
    
    print(f"Full positions: {full_positions}")
    print(f"Full coverage: {full_coverage:.2%}")
    assert full_coverage == 1.0, f"Expected 100%, got {full_coverage:.2%}"
    print("✓ Full coverage detection works")


if __name__ == "__main__":
    print("=" * 60)
    print("Position Extraction Module Tests")
    print("=" * 60)
    
    try:
        test_extract_content_from_positions()
        test_convert_relative_to_absolute()
        test_validate_positions()
        test_clamp_positions_to_range()
        test_split_text_to_paragraphs()
        test_merge_overlapping_ranges()
        test_get_position_coverage()
        
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
