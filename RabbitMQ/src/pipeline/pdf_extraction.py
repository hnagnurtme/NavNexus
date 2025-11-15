"""PDF extraction module"""
import requests
import fitz  # PyMuPDF
import io
from typing import Tuple


def extract_pdf_fast(pdf_url: str, max_pages: int = 25) -> Tuple[str, str]:
    """Fast PDF extraction with language detection"""
    try:
        print(f"📄 Downloading: {pdf_url}")
        resp = requests.get(pdf_url, timeout=30, stream=True)
        resp.raise_for_status()
        
        pdf_bytes = io.BytesIO()
        for chunk in resp.iter_content(8192):
            if chunk:
                pdf_bytes.write(chunk)
        
        pdf_bytes.seek(0)
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        full_text = ""
        total_pages = min(doc.page_count, max_pages)
        
        for i in range(total_pages):
            page = doc[i]
            text = page.get_text().strip()
            if text:
                full_text += f"\n\n=== PAGE {i+1} ===\n{text}"
        
        doc.close()
        pdf_bytes.close()
        
        # Detect language
        sample = full_text[:1000]
        if any('\uAC00' <= c <= '\uD7A3' for c in sample):
            lang = "ko"
        elif any('\u3040' <= c <= '\u30FF' for c in sample):
            lang = "ja"
        elif any('\u4E00' <= c <= '\u9FFF' for c in sample):
            lang = "zh"
        else:
            lang = "en"
        
        print(f"✓ Extracted {total_pages} pages | Language: {lang}")
        return full_text.strip(), lang
    
    except Exception as e:
        raise RuntimeError(f"PDF extraction failed: {e}")
