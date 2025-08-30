import asyncio
import json
import logging
import os
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

async def generate_and_send_single_newsletter(email, portfolio_data, stories):
    """
    Generate and send newsletter for a single user's portfolio with pre-processed stories.
    
    Args:
        email (str): User's email address
        portfolio_data (dict): Complete portfolio object with all accounts
        stories (str): Pre-processed stories content
    """
    logger.info(f"[LOG] Processing newsletter for {email}")
    
    client = create_openai_client()
    
    # Extract all tickers from all accounts in the portfolio
    all_tickers = []
    for account_name, tickers in portfolio_data.items():
        all_tickers.extend(tickers)
    
    # Remove duplicates while preserving order
    unique_tickers = []
    seen = set()
    for ticker in all_tickers:
        if ticker not in seen:
            unique_tickers.append(ticker)
            seen.add(ticker)
    
    logger.info(f"[LOG] Processing portfolio with {len(unique_tickers)} unique tickers across {len(portfolio_data)} accounts")
    
    letter = await call_llm(unique_tickers, stories, client)
    logger.info(f"[LOG] Generated newsletter content")
    
    tmp_path = "/tmp/newsletter.pdf"
    
    try:
        logger.info(f"[LOG] Generating PDF at {tmp_path}")
        generate_pdf(letter, tmp_path)
        logger.info(f"[LOG] PDF generated successfully")
    except Exception as e:
        logger.error(f"[ERROR] Failed to generate PDF: {e}")
        return
    
    try:
        logger.info(f"[LOG] Sending email with PDF attachment to {email}")
        send_email_gmail(tmp_path, email)
        logger.info(f"[LOG] Email sent successfully to {email}")
    except Exception as e:
        logger.error(f"[ERROR] Failed to send email to {email}: {e}")
        return
    
    logger.info(f"[LOG] Newsletter processing completed successfully for {email}")

@app.route("/generate-newsletters", methods=["POST"])
def generate_newsletters_orchestrator():
    """
    Receives emails from Google Apps Script, prepares shared content,
    and creates a Cloud Task for each portfolio.
    """
    logger.info("[LOG] Orchestrator triggered by Apps Script...")
    
    # 1. Receive and process the emails into a single 'stories' string
    try:
        request_data = request.get_json(force=True)
        emails = request_data.get("emails", [])
        if not emails:
            return jsonify({"status": "error", "message": "No emails provided"}), 400
    except Exception as e:
        logger.error(f"[ERROR] Failed to parse JSON from request: {e}")
        return jsonify({"status": "error", "message": "Invalid JSON"}), 400

    stories = ''
    for email in emails:
        stories += f"Article by: {email.get('from', 'Unknown')}\n Story: {email.get('body', '')}\n\n"
    
    logger.info(f"[LOG] Aggregated {len(emails)} emails into shared stories content.")

    # 2. Fetch all portfolios from your database
    portfolios = fetch_portfolios()
    logger.info(f"[LOG] Found {len(portfolios)} portfolios to process.")

    # 3. Create one task per portfolio, including the shared stories
    client = tasks_v2.CloudTasksClient()
    parent = client.queue_path(PROJECT_ID, REGION, QUEUE_ID)

    for user_portfolio in portfolios:
        # Extract email and portfolio from the user_portfolio dict
        email = list(user_portfolio.keys())[0]
        portfolio = user_portfolio[email]
        
        payload = {
            'email': email,
            'tickers': portfolio,  # This is now the entire portfolio object with all accounts
            'stories': stories,  # Include the same stories content in each task
            'timestamp': int(time.time() * 1000)
        }
        
        task = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": CLOUD_RUN_URL,  # URL to your /worker endpoint
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(payload).encode(),
                "oidc_token": {"service_account_email": SERVICE_ACCOUNT_EMAIL}
            }
        }
        response = client.create_task(request={"parent": parent, "task": task})
        logger.info(f"[LOG] Created task {response.name} for portfolio")

    return jsonify({"status": "tasks created", "count": len(portfolios)}), 200

@app.route("/worker", methods=["POST"])
def worker():
    logger.info("[LOG] /worker endpoint triggered")
    try:
        payload = request.get_json(force=True)
        if not payload:
            logger.warning("[WARN] Dropped Cloud Task with no payload (likely a retry)")
            return "Dropped empty payload", 200

        # Check for timestamp and age validation
        timestamp = payload.get('timestamp')
        if not timestamp:
            logger.warning("[WARN] Dropped Cloud Task with no timestamp (likely a retry)")
            return "Dropped empty payload", 200 
        now_ms = int(datetime.now(tz=timezone.utc).timestamp() * 1000)
        age_ms = now_ms - timestamp
        logger.info(f'[LOG] Age of instance is {age_ms} ms')
        MAX_AGE_MS = 10000  
        if age_ms > MAX_AGE_MS:
            logger.info(f"[LOG] Dropping old task, age: {age_ms}ms")
            return "DROPPED_OLD_TASK", 200
        
        # Unpack the email, tickers, and stories from the payload
        email = payload.get('email')
        tickers_data = payload.get('tickers')
        stories_content = payload.get('stories')

        if not email or not tickers_data or not stories_content:
            logger.warning("[WARN] Dropped task with incomplete payload.")
            return "Incomplete payload", 200

        logger.info(f"[LOG] Processing portfolio for {email} with pre-processed stories")

        # Run the async function with the unpacked data
        asyncio.run(generate_and_send_single_newsletter(email, tickers_data, stories_content))
        return jsonify({"status": "completed"}), 200
    except Exception as e:
        logger.error(f"[ERROR] Worker failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=8080)
