"""Translation module using Papago"""
import requests
from typing import List, Dict, Any
from copy import deepcopy


def translate_batch(texts: List[str], source: str = 'ko', target: str = 'en', 
                   papago_client_id: str = "", papago_client_secret: str = "") -> List[str]:
    """Batch translate with Papago"""
    if source == target or not texts:
        return texts
    
    if not papago_client_id or not papago_client_secret:
        return texts
    
    url = "https://papago.apigw.ntruss.com/nmt/v1/translation"
    headers = {
        "X-NCP-APIGW-API-KEY-ID": papago_client_id,
        "X-NCP-APIGW-API-KEY": papago_client_secret,
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
    }
    
    results = []
    for text in texts:
        if not text.strip():
            results.append(text)
            continue
        
        max_len = 4500
        if len(text) > max_len:
            parts = [text[i:i+max_len] for i in range(0, len(text), max_len)]
        else:
            parts = [text]
        
        translated_parts = []
        for part in parts:
            data = {"source": source, "target": target, "text": part}
            try:
                r = requests.post(url, headers=headers, data=data, timeout=10)
                if r.status_code == 200:
                    translated_parts.append(r.json()['message']['result']['translatedText'])
                else:
                    translated_parts.append(part)
            except Exception as e:
                print(f"⚠ Translation error: {e}")
                translated_parts.append(part)
        
        results.append(" ".join(translated_parts))
    
    return results


def translate_structure(structure: Dict[str, Any], source: str, target: str,
                       papago_client_id: str, papago_client_secret: str) -> Dict[str, Any]:
    """
    Translate hierarchical structure from source language to target language.
    Translates all 'name' and 'synthesis' fields throughout the structure.
    
    Args:
        structure: Hierarchical structure dict with domain and categories
        source: Source language code (ko, ja, zh, etc.)
        target: Target language code (typically 'en')
        papago_client_id: Papago API client ID
        papago_client_secret: Papago API secret
    
    Returns:
        Translated structure (deep copy with translations applied)
    """
    if source == target or not structure:
        return structure
    
    # Create deep copy to avoid modifying original
    translated_structure = deepcopy(structure)
    
    # Collect all texts to translate in order
    texts_to_translate = []
    indices = []  # Track which field each translation belongs to
    
    # Domain
    domain = translated_structure.get("domain", {})
    if domain.get("name"):
        texts_to_translate.append(domain["name"])
        indices.append(("domain", "name"))
    if domain.get("synthesis"):
        texts_to_translate.append(domain["synthesis"])
        indices.append(("domain", "synthesis"))
    
    # Categories
    for cat_idx, cat in enumerate(translated_structure.get("categories", [])):
        if cat.get("name"):
            texts_to_translate.append(cat["name"])
            indices.append(("category", cat_idx, "name"))
        if cat.get("synthesis"):
            texts_to_translate.append(cat["synthesis"])
            indices.append(("category", cat_idx, "synthesis"))
        
        # Concepts
        for concept_idx, concept in enumerate(cat.get("concepts", [])):
            if concept.get("name"):
                texts_to_translate.append(concept["name"])
                indices.append(("concept", cat_idx, concept_idx, "name"))
            if concept.get("synthesis"):
                texts_to_translate.append(concept["synthesis"])
                indices.append(("concept", cat_idx, concept_idx, "synthesis"))
            
            # Subconcepts
            for sub_idx, sub in enumerate(concept.get("subconcepts", [])):
                if sub.get("name"):
                    texts_to_translate.append(sub["name"])
                    indices.append(("subconcept", cat_idx, concept_idx, sub_idx, "name"))
                if sub.get("synthesis"):
                    texts_to_translate.append(sub["synthesis"])
                    indices.append(("subconcept", cat_idx, concept_idx, sub_idx, "synthesis"))
    
    # Translate all at once
    if texts_to_translate:
        translated_texts = translate_batch(
            texts_to_translate, 
            source, target,
            papago_client_id, papago_client_secret
        )
        
        # Apply translations back to structure
        for idx, translated_text in zip(indices, translated_texts):
            if idx[0] == "domain":
                translated_structure["domain"][idx[1]] = translated_text
            elif idx[0] == "category":
                translated_structure["categories"][idx[1]][idx[2]] = translated_text
            elif idx[0] == "concept":
                translated_structure["categories"][idx[1]]["concepts"][idx[2]][idx[3]] = translated_text
            elif idx[0] == "subconcept":
                translated_structure["categories"][idx[1]]["concepts"][idx[2]]["subconcepts"][idx[3]][idx[4]] = translated_text
    
    return translated_structure


def translate_chunk_analysis(chunk_data: Dict[str, Any], source: str, target: str,
                            papago_client_id: str, papago_client_secret: str) -> Dict[str, Any]:
    """
    Translate chunk analysis results from source language to target language.
    Translates topic, concepts, summary, and key_claims fields.
    
    Args:
        chunk_data: Chunk analysis dict with topic, concepts, summary, etc.
        source: Source language code
        target: Target language code
        papago_client_id: Papago API client ID
        papago_client_secret: Papago API secret
    
    Returns:
        Translated chunk analysis
    """
    if source == target or not chunk_data:
        return chunk_data
    
    translated = deepcopy(chunk_data)
    
    # Collect texts to translate
    texts_to_translate = []
    
    if translated.get('topic'):
        texts_to_translate.append(translated['topic'])
    
    for concept in translated.get('concepts', []):
        texts_to_translate.append(concept)
    
    if translated.get('summary'):
        texts_to_translate.append(translated['summary'])
    
    for claim in translated.get('key_claims', []):
        texts_to_translate.append(claim)
    
    # Translate all
    if texts_to_translate:
        translated_texts = translate_batch(
            texts_to_translate,
            source, target,
            papago_client_id, papago_client_secret
        )
        
        # Apply translations
        text_idx = 0
        
        if translated.get('topic'):
            translated['topic'] = translated_texts[text_idx]
            text_idx += 1
        
        if translated.get('concepts'):
            for i in range(len(translated['concepts'])):
                translated['concepts'][i] = translated_texts[text_idx]
                text_idx += 1
        
        if translated.get('summary'):
            translated['summary'] = translated_texts[text_idx]
            text_idx += 1
        
        if translated.get('key_claims'):
            for i in range(len(translated['key_claims'])):
                translated['key_claims'][i] = translated_texts[text_idx]
                text_idx += 1
    
    return translated