"""
core/notifications.py

Protean Pursuits — Shared notification utilities

Single source of truth for SMS + email notifications.
All team orchestrators import from here when running under
Protean Pursuits. Standalone team repos carry their own copy
for independent operation.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv("config/.env")

PP_PREFIX = "PROTEAN"


def send_sms(message: str, prefix: str = PP_PREFIX) -> bool:
    """Send SMS via AT&T email-to-text gateway."""
    try:
        sms_address = os.getenv("HUMAN_PHONE_NUMBER", "").replace("+1", "") + "@txt.att.net"
        msg = MIMEText(message[:160])
        msg["From"] = os.getenv("GMAIL_ADDRESS")
        msg["To"] = sms_address
        msg["Subject"] = ""
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(os.getenv("GMAIL_ADDRESS"), os.getenv("GMAIL_APP_PASSWORD"))
            server.send_message(msg)
        print(f"📱 SMS sent: {message[:60]}...")
        return True
    except Exception as e:
        print(f"⚠️  SMS failed: {e}")
        return False


def send_email(subject: str, body: str) -> bool:
    """Send email via Gmail SMTP."""
    try:
        msg = MIMEMultipart()
        msg["From"] = os.getenv("GMAIL_ADDRESS")
        msg["To"] = os.getenv("HUMAN_EMAIL")
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(os.getenv("GMAIL_ADDRESS"), os.getenv("GMAIL_APP_PASSWORD"))
            server.send_message(msg)
        print(f"📧 Email sent: {subject}")
        return True
    except Exception as e:
        print(f"⚠️  Email failed: {e}")
        return False


def notify_human(subject: str, message: str, team: str = PP_PREFIX) -> None:
    """
    Send notification via SMS (primary) and email (secondary).
    team: prefix shown in notification subject (e.g. 'DEV', 'MARKETING', 'PROTEAN')
    """
    full_subject = f"[{team}] {subject}"
    send_sms(f"{full_subject}\n{message}")
    send_email(full_subject, message)
