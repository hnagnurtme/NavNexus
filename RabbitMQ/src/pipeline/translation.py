"""Enhanced translation module using Papago with robust error handling"""
import requests
import time
import re
from typing import List, Dict, Any, Optional
from copy import deepcopy
from dataclasses import asdict


# Supported language codes for Papago
SUPPORTED_LANGUAGES = {
    'ko': 'Korean',
    'en': 'English', 
    'ja': 'Japanese',
    'zh-cn': 'Chinese (Simplified)',
    'zh-tw': 'Chinese (Traditional)',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'ru': 'Russian'
}


def validate_language_codes(source: str, target: str) -> bool:
    """Validate if language codes are supported by Papago"""
    return source in SUPPORTED_LANGUAGES and target in SUPPORTED_LANGUAGES


def split_text_semantically(text: str, max_length: int = 4500) -> List[str]:
    """
    Split text at semantic boundaries (sentences, paragraphs) instead of fixed length
    
    Args:
        text: Text to split
        max_length: Maximum length per chunk
    
    Returns:
        List of semantically split text chunks
    """
    if len(text) <= max_length:
        return [text]
    
    # Try to split at paragraphs first
    paragraphs = re.split(r'\n\s*\n', text)
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        # If adding this paragraph exceeds limit and we have content, start new chunk
        if current_chunk and len(current_chunk) + len(para) + 2 > max_length:
            chunks.append(current_chunk.strip())
            current_chunk = para
        else:
            current_chunk += "\n\n" + para if current_chunk else para
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    # If chunks are still too long, split by sentences
    final_chunks = []
    for chunk in chunks:
        if len(chunk) <= max_length:
            final_chunks.append(chunk)
        else:
            # Split by sentences
            sentences = re.split(r'[.!?]+', chunk)
            sentence_chunk = ""
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                    
                if sentence_chunk and len(sentence_chunk) + len(sentence) + 1 > max_length:
                    final_chunks.append(sentence_chunk.strip())
                    sentence_chunk = sentence
                else:
                    sentence_chunk += ". " + sentence if sentence_chunk else sentence
            
            if sentence_chunk:
                final_chunks.append(sentence_chunk.strip())
    
    return final_chunks


def translate_with_retry(text: str, source: str, target: str, 
                        papago_client_id: str, papago_client_secret: str,
                        max_retries: int = 3, retry_delay: float = 1.0) -> Optional[str]:
    """
    Translate single text with retry logic and proper error handling
    
    Args:
        text: Text to translate
        source: Source language code
        target: Target language code  
        papago_client_id: Papago API client ID
        papago_client_secret: Papago API secret
        max_retries: Maximum retry attempts
        retry_delay: Delay between retries in seconds
    
    Returns:
        Translated text or None if failed
    """
    if not text.strip():
        return text
    
    if not validate_language_codes(source, target):
        print(f"❌ Unsupported language pair: {source} -> {target}")
        return None
    
    url = "https://papago.apigw.ntruss.com/nmt/v1/translation"
    headers = {
        "X-NCP-APIGW-API-KEY-ID": papago_client_id,
        "X-NCP-APIGW-API-KEY": papago_client_secret,
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
    }
    
    data = {"source": source, "target": target, "text": text}
    
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, data=data, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                return result['message']['result']['translatedText']
                
            elif response.status_code == 429:  # Rate limited
                wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                print(f"⚠️ Rate limited, waiting {wait_time}s (attempt {attempt + 1})")
                time.sleep(wait_time)
                continue
                
            else:
                print(f"❌ Papago API error {response.status_code}: {response.text}")
                if attempt == max_retries - 1:
                    return None
                    
        except requests.exceptions.Timeout:
            print(f"⏰ Request timeout (attempt {attempt + 1})")
            if attempt == max_retries - 1:
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"🌐 Network error (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                return None
        
        # Wait before retry
        time.sleep(retry_delay)
    
    return None


