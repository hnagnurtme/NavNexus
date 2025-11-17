import requests

CLIENT_ID = ""
CLIENT_SECRET = ""

def translate(text, source='vi', target='en'):
    url = "https://papago.apigw.ntruss.com/nmt/v1/translation"
    headers = {
        "X-NCP-APIGW-API-KEY-ID": CLIENT_ID,
        "X-NCP-APIGW-API-KEY": CLIENT_SECRET,
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
    }
    data = {
        "source": source,
        "target": target,
        "text": text
    }

    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        result = response.json()
        return result['message']['result']['translatedText']
    else:
        print("Error:", response.status_code, response.text)
        return None

if __name__ == "__main__":
    vietnamese_text = "Xin chào, bạn có khỏe không?"
    english_text = translate(vietnamese_text)
    print("Vietnamese:", vietnamese_text)
    print("English:", english_text)
