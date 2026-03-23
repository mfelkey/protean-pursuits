"""
core/notifications.py

Protean Pursuits — Shared notification utilities

Email provider: Microsoft Outlook (smtp.office365.com:587 + STARTTLS)
SMS: AT&T email-to-text gateway (sent via Outlook)

Required .env keys:
    OUTLOOK_ADDRESS    — mike.felkey@outlook.com
    OUTLOOK_PASSWORD   — your Outlook password
    HUMAN_EMAIL        — where to receive notifications
    HUMAN_PHONE_NUMBER — e.g. +15551234567
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv("config/.env")

PP_PREFIX = "PROTEAN"
SMTP_HOST = "smtp.office365.com"
SMTP_PORT = 587


def _get_smtp_connection():
    """Return an authenticated Outlook SMTP connection."""
    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    server.ehlo()
    server.starttls()
    server.login(
        os.getenv("OUTLOOK_ADDRESS", ""),
        os.getenv("OUTLOOK_PASSWORD", "")
    )
    return server


def send_sms(message: str, prefix: str = PP_PREFIX) -> bool:
    """Send SMS via AT&T email-to-text gateway using Outlook."""
    try:
        phone = os.getenv("HUMAN_PHONE_NUMBER", "").replace("+1", "").replace("-", "").replace(" ", "")
        sms_address = f"{phone}@txt.att.net"
        msg = MIMEText(message[:160])
        msg["From"] = os.getenv("OUTLOOK_ADDRESS")
        msg["To"] = sms_address
        msg["Subject"] = ""
        with _get_smtp_connection() as server:
            server.send_message(msg)
        print(f"📱 SMS sent: {message[:60]}...")
        return True
    except Exception as e:
        print(f"⚠️  SMS failed: {e}")
        return False


def send_email(subject: str, body: str) -> bool:
    """Send email via Outlook SMTP."""
    try:
        msg = MIMEMultipart()
        msg["From"] = os.getenv("OUTLOOK_ADDRESS")
        msg["To"] = os.getenv("HUMAN_EMAIL", os.getenv("OUTLOOK_ADDRESS"))
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        with _get_smtp_connection() as server:
            server.send_message(msg)
        print(f"📧 Email sent: {subject}")
        return True
    except Exception as e:
        print(f"⚠️  Email failed: {e}")
        return False


def notify_human(subject: str, message: str, team: str = PP_PREFIX) -> None:
    """
    Send notification via SMS (primary) and email (secondary).
    team: prefix shown in subject (e.g. 'DEV', 'MARKETING', 'PROTEAN')
    """
    full_subject = f"[{team}] {subject}"
    send_sms(f"{full_subject}\n{message}")
    send_email(full_subject, message)