def translate_batch_enhanced(texts: List[str], source: str = 'ko', target: str = 'en', 
                           papago_client_id: str = "", papago_client_secret: str = "",
                           max_workers: int = 3) -> List[str]:
    """
    Enhanced batch translation with better error handling and rate limiting
    
    Args:
        texts: List of texts to translate
        source: Source language code
        target: Target language code
        papago_client_id: Papago API client ID
        papago_client_secret: Papago API secret  
        max_workers: Maximum concurrent translations (for future async implementation)
    
    Returns:
        List of translated texts (original text if translation failed)
    """
    if source == target or not texts:
        return texts
    
    if not papago_client_id or not papago_client_secret:
        print("❌ Papago credentials not provided")
        return texts
    
    if not validate_language_codes(source, target):
        print(f"❌ Unsupported language pair: {source} -> {target}")
        return texts
    
    results = []
    success_count = 0
    fail_count = 0
    
    for i, text in enumerate(texts):
        if not text or not text.strip():
            results.append(text)
            continue
        
        print(f"  🔄 Translating {i+1}/{len(texts)} ({len(text)} chars)...")
        
        # Split long text semantically
        text_chunks = split_text_semantically(text)
        translated_chunks = []
        
        for chunk in text_chunks:
            translated = translate_with_retry(
                chunk, source, target, 
                papago_client_id, papago_client_secret
            )
            
            if translated is not None:
                translated_chunks.append(translated)
                success_count += 1
            else:
                # Use original chunk if translation fails
                translated_chunks.append(chunk)
                fail_count += 1
                print(f"  ⚠️ Failed to translate chunk: {chunk[:50]}...")
        
        # Combine chunks
        if translated_chunks:
            results.append(" ".join(translated_chunks))
        else:
            results.append(text)
            fail_count += 1
        
        # Rate limiting between texts
        if i < len(texts) - 1:  # Don't wait after last text
            time.sleep(0.5)  # 500ms between requests
    
    print(f"✓ Translation: {success_count} successful, {fail_count} failed")
    return results


def translate_structure_enhanced(structure: Dict[str, Any], source: str, target: str,
                               papago_client_id: str, papago_client_secret: str) -> Dict[str, Any]:
    """
    Enhanced structure translation with better error handling
    
    Args:
        structure: Hierarchical structure to translate
        source: Source language code
        target: Target language code
        papago_client_id: Papago API client ID
        papago_client_secret: Papago API secret
    
    Returns:
        Translated structure with metadata
    """
    if source == target or not structure:
        return structure
    
    if not validate_language_codes(source, target):
        print(f"❌ Cannot translate: unsupported language pair {source} -> {target}")
        return structure
    
    # Create deep copy
    translated_structure = deepcopy(structure)
    translation_metadata = {
        "source_language": source,
        "target_language": target, 
        "translated_at": time.time(),
        "translated_fields": 0,
        "failed_fields": 0
    }
    
    def extract_texts(node: Dict, path: List[str] = []) -> List[tuple]:
        """Recursively extract all translatable texts with their paths"""
        if path is None:
            path = []
        
        texts = []
        
        # Extract name and synthesis fields
        for field in ['name', 'synthesis']:
            if field in node and node[field]:
                full_path = path + [field]
                texts.append(('->'.join(full_path), node[field]))
        
        # Recursively process children in known hierarchical fields
        child_fields = ['categories', 'concepts', 'subconcepts', 'details', 'children']
        for field in child_fields:
            if field in node and isinstance(node[field], list):
                for i, child in enumerate(node[field]):
                    child_path = path + [field, str(i)]
                    texts.extend(extract_texts(child, child_path))
        
        return texts
    
    def apply_translations(node: Dict, translations: Dict[str, str], path: List[str] = []):
        """Apply translations back to structure using path mapping"""
        if path is None:
            path = []
        
        current_path = '->'.join(path) if path else ''
        
        # Apply to current node fields
        for field in ['name', 'synthesis']:
            if field in node and node[field]:
                field_path = current_path + '->' + field if current_path else field
                if field_path in translations:
                    node[field] = translations[field_path]
                    translation_metadata["translated_fields"] += 1
        
        # Recursively apply to children
        child_fields = ['categories', 'concepts', 'subconcepts', 'details', 'children']
        for field in child_fields:
            if field in node and isinstance(node[field], list):
                for i, child in enumerate(node[field]):
                    child_path = path + [field, str(i)]
                    apply_translations(child, translations, child_path)
    
    # Extract all texts with their paths
    all_texts_with_paths = extract_texts(translated_structure)
    
    if not all_texts_with_paths:
        return translated_structure
    
    paths, texts = zip(*all_texts_with_paths)
    
    # Translate all texts
    translated_texts = translate_batch_enhanced(
        list(texts), source, target, papago_client_id, papago_client_secret
    )
    
    # Create path to translation mapping
    translations_dict = dict(zip(paths, translated_texts))
    
    # Count failures
    for path, original, translated in zip(paths, texts, translated_texts):
        if translated == original:  # Translation failed
            translation_metadata["failed_fields"] += 1
            print(f"  ⚠️ Translation failed for: {path}")
    
    # Apply translations back to structure
    apply_translations(translated_structure, translations_dict)
    
    # Add metadata to structure
    translated_structure['_translation_metadata'] = translation_metadata
    
    print(f"✓ Structure translation: {translation_metadata['translated_fields']} fields translated, "
          f"{translation_metadata['failed_fields']} failed")
    
    return translated_structure


