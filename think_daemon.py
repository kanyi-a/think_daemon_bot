import http
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os
import requests
import time
import json
import logging
from datetime import datetime

# Load environment variables
load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
ALERT_RECIPIENT = os.getenv("ALERT_RECIPIENT")

# --- Configuration ---
BOTS = {
    "KUESA": {
        "url": "http://kuesa.sandbox.think.ke/",
        "test_message": "Hello, What is KUESA in full?"
    },
    "Sccodev": {
        "url": "http://sccodev.sandbox.think.ke/",
        "test_message": "Hello, What is Sccodev in full?"
    },
    "NewRain": {
        "url": "http://newrain.sandbox.think.ke/",
        "test_message": "Hello, Where is New Rain located?"
    },
    "ODPC": {
        "url": "http://odpc.think.ke/",
        "test_message": "Hello, What is ODPC in full?"
    },
    "AgentAssistant": {
        "url": "http://agentassistant.sandbox.think.ke/",
        "test_message": "Hello, What is AgentAssistant in full?"
    },
    "Ammerah": {
        "url": "http://ameerah.sandbox.think.ke/",
        "test_message": "Hello, What facials do you offer for dry skin, and how much do they cost?"
    },
    "MPSR": {
        "url": "http://mpsr.sandbox.think.ke/",
        "test_message": "Hello, What is MPSR in full?"
    },
    "SHE": {
        "url": "http://she.sandbox.think.ke/",
        "test_message": "Hello, What is SHE in full?"
    },
    "NyumbaCinema": {
        "url": "http://nyumba.sandbox.think.ke/",
        "test_message": "Hello, How many people can the cinema seat?"
    },
    "BScompanion": {
        "url": "http://bscompanion.sandbox.think.ke/",
        "test_message": "Hello, Can you give me name suggestions for my nail business"
    },
    "RRM": {
        "url": "http://rrm.sandbox.think.ke/",
        "test_message": "Hello, What shops are in Roselyn riviera Mall?"
    },
    "ThinkSafety": {
        "url": "http://thinksafety.sandbox.think.ke/",
        "test_message": "Hello, What information can you provide me with?"
    },
    "Govbot": {
        "url": "http://govstack-api.think.ke/",
        "test_message": "Hello, What services does Govbot offer?"
    }

}


LOG_FILE = "bot_monitor.log"

# --- Setup logging ---
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(message)s')

def send_email_alert(subject, body):
    """Send email alert using Amazon SES"""
    sender = os.getenv("EMAIL_SENDER", EMAIL_USER)
    try:
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = ALERT_RECIPIENT
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
        logging.info(f"📧 Email sent: {subject}")
    except Exception as e:
        logging.error(f"⚠️ Failed to send email: {e}")

def test_bot(name, bot_info):
    """Ping chatbot and record its status"""
    url = bot_info["url"]
    message = bot_info["test_message"]

    try:
        start = time.time()
        response = requests.post(url, json={"message": message}, timeout=20)
        latency = round(time.time() - start, 2)

        if response.status_code == 200 and len(response.text.strip()) > 5:
            logging.info(f"✅ {name} OK ({latency}s)")
            return {"bot": name, "status": "OK", "latency": latency}
        else:
            logging.warning(f"⚠️ {name} BAD RESPONSE ({response.status_code})")
            send_email_alert(
                subject=f"[ALERT] {name} failed test",
                body=f"{name} returned status {response.status_code} or invalid response at {datetime.now()}.\nTest message: {message}\nResponse: {response.text[:200]}"
            )
            return {"bot": name, "status": "BAD RESPONSE", "latency": latency}

    except Exception as e:
        logging.error(f"❌ {name} ERROR: {e}")
        send_email_alert(
            subject=f"[ERROR] {name} not reachable",
            body=f"{name} failed with error: {str(e)} at {datetime.now()}.\nTest message: {message}"
        )
        return {"bot": name, "status": "ERROR", "latency": None}


def run_all_tests():
    results = []
    for bot_name, bot_info in BOTS.items():
        result = test_bot(bot_name, bot_info)
        results.append(result)

    # Save results to JSON
    output = {"timestamp": str(datetime.now()), "results": results}
    with open("results.json", "a") as f:
        f.write(json.dumps(output) + "\n")


if __name__ == "__main__":
    run_all_tests()
