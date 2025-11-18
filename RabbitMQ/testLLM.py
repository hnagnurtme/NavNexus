import os
import requests
import json
import uuid

# 🔑 Nhập thông tin API
API_KEY = "nv-9063a257def64d469cfe961cb502988e5RNo"  # Lấy từ CLOVA Studio Console
MODEL = "HCX-005"  # hoặc HCX-003 nếu bạn chỉ có quyền đó
API_URL = f"https://clovastudio.stream.ntruss.com/v3/chat-completions/{MODEL}"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "X-NCP-CLOVASTUDIO-REQUEST-ID": str(uuid.uuid4()),
    "Content-Type": "application/json; charset=utf-8",
    "Accept": "application/json"
}

data = {
    "messages": [
        {"role": "system", "content": "You are a helpful assistant that speaks Vietnamese."},
        {"role": "user", "content": "Xin chào, bạn có thể nói về HyperCLOVA X không?"}
    ],
    "topP": 0.8,
    "topK": 0,
    "temperature": 0.7,
    "maxTokens": 512,
    "repetitionPenalty": 1.1,
    "includeAiFilters": True
}

response = requests.post(API_URL, headers=headers, data=json.dumps(data))

if response.status_code == 200:
    result = response.json()
    print("✅ Kết quả:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
else:
    print("❌ Lỗi:", response.status_code)
    print(response.text)