def translate_chunk_analysis_enhanced(chunk_data: Dict[str, Any], source: str, target: str,
                                    papago_client_id: str, papago_client_secret: str) -> Dict[str, Any]:
    """
    Enhanced chunk analysis translation with metadata
    
    Args:
        chunk_data: Chunk analysis data
        source: Source language code  
        target: Target language code
        papago_client_id: Papago API client ID
        papago_client_secret: Papago API secret
    
    Returns:
        Translated chunk analysis with metadata
    """
    if source == target or not chunk_data:
        return chunk_data
    
    translated = deepcopy(chunk_data)
    
    # Define fields to translate and their types
    translatable_fields = {
        'topic': 'single',
        'summary': 'single', 
        'concepts': 'list',
        'key_claims': 'list',
        'questions_raised': 'list',
        'primary_topic': 'single',
        'detailed_summary': 'single',
        'key_evidence': 'list'
    }
    
    # Collect all texts to translate
    texts_to_translate = []
    field_mapping = []  # (field_name, index, field_type)
    
    for field, field_type in translatable_fields.items():
        if field not in translated or not translated[field]:
            continue
            
        if field_type == 'single':
            texts_to_translate.append(translated[field])
            field_mapping.append((field, -1, 'single'))
            
        elif field_type == 'list' and isinstance(translated[field], list):
            for i, item in enumerate(translated[field]):
                if item and item.strip():
                    texts_to_translate.append(item)
                    field_mapping.append((field, i, 'list'))
    
    if not texts_to_translate:
        return translated
    
    # Translate all texts
    translated_texts = translate_batch_enhanced(
        texts_to_translate, source, target, papago_client_id, papago_client_secret
    )
    
    # Apply translations back
    translation_stats = {"translated": 0, "failed": 0}
    
    for (field, index, field_type), translated_text in zip(field_mapping, translated_texts):
        original_text = texts_to_translate[translation_stats["translated"] + translation_stats["failed"]]
        
        if translated_text != original_text:  # Success
            if field_type == 'single':
                translated[field] = translated_text
            else:  # list
                translated[field][index] = translated_text
            translation_stats["translated"] += 1
        else:
            translation_stats["failed"] += 1
            print(f"  ⚠️ Failed to translate {field}[{index}]")
    
    # Add translation metadata
    translated['_translation_metadata'] = {
        "source_language": source,
        "target_language": target,
        **translation_stats
    }
    
    print(f"✓ Chunk translation: {translation_stats['translated']} successful, "
          f"{translation_stats['failed']} failed")
    
    return translated


def get_translation_supported_languages() -> Dict[str, str]:
    """Get dictionary of supported language codes and their names"""
    return SUPPORTED_LANGUAGES.copy()