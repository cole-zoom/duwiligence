from flask import Flask, request, jsonify
import os
import requests
import json

LLM_API_URL = "https://api.openai.com/v1/chat/completions"
LLM_API_KEY = os.environ.get("LLM_API_KEY")
print(LLM_API_KEY)
HEADERS = {
    "Authorization": f"Bearer {LLM_API_KEY}",
    "Content-Type": "application/json"
}

app = Flask(__name__)

@app.route("/extract", methods=["POST"])
def extract():
    data = request.get_json(force=True)
    emails = data.get("emails", [])
    portfolios = fetch_portfolios()

    print(f"[INFO] Received {len(emails)} emails")

    for stock in portfolios:
        ticker = stock['symbol']
        for idx, email in enumerate(emails, start=1):
            list_of_stories = call_llm(ticker, str(email['body']))
            print(list_of_stories)



    return jsonify({
        "status": "success",
        "processed": len(emails)
    }), 200

def call_llm(ticker, email):
    prompt = f"""
You are a financial assistant. Your job is to carefully review the following newsletter content, which contains one or more startup or tech-related stories.

You are also given a list of stock ticker symbols (e.g. AAPL, GOOG, TSLA). Your task is to check if *any of the stories* in the newsletter relate in any way — directly or indirectly — to any of the companies represented by those ticker symbols.

If a story is related, you must include it in a JSON list in the following format:
```json
[
  {{
    "title": "title of the story",
    "body": "full text of the story",
    "explanation": "explain clearly how and why this story is related to the stock symbol(s)",
    "confidence": <confidence_score from 0 to 100>
  }},
  ...
]
```

If there is no related stories, YOU MUST GIVE BACK AN EMPTY LIST
```json
[]
```

Only include stories that have a meaningful or plausible connection to the stock tickers. Ignore all others. Be conservative and avoid hallucinating connections.

Here is the stock symbol to check against:
{ticker}

Here is the newsletter content:

{email}

    """
    response = requests.post(LLM_API_URL, headers=HEADERS, json={
        "model": "gpt-4o",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0
    })
    result = response.json()
    print(result)
    try:
        text = result['choices'][0]['message']['content']
        
        cleaned_text = text.replace('```json', '').replace('```', '').strip()
        if cleaned_text.startswith('[') and cleaned_text.endswith(']'):
            return json.loads(cleaned_text)
            
        return {"title": False, "body": 0, "explanation": f"LLM failed: {e}", "confidence": 100 }
    except Exception as e:
        return {"title": False, "body": 0, "explanation": f"LLM failed: {e}", "confidence": 100 }


def fetch_portfolios():
    return[
        {
            'symbol': 'VGT',
            'portfolio': 'Cash'
        },
        {
            'symbol': 'VOOG',
            'portfolio': 'Cash'
        },
        {
            'symbol': 'PLTR',
            'portfolio': 'Cash'
        },
        {
            'symbol': 'VDE',
            'portfolio': 'Cash'
        },
        {
            'symbol': 'NVDA',
            'portfolio': 'Cash'
        },
        {
            'symbol': 'META',
            'portfolio': 'Cash'
        },
        {
            'symbol': 'RY',
            'portfolio': 'Cash'
        },
        {
            'symbol': 'CDNS',
            'portfolio': 'Cash'
        }
    
    ]

if __name__ == "__main__":
    app.run(debug=True, port=8080)
