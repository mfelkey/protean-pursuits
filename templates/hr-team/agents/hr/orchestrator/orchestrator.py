"""
agents/orchestrator/orchestrator.py

Protean Pursuits — HR Team Orchestrator

Scope: Portfolio-wide — serves all Protean Pursuits teams and projects.

Workforce model: Humans only. No contractor staffing recommendations.
                 No AI or bot role suggestions. All people decisions
                 require human approval before any action is taken.

Cross-team coordination: HR flags items to Legal (employment law,
compliance), Finance (compensation, budget), Strategy (headcount planning,
org design), and QA (process compliance) via FLAGS in every output.

Run modes:
  RECRUIT      — end-to-end hiring process for a role or team
  ONBOARD      — new hire onboarding plan for an individual or cohort
  REVIEW       — performance review cycle or individual review support
  POLICY       — draft or update an HR policy or handbook section
  CULTURE      — culture health check or engagement initiative
  BENEFITS     — benefits design or review for a team/company
  FULL_CYCLE   — all agents, complete HR package for a project/initiative

Human-in-the-loop: ALL outputs require human review and approval before
any action affecting a person is taken. Compensation figures and
disciplinary actions escalate immediately.
"""

import os
import json
import uuid
import time
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, LLM

load_dotenv("config/.env")


# ── HR output standards ───────────────────────────────────────────────────────

HR_INSTRUCTION = """
HR OUTPUT STANDARDS — MANDATORY ON ALL OUTPUTS:

1. HUMANS ONLY: All recommendations assume a human workforce. Never suggest
   replacing a human role with AI, automation, or a bot. If automation can
   assist a human in a role, describe it as tooling support — not replacement.

2. CROSS-TEAM FLAGS: End every output with a CROSS-TEAM FLAGS section.
   Flag items that require input from: Legal (employment law, compliance),
   Finance (budget, compensation bands), Strategy (org design, headcount),
   QA (process compliance). Format: [TEAM — DESCRIPTION OF ITEM].

3. CONFIDENTIALITY: All HR outputs are confidential. Never include individual
   employee names in document titles or file names. Use role titles or
   cohort descriptions instead.

4. NO UNILATERAL DECISIONS: HR documents recommend — they do not decide.
   Every compensation figure, disciplinary action, and termination requires
   explicit human sign-off. Flag these clearly with: ⚠️ REQUIRES HUMAN APPROVAL.

5. LEGAL DISCLAIMER: HR outputs are internal guidance only. They are not
   legal advice. Employment law questions must be referred to Legal.

6. OPEN QUESTIONS: End every output with an OPEN QUESTIONS section listing
   decisions that require human input before the recommendation is actioned.
"""

# ── Cross-team coordination flags ─────────────────────────────────────────────

CROSS_TEAM_TRIGGERS = {
    "legal":    ["termination", "disciplinary", "FMLA", "ADA", "accommodation",
                 "harassment", "discrimination", "background check", "visa",
                 "non-compete", "arbitration", "severance", "redundancy"],
    "finance":  ["salary", "compensation", "bonus", "equity", "budget",
                 "headcount", "benefits cost", "payroll", "raise", "promotion"],
    "strategy": ["org design", "team structure", "headcount plan", "reorg",
                 "leadership", "succession", "workforce planning"],
    "qa":       ["process", "compliance", "audit", "documentation", "SOP",
                 "checklist", "training compliance"],
}


# ── Notification helpers ───────────────────────────────────────────────────────

def send_sms(message: str) -> bool:
    try:
        import smtplib
        from email.mime.text import MIMEText
        sms_addr = os.getenv("HUMAN_PHONE_NUMBER", "").replace("+1", "") + "@txt.att.net"
        msg = MIMEText(message[:160])
        msg["From"] = os.getenv("OUTLOOK_ADDRESS")
        msg["To"]   = sms_addr
        msg["Subject"] = ""
        with smtplib.SMTP("smtp.office365.com", 587) as s:
            s.ehlo(); s.starttls()
            s.login(os.getenv("OUTLOOK_ADDRESS"), os.getenv("OUTLOOK_PASSWORD"))
            s.send_message(msg)
        return True
    except Exception as e:
        print(f"⚠️  SMS failed: {e}")
        return False


def send_email(subject: str, body: str) -> bool:
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        msg = MIMEMultipart()
        msg["From"]    = os.getenv("OUTLOOK_ADDRESS")
        msg["To"]      = os.getenv("HUMAN_EMAIL")
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP("smtp.office365.com", 587) as s:
            s.ehlo(); s.starttls()
            s.login(os.getenv("OUTLOOK_ADDRESS"), os.getenv("OUTLOOK_PASSWORD"))
            s.send_message(msg)
        return True
    except Exception as e:
        print(f"⚠️  Email failed: {e}")
        return False


def notify_human(subject: str, message: str) -> None:
    send_sms(f"[HR-TEAM] {subject}\n{message}")
    send_email(f"[HR-TEAM] {subject}", message)


