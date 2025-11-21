"""
Position-based content extraction utilities

This module provides utilities for extracting content from PDFs based on paragraph positions
rather than arbitrary text chunks. This ensures:
- Original text preservation (no LLM paraphrasing)
- Paragraph-level traceability
- Efficient recursive expansion
"""

from typing import List, Dict, Any, Optional, Tuple, Union


def extract_content_from_positions(
    positions: List[Union[List[int], int]],
    paragraphs: List[str],
    parent_range: Optional[List[int]] = None
) -> List[Dict[str, Any]]:
    """
    Extract actual content from paragraph positions
    
    Args:
        positions: List of [start, end] ranges or single indices
                  Examples: [[0, 5], [10, 15]] or [3, 7, 12]
        paragraphs: Full paragraph array from PDF
        parent_range: If extracting from sub-section, the parent's range [start, end]
                     Used to convert relative positions to absolute
    
    Returns:
        List of content dicts with:
        - text: Extracted and normalized text
        - position_range: [start, end] absolute paragraph indices
        - paragraph_count: Number of paragraphs in this range
        - word_count: Approximate word count
        - is_normalized: Whether text has been normalized
    
    Example:
        >>> paragraphs = ["Para 1", "Para 2", "Para 3", "Para 4"]
        >>> positions = [[0, 1], [3, 3]]
        >>> extract_content_from_positions(positions, paragraphs)
        [
            {
                'text': 'Para 1\\n\\nPara 2',
                'position_range': [0, 1],
                'paragraph_count': 2,
                'word_count': 4,
                'is_normalized': True
            },
            {
                'text': 'Para 4',
                'position_range': [3, 3],
                'paragraph_count': 1,
                'word_count': 2,
                'is_normalized': True
            }
        ]
    """
    from .content_normalization import normalize_text
    
    if not paragraphs:
        return []
    
    content = []
    max_idx = len(paragraphs) - 1
    
    for pos in positions:
        if isinstance(pos, list) and len(pos) >= 2:
            # Range [start, end]
            start, end = pos[0], pos[1]
            
            # If parent_range provided, convert relative → absolute
            if parent_range:
                start = parent_range[0] + start
                end = parent_range[0] + end
            
            # Clamp to valid range
            start = max(0, min(start, max_idx))
            end = max(0, min(end, max_idx))
            
            # Ensure start <= end
            if start > end:
                start, end = end, start
            
            # Extract paragraphs
            extracted_paras = paragraphs[start:end + 1]
            if not extracted_paras:
                continue
            
            # Join with double newlines to preserve paragraph structure
            text = "\n\n".join(extracted_paras)
            
            # Normalize text
            normalized_text = normalize_text(text)
            
            content.append({
                'text': normalized_text,
                'position_range': [start, end],
                'paragraph_count': end - start + 1,
                'word_count': len(normalized_text.split()),
                'is_normalized': True,
                'source': 'position_extraction'
            })
            
        elif isinstance(pos, int):
            # Single position
            idx = pos
            
            # If parent_range provided, convert relative → absolute
            if parent_range:
                idx = parent_range[0] + idx
            
            # Clamp to valid range
            idx = max(0, min(idx, max_idx))
            
            # Extract single paragraph
            text = paragraphs[idx]
            
            # Normalize text
            normalized_text = normalize_text(text)
            
            content.append({
                'text': normalized_text,
                'position_range': [idx, idx],
                'paragraph_count': 1,
                'word_count': len(normalized_text.split()),
                'is_normalized': True,
                'source': 'position_extraction'
            })
    
    return content


def convert_relative_to_absolute(
    relative_positions: List[Union[List[int], int]],
    parent_range: List[int]
) -> List[Union[List[int], int]]:
    """
    Convert positions relative to parent content → absolute in document
    
    Args:
        relative_positions: Positions relative to parent content
                          Examples: [[2, 8], [10, 15]] or [3, 7]
        parent_range: Parent's absolute range [start, end]
                     Example: [12, 25] (paragraphs 12-25 in document)
    
    Returns:
        Absolute positions in the original document
    
    Example:
        Parent range: [12, 25] (paragraphs 12-25 in document)
        Relative position: [[2, 8]] (paragraphs 2-8 within parent content)
        Absolute position: [[14, 20]] (12 + 2 = 14, 12 + 8 = 20)
        
        >>> convert_relative_to_absolute([[2, 8], [10, 12]], [12, 25])
        [[14, 20], [22, 24]]
        >>> convert_relative_to_absolute([3, 7], [12, 25])
        [15, 19]
    """
    if not parent_range or len(parent_range) < 2:
        return relative_positions
    
    parent_start = parent_range[0]
    absolute_positions = []
    
    for rel_pos in relative_positions:
        if isinstance(rel_pos, list) and len(rel_pos) >= 2:
            # Range
            abs_start = parent_start + rel_pos[0]
            abs_end = parent_start + rel_pos[1]
            absolute_positions.append([abs_start, abs_end])
        elif isinstance(rel_pos, int):
            # Single position
            absolute_positions.append(parent_start + rel_pos)
        else:
            # Invalid format, keep as is
            absolute_positions.append(rel_pos)
    
    return absolute_positions


