import asyncio
import base64
import json
import logging
import os
import requests
import smtplib
import time
from datetime import datetime, timezone
from email.message import EmailMessage
from flask import Flask, request, jsonify
from utils.generatepdf import generate_pdf
import httpx
from google.cloud import tasks_v2

# Set up logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ID = os.environ.get("GCP_PROJECT")
QUEUE_ID = "duw-background-tasks"
REGION = "us-east1"
CLOUD_RUN_URL = os.environ.get("WORKER_URL")  
SERVICE_ACCOUNT_EMAIL = os.environ.get("TASK_SERVICE_ACCOUNT")

LLM_API_URL = "https://api.openai.com/v1/chat/completions"
LLM_API_KEY = os.environ.get("LLM_API_KEY")
HEADERS = {
    "Authorization": f"Bearer {LLM_API_KEY}",
    "Content-Type": "application/json"
}
GMAIL_USER = os.environ.get("GMAIL_USER")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")

app = Flask(__name__)

async def process_emails_and_send_newsletter_async(emails):
    logger.info("[LOG] Background processing started (async)")
    portfolios = fetch_portfolios()
    logger.info(f"[LOG] Number of portfolios fetched: {len(portfolios)}")
    stockxstories = []
    BATCH_SIZE = 12
    for stock in portfolios:
        ticker = stock['symbol']
        logger.info(f"[LOG] Processing ticker: {ticker}")
        stories = []
        for i in range(0, len(emails), BATCH_SIZE):
            batch = emails[i:i+BATCH_SIZE]
            logger.info(f"[LOG] Processing batch {i//BATCH_SIZE+1} for ticker {ticker}")
            tasks = [call_llm(ticker, str(email['body'])) for email in batch]
            results = await asyncio.gather(*tasks)
            for idx, list_of_stories in enumerate(results):
                logger.info(f"[LOG] LLM returned {len(list_of_stories)} stories for ticker {ticker} on email {i+idx+1}")
                stories += list_of_stories
            if i + BATCH_SIZE < len(emails):
                logger.info(f"[LOG] Waiting 3 seconds before next batch for ticker {ticker}")
                await asyncio.sleep(3)
        stockxstories.append({
                'ticker': ticker,
                'stories': stories
            })
        logger.info(f"[LOG] Finished processing ticker {ticker}, total stories: {len(stories)}")
    non_empty_stories = [item for item in stockxstories if item.get("stories")]
    logger.info(f"[LOG] Number of non-empty stock stories: {len(non_empty_stories)}")
    tmp_path = "/tmp/newsletter.pdf"
    try:
        logger.info(f"[LOG] Generating PDF at {tmp_path}")
        generate_pdf(non_empty_stories, tmp_path)
        logger.info(f"[LOG] PDF generated successfully")
    except Exception as e:
        logger.error(f"[ERROR] Failed to generate PDF: {e}")
        return
    try:
        logger.info(f"[LOG] Sending email with PDF attachment to coledumanski@gmail.com")
        send_email_gmail(tmp_path, "coledumanski@gmail.com")
        send_email_gmail(tmp_path, "aidan8.kingsley@rogers.com")
        logger.info(f"[LOG] Email sent successfully")
    except Exception as e:
        logger.error(f"[ERROR] Failed to send email: {e}")
        return
    logger.info(f"[LOG] Background processing completed successfully (async)")

@app.route("/extract", methods=["POST"])
def extract():
    logger.info("[LOG] /extract endpoint called")
    try:
        data = request.get_json(force=True)
        logger.info(f"[LOG] Received request data: {json.dumps(data)[:500]}")
    except Exception as e:
        logger.error(f"[ERROR] Failed to parse JSON from request: {e}")
        return jsonify({"status": "error", "message": "Invalid JSON"}), 400
    emails = data.get("emails", [])
    logger.info(f"[LOG] Number of emails received: {len(emails)}")
    
    client = tasks_v2.CloudTasksClient()
    parent = client.queue_path(PROJECT_ID, REGION, QUEUE_ID)

    payload = {
        'emails': data,
        'timestamp': int(time.time() * 1000)
    }
    task = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": CLOUD_RUN_URL, 
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps(payload).encode(),
            "oidc_token": {
                "service_account_email": SERVICE_ACCOUNT_EMAIL
            }
        }
    }

    response = client.create_task(request={"parent": parent, "task": task})
    logger.info(f"[LOG] Task created: {response.name}")


    return jsonify({"status": "processing"}), 200

