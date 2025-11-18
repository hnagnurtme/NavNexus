"""Translation module using Papago"""
import requests
from typing import List


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
        
        results.append("".join(translated_parts))
    
    return results