def validate_positions(
    positions: List[Union[List[int], int]],
    paragraph_count: int
) -> Tuple[bool, List[str]]:
    """
    Validate that positions are within valid ranges
    
    Args:
        positions: List of positions to validate
        paragraph_count: Total number of paragraphs in the document
    
    Returns:
        Tuple of (is_valid, error_messages)
        
    Example:
        >>> validate_positions([[0, 5], [10, 15]], 20)
        (True, [])
        >>> validate_positions([[0, 25], [30, 35]], 20)
        (False, ['Position range [0, 25] exceeds paragraph count 20', ...])
    """
    if paragraph_count <= 0:
        return False, ["Paragraph count must be positive"]
    
    errors = []
    max_idx = paragraph_count - 1
    
    for pos in positions:
        if isinstance(pos, list) and len(pos) >= 2:
            start, end = pos[0], pos[1]
            
            if start < 0:
                errors.append(f"Position range {pos} has negative start index")
            if end < 0:
                errors.append(f"Position range {pos} has negative end index")
            if start > max_idx:
                errors.append(f"Position range {pos} start exceeds paragraph count {paragraph_count}")
            if end > max_idx:
                errors.append(f"Position range {pos} end exceeds paragraph count {paragraph_count}")
            if start > end:
                errors.append(f"Position range {pos} has start > end")
                
        elif isinstance(pos, int):
            if pos < 0:
                errors.append(f"Position {pos} is negative")
            if pos > max_idx:
                errors.append(f"Position {pos} exceeds paragraph count {paragraph_count}")
        else:
            errors.append(f"Invalid position format: {pos} (must be int or [int, int])")
    
    return len(errors) == 0, errors


def clamp_positions_to_range(
    positions: List[Union[List[int], int]],
    paragraph_count: int
) -> List[Union[List[int], int]]:
    """
    Clamp positions to valid ranges (0 to paragraph_count - 1)
    
    This is a fallback when LLM returns invalid positions.
    
    Args:
        positions: List of positions (may be out of range)
        paragraph_count: Total number of paragraphs
    
    Returns:
        Clamped positions that are guaranteed to be valid
        
    Example:
        >>> clamp_positions_to_range([[0, 25], [30, 35]], 20)
        [[0, 19], [19, 19]]
        >>> clamp_positions_to_range([30, 35], 20)
        [19, 19]
    """
    if paragraph_count <= 0:
        return []
    
    max_idx = paragraph_count - 1
    clamped = []
    
    for pos in positions:
        if isinstance(pos, list) and len(pos) >= 2:
            start = max(0, min(pos[0], max_idx))
            end = max(0, min(pos[1], max_idx))
            
            # Ensure start <= end
            if start > end:
                start, end = end, start
            
            clamped.append([start, end])
            
        elif isinstance(pos, int):
            clamped.append(max(0, min(pos, max_idx)))
        else:
            # Invalid format, skip
            continue
    
    return clamped


def split_text_to_paragraphs(text: str) -> List[str]:
    """
    Split text into paragraphs for position-based extraction
    
    This is used when we need to split extracted content (e.g., parent content)
    back into paragraphs for recursive extraction.
    
    Args:
        text: Text to split into paragraphs
    
    Returns:
        List of paragraph strings
        
    Example:
        >>> split_text_to_paragraphs("Para 1\\n\\nPara 2\\n\\nPara 3")
        ['Para 1', 'Para 2', 'Para 3']
    """
    import re
    
    # Split on double newlines or more
    paragraphs = re.split(r'\n\s*\n+', text.strip())
    
    # Filter out empty paragraphs
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    
    return paragraphs


def merge_overlapping_ranges(
    ranges: List[List[int]]
) -> List[List[int]]:
    """
    Merge overlapping or adjacent position ranges
    
    This is useful when multiple evidence items cover overlapping paragraphs.
    
    Args:
        ranges: List of [start, end] ranges
    
    Returns:
        List of merged non-overlapping ranges
        
    Example:
        >>> merge_overlapping_ranges([[0, 5], [3, 8], [10, 12]])
        [[0, 8], [10, 12]]
        >>> merge_overlapping_ranges([[0, 5], [6, 10], [11, 15]])
        [[0, 15]]
    """
    if not ranges:
        return []
    
    # Sort by start position
    sorted_ranges = sorted(ranges, key=lambda x: x[0])
    
    merged = [sorted_ranges[0]]
    
    for current in sorted_ranges[1:]:
        last = merged[-1]
        
        # Check if current overlaps or is adjacent to last
        if current[0] <= last[1] + 1:
            # Merge by extending the end
            merged[-1] = [last[0], max(last[1], current[1])]
        else:
            # No overlap, add as new range
            merged.append(current)
    
    return merged


def get_position_coverage(
    positions: List[Union[List[int], int]],
    paragraph_count: int
) -> float:
    """
    Calculate what percentage of paragraphs are covered by positions
    
    Args:
        positions: List of position ranges or single positions
        paragraph_count: Total number of paragraphs
    
    Returns:
        Coverage percentage (0.0 to 1.0)
        
    Example:
        >>> get_position_coverage([[0, 4], [8, 9]], 20)
        0.35  # 7 out of 20 paragraphs = 35%
    """
    if paragraph_count <= 0:
        return 0.0
    
    # Convert all positions to ranges
    ranges = []
    for pos in positions:
        if isinstance(pos, list) and len(pos) >= 2:
            ranges.append(pos)
        elif isinstance(pos, int):
            ranges.append([pos, pos])
    
    # Merge overlapping ranges
    merged = merge_overlapping_ranges(ranges)
    
    # Count total paragraphs covered
    covered = sum(end - start + 1 for start, end in merged)
    
    return min(1.0, covered / paragraph_count)
