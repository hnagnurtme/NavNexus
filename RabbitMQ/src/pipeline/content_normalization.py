"""
Content normalization utilities for cleaning PDF-extracted text

This module provides comprehensive text normalization to handle:
- PDF extraction artifacts (null bytes, invalid characters)
- Multiple spaces/newlines
- Broken sentences across paragraphs
- Reference markers
- Common PDF rendering issues (ligatures, special characters)
"""

import re
from typing import str, Optional


def normalize_text(text: str, aggressive: bool = False) -> str:
    """
    Normalize extracted text for LLM processing
    
    This is the main normalization function that applies all cleaning steps.
    
    Args:
        text: Raw text extracted from PDF
        aggressive: If True, apply more aggressive cleaning (may remove more content)
    
    Returns:
        Normalized, cleaned text ready for LLM processing
        
    Example:
        >>> normalize_text("This  is\\x00text\\ufffd  with\\n\\n\\nissues")
        'This is text with issues'
    """
    if not text:
        return ""
    
    # Step 1: Remove null bytes and invalid unicode
    text = remove_invalid_chars(text)
    
    # Step 2: Fix common PDF ligatures and special characters
    text = fix_pdf_ligatures(text)
    
    # Step 3: Normalize whitespace
    text = normalize_whitespace(text)
    
    # Step 4: Remove or clean reference markers
    text = clean_reference_markers(text)
    
    # Step 5: Fix broken sentences (optional, aggressive mode)
    if aggressive:
        text = fix_broken_sentences(text)
    
    # Step 6: Remove isolated numbers and page markers
    if aggressive:
        text = remove_page_markers(text)
    
    return text.strip()


def remove_invalid_chars(text: str) -> str:
    """
    Remove null bytes and invalid unicode characters
    
    Common PDF extraction artifacts:
    - \\x00: Null bytes
    - \\ufffd: Replacement character (indicates encoding error)
    - \\u200b: Zero-width space
    - \\ufeff: Byte order mark
    
    Args:
        text: Input text
    
    Returns:
        Text with invalid characters removed
    """
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Remove replacement character (often indicates corrupted text)
    text = text.replace('\ufffd', '')
    
    # Remove zero-width spaces and other invisible characters
    text = text.replace('\u200b', '')  # Zero-width space
    text = text.replace('\u200c', '')  # Zero-width non-joiner
    text = text.replace('\u200d', '')  # Zero-width joiner
    text = text.replace('\ufeff', '')  # Byte order mark
    
    # Remove other control characters except newlines and tabs
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t\r')
    
    return text


def fix_pdf_ligatures(text: str) -> str:
    """
    Fix common PDF ligature rendering issues
    
    PDFs sometimes render ligatures as special characters that don't
    convert properly to plain text.
    
    Args:
        text: Input text
    
    Returns:
        Text with ligatures fixed
    """
    ligature_map = {
        'ﬁ': 'fi',
        'ﬂ': 'fl',
        'ﬀ': 'ff',
        'ﬃ': 'ffi',
        'ﬄ': 'ffl',
        'ﬅ': 'ft',
        'ﬆ': 'st',
        # Common PDF rendering issues
        ''': "'",  # Smart quote
        ''': "'",  # Smart quote
        '"': '"',  # Smart quote
        '"': '"',  # Smart quote
        '–': '-',  # En dash
        '—': '-',  # Em dash
        '…': '...',  # Ellipsis
    }
    
    for pdf_char, normal_char in ligature_map.items():
        text = text.replace(pdf_char, normal_char)
    
    return text


def normalize_whitespace(text: str, preserve_paragraphs: bool = True) -> str:
    """
    Normalize whitespace in text
    
    Args:
        text: Input text
        preserve_paragraphs: If True, preserve double newlines (paragraph breaks)
                           If False, collapse all whitespace to single spaces
    
    Returns:
        Text with normalized whitespace
    """
    if preserve_paragraphs:
        # Preserve paragraph breaks (double newlines)
        # First, standardize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Replace 3+ newlines with exactly 2
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Replace multiple spaces with single space (but preserve newlines)
        text = re.sub(r'[^\S\n]+', ' ', text)
        
        # Clean up spaces around newlines
        text = re.sub(r' *\n *', '\n', text)
        
    else:
        # Collapse all whitespace to single spaces
        text = ' '.join(text.split())
    
    return text


def clean_reference_markers(text: str, remove: bool = False) -> str:
    """
    Clean or remove reference markers like [1], [2], etc.
    
    Args:
        text: Input text
        remove: If True, remove markers entirely
               If False, just clean up spacing around them
    
    Returns:
        Text with reference markers cleaned or removed
    """
    if remove:
        # Remove isolated reference markers
        # Matches: [1], [12], [123] when surrounded by spaces
        text = re.sub(r'\s+\[\d+\]\s+', ' ', text)
        
        # Also remove at end of sentences
        text = re.sub(r'\s*\[\d+\]\.', '.', text)
        text = re.sub(r'\s*\[\d+\],', ',', text)
        text = re.sub(r'\s*\[\d+\];', ';', text)
    else:
        # Just normalize spacing around markers
        # Ensure single space before and after
        text = re.sub(r'\s*\[(\d+)\]\s*', r' [\1] ', text)
    
    return text