@app.route("/worker", methods=["POST"])
def worker():
    try:
        logger.info("[LOG] /worker endpoint triggered")
        payload = request.get_json(force=True)
        if not payload:
            logger.warning("[WARN] Dropped Cloud Task with no payload (likely a retry)")
            return "Dropped empty payload", 200 
          
        data = payload.get('emails')
        if not data:
            logger.warning("[WARN] Dropped Cloud Task with no data (likely a retry)")
            return "Dropped empty payload", 200  

        timestamp = payload.get('timestamp')
        if not timestamp:
            logger.warning("[WARN] Dropped Cloud Task with no timestamp (likely a retry)")
            return "Dropped empty payload", 200 
        now_ms = int(datetime.now(tz=timezone.utc).timestamp() * 1000)
        age_ms = now_ms-timestamp
        logger.info(f'[LOG] Age of instance is{age_ms} ms')
        MAX_AGE_MS = 10000  
        if age_ms > MAX_AGE_MS:
            logger.info(f"[LOG] Dropping old task, age: {age_ms}ms")
            return "DROPPED_OLD_TASK", 200

        emails = data.get("emails", [])
        logger.info(f"[LOG] Number of emails received in worker: {len(emails)}")

        asyncio.run(process_emails_and_send_newsletter_async(emails))
        return jsonify({"status": "completed"}), 200
    except Exception as e:
        logger.error(f"[ERROR] Worker failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

async def call_llm(ticker, email):
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
    max_retries = 1
    for i in range(max_retries):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(LLM_API_URL, headers=HEADERS, json={
                    "model": "gpt-4o",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0
                })
            logger.info(response)
            result = response.json()
            text = result['choices'][0]['message']['content']
            cleaned_text = text.replace('```json', '').replace('```', '').strip()
            if cleaned_text.startswith('[') and cleaned_text.endswith(']'):
                return json.loads(cleaned_text)
            await asyncio.sleep(i*2)
        except Exception as e:
            logger.error(f"[ERROR] LLM call failed for ticker {ticker}: {e}")
            await asyncio.sleep(i*2)
    return []
    
def send_email_gmail(pdf_path, to_email):
    msg = EmailMessage()
    msg['Subject'] = "Your Daily Newsletter"
    msg['From'] = GMAIL_USER
    msg['To'] = to_email
    msg.set_content("Attached is your newsletter PDF.")

    with open(pdf_path, 'rb') as f:
        msg.add_attachment(f.read(), maintype='application', subtype='pdf', filename='newsletter.pdf')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        smtp.send_message(msg)


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
        },
        {
            'symbol': 'AISP',
            'portfolio': 'Cash'
        },
        {
            'symbol': 'USE',
            'portfolio': 'Cash'
        },
        {
            'symbol': 'BFM',
            'portfolio': 'Cash'
        },
        {
            'symbol': 'VUS',
            'portfolio': 'Cash'
        },
        {
            'symbol': 'TD',
            'portfolio': 'Cash'
        },
        {
            'symbol': 'AMZN',
            'portfolio': 'Cash'
        },
        {
            'symbol': 'SCHD',
            'portfolio': 'Cash'
        },
        {
            'symbol': 'TSLA',
            'portfolio': 'Cash'
        },
        {
            'symbol': 'GOOG',
            'portfolio': 'Cash'
        },
        {
            'symbol': 'BTC',
            'portfolio': 'Cash'
        }
    
    ]

if __name__ == "__main__":
    app.run(debug=True, port=8080)
