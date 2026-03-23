import os
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, LLM

load_dotenv("config/.env")

from config.langfuse_setup import init_langfuse
init_langfuse()

# ── Notification helpers ──────────────────────────────────────────────────────

def send_sms(message: str) -> bool:
    """Send SMS via AT&T email-to-text gateway. Returns True on success."""
    try:
        import smtplib
        from email.mime.text import MIMEText

        # AT&T email-to-text gateway
        sms_address = os.getenv("HUMAN_PHONE_NUMBER", "").replace("+1", "") + "@txt.att.net"

        msg = MIMEText(message[:160])  # SMS limit
        msg["From"] = os.getenv("GMAIL_ADDRESS")
        msg["To"] = sms_address
        msg["Subject"] = ""

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(
                os.getenv("GMAIL_ADDRESS"),
                os.getenv("GMAIL_APP_PASSWORD")
            )
            server.send_message(msg)
        print(f"📱 SMS sent via AT&T gateway: {message[:60]}...")
        return True
    except Exception as e:
        print(f"⚠️  SMS failed: {e}")
        return False

def send_email(subject: str, body: str) -> bool:
    """Send email via Gmail SMTP. Returns True on success."""
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        msg = MIMEMultipart()
        msg["From"] = os.getenv("GMAIL_ADDRESS")
        msg["To"] = os.getenv("HUMAN_EMAIL")
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(
                os.getenv("GMAIL_ADDRESS"),
                os.getenv("GMAIL_APP_PASSWORD")
            )
            server.send_message(msg)
        print(f"📧 Email sent: {subject}")
        return True
    except Exception as e:
        print(f"⚠️  Email failed: {e}")
        return False

def notify_human(subject: str, message: str) -> None:
    """Send notification via SMS (primary) and email (secondary)."""
    sms_sent = send_sms(f"[DEV-TEAM] {subject}\n{message}")
    send_email(f"[DEV-TEAM] {subject}", message)
    if not sms_sent:
        print("⚠️  Primary notification (SMS) failed. Email attempted as fallback.")

# ── Project context ───────────────────────────────────────────────────────────

def create_project_context(natural_language_request: str, classification: str) -> dict:
    """Initialize a structured project context object."""
    return {
        "project_id": f"PROJ-{uuid.uuid4().hex[:8].upper()}",
        "created_at": datetime.utcnow().isoformat(),
        "status": "INITIATED",
        "classification": classification,  # DEV | DS | JOINT
        "original_request": natural_language_request,
        "structured_spec": {},             # Filled by Orchestrator
        "assigned_crew": None,
        "checkpoints": [],
        "handoffs": [],
        "artifacts": [],
        "audit_log": []
    }

def log_event(context: dict, event: str, detail: str = "") -> dict:
    """Append an event to the project audit log."""
    context["audit_log"].append({
        "timestamp": datetime.utcnow().isoformat(),
        "event": event,
        "detail": detail
    })
    return context

def save_context(context: dict) -> None:
    """Persist project context to logs directory."""
    os.makedirs("logs", exist_ok=True)
    path = f"logs/{context['project_id']}.json"
    with open(path, "w") as f:
        json.dump(context, f, indent=2)
    print(f"💾 Context saved: {path}")

# ── Checkpoint handler ────────────────────────────────────────────────────────

def request_human_approval(context: dict, checkpoint_name: str, 
                            summary: str) -> bool:
    """
    Notify human, wait for approval input.
    Returns True if approved, False if rejected.
    """
    message = (
        f"Project: {context['project_id']}\n"
        f"Checkpoint: {checkpoint_name}\n"
        f"Action required: Review and approve to continue.\n\n"
        f"{summary}\n\n"
        f"Reply APPROVE or REJECT in terminal."
    )
    notify_human(f"Approval needed: {checkpoint_name}", message)
    log_event(context, f"CHECKPOINT: {checkpoint_name}", "Awaiting human approval")
    save_context(context)

    print(f"\n{'='*60}")
    print(f"⏸️  CHECKPOINT: {checkpoint_name}")
    print(f"Project: {context['project_id']}")
    print(f"\n{summary}")
    print(f"{'='*60}")

    while True:
        response = input("\nType APPROVE or REJECT: ").strip().upper()
        if response == "APPROVE":
            log_event(context, f"APPROVED: {checkpoint_name}")
            save_context(context)
            return True
        elif response == "REJECT":
            log_event(context, f"REJECTED: {checkpoint_name}")
            save_context(context)
            return False
        else:
            print("Please type APPROVE or REJECT.")

# ── Agent factory ─────────────────────────────────────────────────────────────

def build_devteam_orchestrator() -> Agent:
    """Instantiate and return the Dev-Team Orchestrator agent."""
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/gpt-oss:120b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    )

    return Agent(
        role="Dev-Team Orchestrator",
        goal=(
            "Receive software development project requests, initialize structured "
            "project context, route to the correct dev sub-team (backend, frontend, "
            "mobile, DevOps, QA), manage checkpoints, coordinate handoffs between "
            "agents, and ensure complete audit trails."
        ),
        backstory=(
            "You are the Dev-Team Orchestrator — the central coordinator for a "
            "federated AI software development system. You manage the full dev "
            "pipeline: product requirements, technical architecture, backend, "
            "frontend, mobile (React Native, DevOps, QA), security review, "
            "infrastructure, and quality assurance. You structure incoming work "
            "into actionable project specs and coordinate execution with human "
            "oversight at every major decision. "
            "You never proceed past a checkpoint without explicit human approval."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=True
    )
