"""
core/notifications.py

Protean Pursuits — Shared notification utilities

Primary: Pushover mobile push notifications
Fallback: Log file at logs/notifications.log

Required .env keys:
    PUSHOVER_USER_KEY  — your Pushover user key
    PUSHOVER_API_TOKEN — your Pushover application token
"""

import os
import json
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv("config/.env")

PP_PREFIX = "PROTEAN"
PUSHOVER_API_URL = "https://api.pushover.net/1/messages.json"


def _log_notification(subject: str, message: str) -> None:
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / "notifications.log"
    entry = (
        f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC] "
        f"{subject}\n{message}\n{'─'*60}\n"
    )
    with open(log_path, "a") as f:
        f.write(entry)


def send_pushover(subject: str, message: str, priority: int = 0) -> bool:
    user_key = os.getenv("PUSHOVER_USER_KEY", "")
    api_token = os.getenv("PUSHOVER_API_TOKEN", "")
    if not user_key or not api_token:
        print("⚠️  Pushover credentials not set in config/.env")
        return False
    try:
        data = urllib.parse.urlencode({
            "token":    api_token,
            "user":     user_key,
            "title":    subject[:250],
            "message":  message[:1024],
            "priority": priority,
        }).encode("utf-8")
        req = urllib.request.Request(PUSHOVER_API_URL, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            if result.get("status") == 1:
                print(f"📱 Pushover sent: {subject[:60]}")
                return True
            else:
                print(f"⚠️  Pushover error: {result}")
                return False
    except Exception as e:
        print(f"⚠️  Pushover failed: {e}")
        return False


def send_sms(message: str, prefix: str = PP_PREFIX) -> bool:
    return send_pushover(f"[{prefix}] SMS", message, priority=1)


def send_email(subject: str, body: str) -> bool:
    return send_pushover(subject, body, priority=0)


def notify_human(subject: str, message: str, team: str = PP_PREFIX) -> None:
    full_subject = f"[{team}] {subject}"
    _log_notification(full_subject, message)
    success = send_pushover(full_subject, message, priority=1)
    if not success:
        print(f"📝 Notification logged to logs/notifications.log")
