from resend import Client
from config import RESEND_API_KEY, RESEND_SENDER, SMS_GATEWAY_CONFIG
import requests
import json
import os
from requests.auth import HTTPBasicAuth
from datetime import datetime
from flask_jwt_extended import create_access_token

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
RESEND_CLIENT = Client(api_key=RESEND_API_KEY)

##FUNCTION FOR EMAIL WITH DEMO COMPATIBILITY

def send_email(to: str, subject: str, html: str, text: str = ""):
    if not all([to, subject, html]):
        raise ValueError("Recipient, subject, and HTML body are required.")

    if DEMO_MODE:
        return _send_demo_email(to, subject, html, text)
    else:
        return _send_real_email(to, subject, html, text)


def _send_real_email(to: str, subject: str, html: str, text: str = ""):
  
    if not all([to, subject, html]):
        raise ValueError("Recipient, subject, and HTML body are required.")

    payload = {
        "from": RESEND_SENDER,
        "to": to,
        "subject": subject,
        "html": html,
    }

    if text:
        payload["text"] = text

    try:
        response = RESEND_CLIENT.emails.send(payload)
        return response
    except Exception as e:
        raise RuntimeError(f"Failed to send email: {e}")
    
def _send_demo_email(to, subject, html, text=""):
    print(f"\n[DEMO EMAIL]")
    print(f"To: {to}")
    print(f"Subject: {subject}")
    print(f"HTML: {html}")
    if text:
        print(f"Text: {text}")
    
    return {
        "status": "demo-success",
        "to": to,
        "subject": subject,
        "timestamp": datetime.now().isoformat()
    }

## FUNCTION FOR SEND SMS WITH DEMO COMPATIBLITY

def send_sms(to_number: str, message_text: str) -> dict:
    if not to_number.startswith("+"):
        return {"status": 400, "error": "Phone number must include country code, e.g. +91"}

    if DEMO_MODE:
        return _send_demo_sms(to_number, message_text)
    else:
        return _send_real_sms(to_number, message_text)

def _send_real_sms(to_number: str, message_text: str) -> dict:
    if not to_number.startswith("+"):
        return {"status": 400, "error": "Phone number must include country code, e.g. +91"}

    payload = {
        "textMessage": {"text": message_text},
        "phoneNumbers": [to_number]
    }

    try:
        response = requests.post(
            SMS_GATEWAY_CONFIG["url"],
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            auth=HTTPBasicAuth(SMS_GATEWAY_CONFIG["username"], SMS_GATEWAY_CONFIG["password"]),
            timeout=5
        )
        response.raise_for_status()
        return {
            "status": response.status_code,
            "data": response.json()
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": 500,
            "error": str(e)
        }
    
def _send_demo_sms(to_number: str, message_text: str) -> dict:
    print(f"\n[DEMO SMS]")
    print(f"To: {to_number}")
    print(f"Message: {message_text}")
    return {
        "status": "demo-success",
        "to": to_number,
        "text": message_text,
        "timestamp": datetime.now().isoformat()
    }


def generate_jwt(user):
    return create_access_token(identity=user.id)