def fix_broken_sentences(text: str) -> str:
    """
    Attempt to fix sentences broken across lines
    
    Common in PDFs where line breaks occur mid-sentence.
    This is aggressive and may not always be correct.
    
    Args:
        text: Input text
    
    Returns:
        Text with broken sentences potentially fixed
    """
    # If a line ends with a lowercase word (not punctuation),
    # and next line starts with lowercase, join them
    text = re.sub(
        r'([a-z,])\n([a-z])',
        r'\1 \2',
        text
    )
    
    # Fix hyphenated words broken across lines
    text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', text)
    
    return text


def remove_page_markers(text: str) -> str:
    """
    Remove common page markers and headers/footers
    
    This is aggressive and may remove valid content.
    Use with caution.
    
    Args:
        text: Input text
    
    Returns:
        Text with page markers removed
    """
    # Remove isolated page numbers
    # Matches: "Page 1", "Page 12", "p. 1", "1/10", etc.
    text = re.sub(r'\bPage\s+\d+\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\bp\.\s*\d+\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\b\d+\s*/\s*\d+\b', '', text)
    
    # Remove isolated numbers on their own line (likely page numbers)
    text = re.sub(r'\n\s*\d{1,3}\s*\n', '\n', text)
    
    return text


def clean_for_llm(text: str, max_length: Optional[int] = None) -> str:
    """
    Prepare text specifically for LLM processing
    
    Applies all normalization steps and optionally truncates to max length.
    
    Args:
        text: Raw text from PDF
        max_length: Maximum character length (None = no limit)
    
    Returns:
        Clean text ready for LLM
    """
    # Apply standard normalization
    text = normalize_text(text, aggressive=True)
    
    # Additional LLM-specific cleaning
    # Remove excessive punctuation
    text = re.sub(r'\.{4,}', '...', text)  # Multiple dots to ellipsis
    text = re.sub(r'-{3,}', '---', text)   # Multiple dashes
    
    # Ensure sentences end with proper punctuation
    # (This is optional and may not always be correct)
    # text = re.sub(r'([a-z])\n\n', r'\1.\n\n', text)
    
    # Truncate if needed
    if max_length and len(text) > max_length:
        # Try to truncate at sentence boundary
        truncated = text[:max_length]
        last_period = truncated.rfind('.')
        last_newline = truncated.rfind('\n\n')
        
        cutoff = max(last_period, last_newline)
        if cutoff > max_length * 0.8:  # At least 80% of max_length
            text = truncated[:cutoff + 1]
        else:
            text = truncated
    
    return text.strip()


def extract_clean_paragraphs(text: str, min_length: int = 20) -> list[str]:
    """
    Extract clean paragraphs from text
    
    Args:
        text: Normalized text
        min_length: Minimum paragraph length in characters
    
    Returns:
        List of clean paragraph strings
    """
    # Normalize first
    text = normalize_text(text)
    
    # Split on double newlines
    paragraphs = re.split(r'\n\s*\n+', text)
    
    # Filter and clean
    clean_paras = []
    for para in paragraphs:
        para = para.strip()
        if len(para) >= min_length:
            clean_paras.append(para)
    
    return clean_paras


def preserve_formatting_markers(text: str) -> str:
    """
    Identify and preserve important formatting markers
    
    Some text elements should be preserved:
    - Headers (lines with fewer words, possibly in caps)
    - Lists (lines starting with -, *, 1., etc.)
    - Code blocks (indented text)
    
    This is advanced and may not always be needed.
    
    Args:
        text: Input text
    
    Returns:
        Text with formatting markers preserved
    """
    # This is a placeholder for future enhancement
    # Current implementation just returns text as-is
    return text


def calculate_text_quality_score(text: str) -> float:
    """
    Calculate a quality score for extracted text
    
    Useful for detecting if PDF extraction was successful.
    
    Args:
        text: Extracted text
    
    Returns:
        Quality score from 0.0 to 1.0
        - 1.0 = High quality (clean, readable text)
        - 0.0 = Low quality (garbled, mostly artifacts)
    """
    if not text or len(text) < 10:
        return 0.0
    
    score = 1.0
    
    # Penalize for invalid characters
    invalid_char_ratio = len(re.findall(r'[\x00\ufffd]', text)) / len(text)
    score -= invalid_char_ratio * 0.5
    
    # Penalize for excessive whitespace
    whitespace_ratio = len(re.findall(r'\s', text)) / len(text)
    if whitespace_ratio > 0.5:  # More than 50% whitespace is suspicious
        score -= (whitespace_ratio - 0.5) * 0.5
    
    # Reward for proper sentence structure
    sentence_count = len(re.findall(r'[.!?]\s+[A-Z]', text))
    if sentence_count > 0:
        score += min(0.2, sentence_count / 100 * 0.2)
    
    # Penalize for excessive numbers (might be tables/data)
    digit_ratio = len(re.findall(r'\d', text)) / len(text)
    if digit_ratio > 0.3:  # More than 30% digits
        score -= (digit_ratio - 0.3) * 0.3
    
    return max(0.0, min(1.0, score))
