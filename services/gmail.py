import os
import smtplib
import logging
from email.message import EmailMessage

# Set up logger
logger = logging.getLogger(__name__)

# Environment variables
GMAIL_USER = os.environ.get("GMAIL_USER")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")


def send_email_gmail(pdf_path, to_email):
    """
    Send an email with PDF attachment using Gmail SMTP.
    
    Args:
        pdf_path (str): Path to the PDF file to attach
        to_email (str): Recipient email address
    """
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
    
    logger.info(f"[LOG] Email sent successfully to {to_email}")
