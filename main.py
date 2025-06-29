from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv

# Load environment variables (optional)
load_dotenv()

app = Flask(__name__)

@app.route("/extract", methods=["POST"])
def extract():
    data = request.get_json(force=True)
    emails = data.get("emails", [])

    print(f"[INFO] Received {len(emails)} emails")

    for idx, email in enumerate(emails, start=1):
        print(f"\n--- Email {idx} ---")
        print(f"From   : {email.get('from')}")
        print(f"Date   : {email.get('date')}")
        print(f"Subject: {email.get('subject')}")
        print(f"Body   : {email.get('body')[:200]}...")  # Print first 200 chars

    return jsonify({
        "status": "success",
        "processed": len(emails)
    }), 200

if __name__ == "__main__":
    app.run(debug=True, port=8080)
