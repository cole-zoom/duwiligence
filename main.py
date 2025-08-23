import asyncio
import base64
import json
import logging
import os
import requests
import time
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from utils.generatepdf import generate_pdf
from google.cloud import tasks_v2
from services.gmail import send_email_gmail
from services.llm import call_llm, create_openai_client
from services.portfolio import fetch_portfolios

# Set up logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ID = os.environ.get("GCP_PROJECT")
QUEUE_ID = "duw-background-tasks"
REGION = "us-east1"
CLOUD_RUN_URL = os.environ.get("WORKER_URL")  
SERVICE_ACCOUNT_EMAIL = os.environ.get("TASK_SERVICE_ACCOUNT")



app = Flask(__name__)

async def process_emails_and_send_newsletter_async(emails):
    """
    This function processes the emails and sends the newsletter.
    """

    logger.info("[LOG] Background processing started (async)")
    portfolios = fetch_portfolios()
    logger.info(f"[LOG] Number of portfolios fetched: {len(portfolios)}")

    client = create_openai_client()
    stories = ''

    for email in emails:
        stories += f"Article by: {email['from']}\n Story: {email['body']}\n\n"

    # Process each portfolio
    letter = ''
    for portfolio in portfolios:

        tickers = [portfolio['symbol'] for portfolio in portfolios]
        
        logger.info(f"[LOG] Processing Portfolio")

        letter = call_llm(tickers, stories, client)

        logger.info(f"[LOG] Finished processing stories, total stories: {len(stories)}")
    
    logger.info(f"[LOG] Number of non-empty stock stories: {len(non_empty_stories)}")
    tmp_path = "/tmp/newsletter.pdf"

    try:
        logger.info(f"[LOG] Generating PDF at {tmp_path}")
        generate_pdf(letter, tmp_path)
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




if __name__ == "__main__":
    app.run(debug=True, port=8080)
