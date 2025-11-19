"""
PDF to Text Converter using Enhanced Extraction Module
"""

import os
from datetime import datetime
from typing import Optional

# Import từ module của bạn
from ..src.pipeline.pdf_extraction import extract_pdf_enhanced


def convert_pdf_to_text(pdf_url: str, output_filename: Optional[str] = None) -> str:
    """
    Convert PDF from URL to text file using enhanced extraction
    
    Args:
        pdf_url: URL of the PDF file
        output_filename: Optional output filename (default: auto-generated)
    
    Returns:
        Absolute path to the created text file
    """
    try:
        print("🚀 Starting PDF to Text Conversion...")
        print(f"📥 Source: {pdf_url}")
        
        # Extract text from PDF
        full_text, language, metadata = extract_pdf_enhanced(pdf_url)
        
        # Generate output filename if not provided
        if not output_filename:
            if "/" in pdf_url:
                base_name = pdf_url.split("/")[-1].replace(".pdf", "")
            else:
                base_name = "extracted_text"
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{base_name}_{timestamp}.txt"
        
        # Ensure .txt extension
        if not output_filename.endswith('.txt'):
            output_filename += '.txt'
        
        # SAVE FILE NEXT TO THIS SCRIPT
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(current_dir, output_filename)

        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("PDF TEXT EXTRACTION REPORT\n")
            f.write("=" * 60 + "\n")
            f.write(f"Source URL: {pdf_url}\n")
            f.write(f"Extraction Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Pages: {metadata['total_pages']}\n")
            f.write(f"Extracted Pages: {metadata['extracted_pages']}\n")
            f.write(f"Language: {language} (confidence: {metadata['language_confidence']:.2f})\n")
            f.write(f"File Size: {metadata['file_size']:,} bytes\n")
            f.write(f"Average Text per Page: {metadata['avg_text_per_page']:.0f} characters\n")
            f.write("=" * 60 + "\n\n")

            # Write extracted text
            f.write(full_text)
        
        print(f"✅ Successfully converted PDF to text!")
        print(f"📁 Output file: {output_path}")
        print(f"📊 Statistics:")
        print(f"   - Pages: {metadata['extracted_pages']}/{metadata['total_pages']}")
        print(f"   - Language: {language}")
        print(f"   - File size: {len(full_text):,} characters")
        
        return output_path
        
    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        raise


def main():
    """Main function to convert a specific PDF"""
    
    # The PDF you want to test
    pdf_url = "https://sg.object.ncloudstorage.com/navnexus/GAP.pdf"
    
    # Output filename (optional)
    output_file = "GAP_extracted_text.txt"
    
    try:
        result_file = convert_pdf_to_text(pdf_url, output_file)
        
        # Display file info
        file_size = os.path.getsize(result_file)
        with open(result_file, 'r', encoding='utf-8') as f:
            content = f.read()
            line_count = content.count('\n') + 1
            word_count = len(content.split())
        
        print(f"\n📋 File Summary:")
        print(f"   - Output: {result_file}")
        print(f"   - Size: {file_size:,} bytes")
        print(f"   - Lines: {line_count:,}")
        print(f"   - Words: {word_count:,}")
        
    except Exception as e:
        print(f"💥 Error during conversion: {e}")


if __name__ == "__main__":
    main()
