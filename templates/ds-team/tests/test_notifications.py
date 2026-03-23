import sys
sys.path.insert(0, "/home/mfelkey/dev-team")

import os
from dotenv import load_dotenv
load_dotenv("config/.env")

from agents.orchestrator.orchestrator import send_sms, send_email

print("Testing SMS...")
sms_ok = send_sms("DEV-TEAM: SMS notification test successful.")

print("Testing email...")
email_ok = send_email(
    subject="DEV-TEAM: Email Notification Test",
    body="This is a test email from your AI dev team notification system. If you received this, email notifications are working correctly."
)

print("\n=== NOTIFICATION TEST RESULTS ===")
print(f"SMS:   {'✅ OK' if sms_ok else '❌ FAILED'}")
print(f"Email: {'✅ OK' if email_ok else '❌ FAILED'}")
