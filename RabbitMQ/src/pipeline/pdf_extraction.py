"""Enhanced PDF extraction module with improved text processing"""
import requests
import fitz  # PyMuPDF
import io
import re
from typing import Tuple, Dict, Optional
from collections import Counter


def extract_pdf_enhanced(
    pdf_url: str, 
    max_pages: int = 25,
    timeout: int = 30,
    chunk_size: int = 8192
) -> Tuple[str, str, Dict]:
    """
    Enhanced PDF extraction with better text processing and language detection
    
    Args:
        pdf_url: URL of the PDF file
        max_pages: Maximum number of pages to extract
        timeout: Request timeout in seconds
        chunk_size: Download chunk size
    
    Returns:
        Tuple of (full_text, detected_language, metadata)
    """
    try:
        print(f"📄 Downloading: {pdf_url}")
        
        # Stream download with progress tracking
        pdf_bytes = download_pdf_with_progress(pdf_url, timeout, chunk_size)
        if not pdf_bytes:
            raise RuntimeError("Failed to download PDF")
        
        # Extract text with multiple strategies
        extraction_result = extract_text_from_pdf(pdf_bytes, max_pages)
        
        if not extraction_result["text"]:
            raise RuntimeError("No text extracted from PDF")
        
        # Enhanced language detection
        lang = detect_language_enhanced(extraction_result["text"])
        
        # Clean and normalize text
        clean_text = clean_extracted_text(extraction_result["text"])
        
        metadata = {
            "total_pages": extraction_result["total_pages"],
            "extracted_pages": extraction_result["extracted_pages"],
            "avg_text_per_page": extraction_result["avg_text_per_page"],
            "language_confidence": lang["confidence"],
            "file_size": len(pdf_bytes.getvalue()) if pdf_bytes else 0
        }
        
        print(f"✓ Extracted {extraction_result['extracted_pages']}/{extraction_result['total_pages']} pages | "
              f"Language: {lang['language']} (confidence: {lang['confidence']})")
        
        return clean_text, lang["language"], metadata
    
    except Exception as e:
        raise RuntimeError(f"PDF extraction failed: {e}")


def download_pdf_with_progress(pdf_url: str, timeout: int, chunk_size: int) -> Optional[io.BytesIO]:
    """Download PDF with progress tracking and error handling"""
    try:
        resp = requests.get(pdf_url, timeout=timeout, stream=True)
        resp.raise_for_status()
        
        # Check content type
        content_type = resp.headers.get('content-type', '')
        if 'pdf' not in content_type.lower():
            print(f"⚠️  Warning: Content-Type is '{content_type}', expected PDF")
        
        pdf_bytes = io.BytesIO()
        total_size = int(resp.headers.get('content-length', 0))
        downloaded = 0
        
        for chunk in resp.iter_content(chunk_size=chunk_size):
            if chunk:
                pdf_bytes.write(chunk)
                downloaded += len(chunk)
                
                # Progress reporting for large files
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    if percent % 20 == 0:  # Report every 20%
                        print(f"  📥 Download progress: {percent:.1f}%")
        
        pdf_bytes.seek(0)
        return pdf_bytes
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Download failed: {e}")
        return None


def extract_text_from_pdf(pdf_bytes: io.BytesIO, max_pages: int) -> Dict:
    """Extract text from PDF using multiple strategies"""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        full_text = ""
        text_per_page = []
        total_pages = min(doc.page_count, max_pages)  # LẤY PAGE COUNT TRƯỚC KHI CLOSE

        for i in range(total_pages):
            page = doc[i]

            # Strategy 1: Default
            text = page.get_text()

            # Strategy 2: Sorted
            if len(str(text).strip()) < 50:
                text = page.get_text("text", sort=True)

            # Strategy 3: Blocks
            if len(str(text).strip()) < 50:
                blocks = page.get_text("blocks")
                text = "\n".join([block[4] for block in blocks if block[4].strip()])

            cleaned_text = clean_page_text(str(text), i + 1)

            # FIXED: check cleaned_text, not function name
            if cleaned_text:
                full_text += cleaned_text + "\n\n"
                text_per_page.append(len(cleaned_text))

        # Store page count before closing the document
        total_doc_pages = doc.page_count
        doc.close()

        avg_text_per_page = (
            sum(text_per_page) / len(text_per_page) if text_per_page else 0
        )

        return {
            "text": full_text.strip(),
            "total_pages": total_doc_pages,
            "extracted_pages": total_pages,
            "avg_text_per_page": avg_text_per_page,
            "text_per_page": text_per_page
        }

    except Exception as e:
        raise RuntimeError(f"PDF text extraction error: {e}")