# ── HITL review gate ───────────────────────────────────────────────────────────

def request_human_review(artifact_path: str, summary: str,
                          timeout_hours: int = 48) -> bool:
    approval_dir = "logs/approvals"
    os.makedirs(approval_dir, exist_ok=True)
    review_id    = f"HR-{uuid.uuid4().hex[:8].upper()}"
    response_file = f"{approval_dir}/{review_id}.response.json"

    with open(f"{approval_dir}/{review_id}.json", "w") as f:
        json.dump({
            "review_id":     review_id,
            "artifact_path": artifact_path,
            "summary":       summary,
            "requested_at":  datetime.utcnow().isoformat(),
            "status":        "PENDING"
        }, f, indent=2, default=str)

    notify_human(
        subject=f"[HR REVIEW] {review_id}",
        message=(
            f"Summary: {summary}\nArtifact: {artifact_path}\n\n"
            f"Approve: write to {response_file}:\n"
            f'  {{"decision": "APPROVED"}}\n'
            f"Reject: {{\"decision\": \"REJECTED\", \"reason\": \"...\"}}\n"
            f"Timeout: {timeout_hours}h"
        )
    )
    print(f"\n⏸️  [HR REVIEW] {review_id} — {summary}")
    print(f"📄 Artifact: {artifact_path}")

    elapsed = 0
    while elapsed < timeout_hours * 3600:
        if os.path.exists(response_file):
            with open(response_file) as f:
                resp = json.load(f)
            decision = resp.get("decision", "").upper()
            if decision == "APPROVED":
                print(f"✅ Approved — {review_id}")
                return True
            elif decision == "REJECTED":
                print(f"❌ Rejected — {review_id}: {resp.get('reason', '')}")
                return False
        time.sleep(30)
        elapsed += 30

    print(f"⏰ Timed out — {review_id}")
    return False


# ── Context helpers ────────────────────────────────────────────────────────────

def create_hr_context(project_name: str, hr_mode: str,
                      project_id: str = None) -> dict:
    return {
        "framework":    "protean-pursuits-hr",
        "hr_id":        f"HR-{uuid.uuid4().hex[:8].upper()}",
        "project_name": project_name,
        "hr_mode":      hr_mode,
        "project_id":   project_id,
        "created_at":   datetime.utcnow().isoformat(),
        "status":       "INITIATED",
        "artifacts":    [],
        "cross_team_flags": [],
        "events":       []
    }


def save_context(context: dict) -> str:
    os.makedirs("logs", exist_ok=True)
    path = f"logs/{context['hr_id']}.json"
    with open(path, "w") as f:
        json.dump(context, f, indent=2, default=str)
    return path


def log_event(context: dict, event_type: str, detail: str = "") -> None:
    context["events"].append({
        "event_type": event_type,
        "detail":     detail,
        "timestamp":  datetime.utcnow().isoformat()
    })
    save_context(context)


def save_artifact(context: dict, name: str, artifact_type: str,
                  content: str, output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    ts   = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = f"{output_dir}/{context['hr_id']}_{artifact_type}_{ts}.md"
    with open(path, "w") as f:
        f.write(content)
    context["artifacts"].append({
        "name":       name,
        "type":       artifact_type,
        "path":       path,
        "status":     "PENDING_REVIEW",
        "created_at": datetime.utcnow().isoformat()
    })
    log_event(context, f"{artifact_type}_COMPLETE", path)
    print(f"\n💾 [{artifact_type}] Saved: {path}")
    return path


# ── HR Orchestrator agent ──────────────────────────────────────────────────────

def build_hr_orchestrator() -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/qwen3:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )
    return Agent(
        role="HR Team Orchestrator",
        goal=(
            "Coordinate the HR Team to produce people operations outputs — "
            "recruiting plans, onboarding programmes, performance frameworks, "
            "HR policies, culture initiatives, and benefits design — for any "
            "Protean Pursuits project or team expansion."
        ),
        backstory=(
            "You are the Chief People Officer at Protean Pursuits LLC — an HR "
            "leader with 18 years of experience building people functions at "
            "high-growth technology companies. You have led HR teams through "
            "rapid scale (0 to 200 people), international expansion, and "
            "remote-first transformations. "
            "You lead six specialist agents: Recruiting, Onboarding, Performance "
            "& Compensation, Policy & Compliance, Culture & Engagement, and "
            "Benefits. You orchestrate them based on what each project or "
            "initiative actually needs. "
            "Your workforce model is humans only — you never recommend replacing "
            "a person with AI or automation. Technology is a tool that helps "
            "your people do their best work. "
            "You coordinate closely with Legal (employment law, compliance), "
            "Finance (compensation bands, headcount budgets), Strategy (org "
            "design, workforce planning), and QA (process compliance). You "
            "flag items to those teams proactively in every output. "
            "All your outputs are confidential, recommendation-based, and "
            "require human approval before any action affecting a person "
            "is taken. You are thorough, empathetic, and direct."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=True
    )
