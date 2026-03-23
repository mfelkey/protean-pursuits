import os
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, LLM

load_dotenv("config/.env")

# ── Notification helpers ──────────────────────────────────────────────────────

def send_sms(message: str) -> bool:
    """Send SMS via AT&T email-to-text gateway. Returns True on success."""
    try:
        import smtplib
        from email.mime.text import MIMEText

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
            server.login(os.getenv("GMAIL_ADDRESS"), os.getenv("GMAIL_APP_PASSWORD"))
            server.send_message(msg)
        print(f"📧 Email sent: {subject}")
        return True
    except Exception as e:
        print(f"⚠️  Email failed: {e}")
        return False


def notify_human(subject: str, message: str) -> None:
    """Send notification via SMS (primary) and email (secondary)."""
    sms_sent = send_sms(f"[MARKETING-TEAM] {subject}\n{message}")
    send_email(f"[MARKETING-TEAM] {subject}", message)
    if not sms_sent:
        print("⚠️  Primary notification (SMS) failed. Email attempted as fallback.")


# ── Human-in-the-loop approval gate ──────────────────────────────────────────

def request_human_approval(gate_type: str, artifact_path: str, summary: str) -> bool:
    """
    Pause execution and notify the human for approval.

    gate_type: 'POST', 'EMAIL', or 'VIDEO'
    artifact_path: path to the artifact awaiting approval
    summary: short description of what is being approved

    Returns True if approved, False if rejected.
    Blocks until a response file is written or timeout (24h).
    """
    import time

    approval_dir = "logs/approvals"
    os.makedirs(approval_dir, exist_ok=True)

    approval_id = f"APPROVAL-{uuid.uuid4().hex[:8].upper()}"
    approval_file = f"{approval_dir}/{approval_id}.json"
    response_file = f"{approval_dir}/{approval_id}.response.json"

    approval_request = {
        "approval_id": approval_id,
        "gate_type": gate_type,
        "artifact_path": artifact_path,
        "summary": summary,
        "requested_at": datetime.utcnow().isoformat(),
        "status": "PENDING"
    }

    with open(approval_file, "w") as f:
        json.dump(approval_request, f, indent=2)

    notify_human(
        subject=f"[APPROVAL REQUIRED] {gate_type} — {approval_id}",
        message=(
            f"A {gate_type} artifact requires your approval before publishing.\n\n"
            f"Summary: {summary}\n"
            f"Artifact: {artifact_path}\n"
            f"Approval ID: {approval_id}\n\n"
            f"To approve: write '{approval_id}:APPROVED' to {response_file}\n"
            f"To reject:  write '{approval_id}:REJECTED:<reason>' to {response_file}\n\n"
            f"This request will time out in 24 hours."
        )
    )

    print(f"\n⏸️  [{gate_type}] Human approval required — {approval_id}")
    print(f"   Artifact: {artifact_path}")
    print(f"   Waiting for response at: {response_file}\n")

    timeout_seconds = 86400  # 24 hours
    poll_interval = 30
    elapsed = 0

    while elapsed < timeout_seconds:
        if os.path.exists(response_file):
            with open(response_file) as f:
                response = json.load(f)
            decision = response.get("decision", "").upper()
            if decision == "APPROVED":
                print(f"✅ [{gate_type}] Approved by human — {approval_id}")
                log_event_raw(approval_id, gate_type, "APPROVED", artifact_path)
                return True
            elif decision == "REJECTED":
                reason = response.get("reason", "No reason provided")
                print(f"❌ [{gate_type}] Rejected by human — {approval_id}: {reason}")
                log_event_raw(approval_id, gate_type, "REJECTED", artifact_path, reason)
                return False
        time.sleep(poll_interval)
        elapsed += poll_interval

    print(f"⏰ [{gate_type}] Approval timed out — {approval_id}. Artifact NOT published.")
    log_event_raw(approval_id, gate_type, "TIMEOUT", artifact_path)
    return False


# ── Project context ───────────────────────────────────────────────────────────

def create_campaign_context(campaign_name: str, campaign_type: str) -> dict:
    """Initialize a structured campaign context object."""
    return {
        "project_id": "PROJ-TEMPLATE",
        "campaign_id": f"CAMP-{uuid.uuid4().hex[:8].upper()}",
        "campaign_name": campaign_name,
        "campaign_type": campaign_type,
        "created_at": datetime.utcnow().isoformat(),
        "status": "INITIATED",
        "artifacts": [],
        "events": [],
        "approvals": []
    }


def save_context(context: dict) -> str:
    """Persist campaign context to logs/."""
    os.makedirs("logs", exist_ok=True)
    path = f"logs/{context['campaign_id']}.json"
    with open(path, "w") as f:
        json.dump(context, f, indent=2)
    return path


def log_event(context: dict, event_type: str, detail: str = "") -> None:
    """Append a timestamped event to the campaign context."""
    context["events"].append({
        "event_type": event_type,
        "detail": detail,
        "timestamp": datetime.utcnow().isoformat()
    })
    save_context(context)


def log_event_raw(approval_id: str, gate_type: str, decision: str,
                  artifact_path: str, reason: str = "") -> None:
    """Log an approval event without a full context object."""
    os.makedirs("logs/approvals", exist_ok=True)
    entry = {
        "approval_id": approval_id,
        "gate_type": gate_type,
        "decision": decision,
        "artifact_path": artifact_path,
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat()
    }
    log_path = f"logs/approvals/{approval_id}.log.json"
    with open(log_path, "w") as f:
        json.dump(entry, f, indent=2)


# ── Orchestrator agent ────────────────────────────────────────────────────────

def build_marketing_orchestrator() -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/qwen3:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    return Agent(
        role="Marketing Orchestrator",
        goal=(
            "Plan, coordinate, and track all PROJECT_NAME_PLACEHOLDER marketing campaigns across "
            "social, video, email, and analytics workstreams — ensuring every deliverable "
            "is on-brand, on-schedule, and approved by the human before publishing."
        ),
        backstory=(
            "You are a Senior Marketing Operations Lead with 15 years of experience "
            "running multi-channel digital marketing programmes for high-growth SaaS "
            "and fintech products. You have deep expertise in campaign planning, "
            "content calendaring, and cross-team coordination. "
            "You are fluent in project management methodologies and use task management "
            "APIs to create, assign, and track work across the Social, Video, Email, "
            "and Analyst agents. You never let a deliverable go live without human "
            "approval — every post, email send, and video publish passes through a "
            "formal approval gate before execution. "
            "You understand the PROJECT_NAME_PLACEHOLDER brand deeply: data-forward, quietly "
            "confident, never hypey, never tipster-adjacent. You enforce brand voice "
            "across every agent output and reject anything that violates the standing "
            "'What We Never Say' rules from the Brand Guide. "
            "You are the single point of accountability for the marketing team. "
            "You brief each agent with the context they need, review their drafts, "
            "route approvals to the human, and log every decision. "
            "You produce a Campaign Brief for every campaign, a Weekly Status Report "
            "every Monday, and a Monthly Performance Summary aligned to the KPIs in "
            "the Marketing Plan."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=True
    )