def clean_page_text(text: str, page_num: int) -> str:
    """Clean and format text from a single page"""
    if not text or not text.strip():
        return ""
    
    # Remove excessive whitespace but preserve paragraph breaks
    text = re.sub(r'\n\s*\n', '\n\n', text.strip())
    text = re.sub(r'[ \t]+', ' ', text)
    
    # Remove common PDF artifacts
    artifacts = [
        r'\x0c',  # Form feed
        r'-\n',   # Hyphenated line breaks
    ]
    
    for artifact in artifacts:
        text = text.replace(artifact, '')
    
    # Fix hyphenated words across line breaks
    text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', text)
    
    # Add page marker if there's substantial content
    if len(text) > 100:
        return f"=== PAGE {page_num} ===\n{text}"
    else:
        return text


def clean_extracted_text(text: str) -> str:
    """Final cleaning of extracted text"""
    if not text:
        return ""
    
    # Remove duplicate page markers (if any)
    text = re.sub(r'=== PAGE \d+ ===\s+=== PAGE \d+ ===', '', text)
    
    # Normalize line endings
    text = text.replace('\r\n', '\n')
    
    # Remove extra blank lines (keep max 2 consecutive)
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    
    return text.strip()


def detect_language_enhanced(text: str) -> Dict:
    """
    Enhanced language detection with confidence scoring
    
    Returns:
        Dict with 'language' and 'confidence'
    """
    if not text:
        return {"language": "en", "confidence": 0.0}
    
    # Use larger sample for better accuracy
    sample = text[:5000]  # Increased sample size
    char_counts = Counter(sample)
    total_chars = len(sample)
    
    # Define Unicode ranges for different languages
    lang_ranges = {
        "ko": ('\uAC00', '\uD7A3'),  # Hangul syllables
        "ja": ('\u3040', '\u30FF'),  # Hiragana + Katakana
        "zh": ('\u4E00', '\u9FFF'),  # CJK Unified Ideographs
    }
    
    lang_scores = {}
    
    # Calculate character-based scores
    for lang, (start, end) in lang_ranges.items():
        lang_chars = sum(1 for char in sample if start <= char <= end)
        score = lang_chars / total_chars if total_chars > 0 else 0
        lang_scores[lang] = score
    
    # Also check for common words as fallback
    common_words = {
        "en": ["the", "and", "of", "to", "in"],
        "ko": ["그", "에", "의", "을", "를"],
        "ja": ["の", "に", "は", "を", "が"],
        "zh": ["的", "是", "在", "了", "有"],
    }
    
    words = re.findall(r'\b\w+\b', sample.lower())
    word_counts = Counter(words)
    
    for lang, word_list in common_words.items():
        word_score = sum(word_counts[word] for word in word_list) / len(words) if words else 0
        lang_scores[lang] = lang_scores.get(lang, 0) + word_score * 0.5  # Weight word matches
    
    # Find best language
    if lang_scores:
        best_lang = max(lang_scores.items(), key=lambda x: x[1])
        if best_lang[1] > 0.1:  # Minimum confidence threshold
            return {"language": best_lang[0], "confidence": min(best_lang[1] * 2, 1.0)}
    
    # Default to English with low confidence
    return {"language": "en", "confidence": 0.1}


def get_pdf_metadata(pdf_bytes: io.BytesIO) -> Dict:
    """Extract PDF metadata if available"""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        metadata = doc.metadata or {}
        doc.close()
        
        return {
            "title": metadata.get("title", ""),
            "author": metadata.get("author", ""),
            "subject": metadata.get("subject", ""),
            "creator": metadata.get("creator", ""),
            "creation_date": metadata.get("creationDate", ""),
        }
    except:
        return {}