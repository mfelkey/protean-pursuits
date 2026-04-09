"""
agents/orchestrator/orchestrator.py

Protean Pursuits — HR Team Orchestrator

Run modes (maps to hr_flow.py --mode):
  RECRUIT      — Job description, sourcing plan, interview guide
  ONBOARD      — Onboarding plan, checklist, tooling setup
  REVIEW       — Performance review framework, compensation analysis
  POLICY       — HR policy documents, compliance audit
  CULTURE      — Employee engagement plan, culture assessment
  BENEFITS     — Benefits analysis, vendor comparison
  FULL_CYCLE   — All modes sequenced as a complete HR package

Human-in-the-loop: ALL HR outputs require human approval before any action
affecting a person. The HR action gate fires automatically on every run.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))

import os
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Crew, Task, LLM

load_dotenv("config/.env")


# ── HR mode constants ─────────────────────────────────────────────────────────

HR_MODES = {
    "RECRUIT":    "Recruiting — job description, sourcing plan, interview guide",
    "ONBOARD":    "Onboarding — 30/60/90 day plan, checklist, tooling setup",
    "REVIEW":     "Performance & Compensation — review framework, comp analysis",
    "POLICY":     "Policy & Compliance — policy documents, compliance audit",
    "CULTURE":    "Culture & Engagement — engagement plan, culture assessment",
    "BENEFITS":   "Benefits — benefits analysis, vendor comparison, recommendations",
    "FULL_CYCLE": "Full Cycle — all HR modes sequenced as a complete package",
}

HR_INSTRUCTION = """
HR OUTPUT STANDARDS — MANDATORY:

1. HR ACTION GATE: No action affecting a person's employment, compensation,
   or status may be taken autonomously. Every such output must be held for
   human approval before any action is executed.

2. LEGAL COMPLIANCE BLOCK: Every HR output must include:
   ---
   JURISDICTION: [list applicable]
   LEGAL COMPLIANCE: [key statutes / regs considered]
   EXTERNAL COUNSEL FLAG: [REQUIRED | RECOMMENDED | NOT REQUIRED] — reason
   ---

3. SENSITIVITY FLAG: Flag any output containing personal data, performance
   evaluations, compensation details, or disciplinary content as SENSITIVE.

4. OPEN QUESTIONS: Every output ends with a numbered list of decisions
   requiring human input before any action is taken.

5. NO AUTOMATED PEOPLE ACTIONS: Agents never send offer letters, rejection
   notices, performance ratings, or any communication to a person.
"""


# ── Notification helpers ──────────────────────────────────────────────────────

def send_sms(message: str) -> bool:
    try:
        import smtplib
        from email.mime.text import MIMEText
        sms_address = (
            os.getenv("HUMAN_PHONE_NUMBER", "").replace("+1", "") + "@txt.att.net"
        )
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
    sms_sent = send_sms(f"[HR-TEAM] {subject}\n{message}")
    send_email(f"[HR-TEAM] {subject}", message)
    if not sms_sent:
        print("⚠️  SMS failed. Email attempted as fallback.")


# ── HR action gate ────────────────────────────────────────────────────────────

def request_human_approval(
    artifact_path: str,
    summary: str,
    action_type: str,
    timeout_hours: int = 48,
) -> bool:
    """
    HR action gate — blocks until human approves or rejects.
    Required before ANY action affecting a person.
    Returns True if approved, False if rejected or timed out.
    """
    import time as _t

    approval_dir = "logs/approvals"
    os.makedirs(approval_dir, exist_ok=True)
    approval_id = f"HR-{uuid.uuid4().hex[:8].upper()}"
    response_file = f"{approval_dir}/{approval_id}.response.json"

    with open(f"{approval_dir}/{approval_id}.json", "w") as f:
        json.dump({
            "approval_id": approval_id,
            "action_type": action_type,
            "artifact_path": artifact_path,
            "summary": summary,
            "requested_at": datetime.utcnow().isoformat(),
            "status": "PENDING",
        }, f, indent=2)

    notify_human(
        subject=f"[HR ACTION GATE — {action_type}] {approval_id}",
        message=(
            f"HR Action Type: {action_type}\n"
            f"Summary: {summary}\n"
            f"Artifact: {artifact_path}\n"
            f"Approval ID: {approval_id}\n\n"
            f"⚠️  No action affecting any person will proceed without your approval.\n\n"
            f"To approve: write to {response_file}:\n"
            f'  {{"decision": "APPROVED"}}\n\n'
            f"To reject:\n"
            f'  {{"decision": "REJECTED", "reason": "your feedback"}}\n\n'
            f"Timeout: {timeout_hours} hours."
        ),
    )

    print(f"\n⏸️  [HR ACTION GATE — {action_type}] {approval_id}")
    print(f"   Artifact: {artifact_path}\n")

    elapsed = 0
    while elapsed < timeout_hours * 3600:
        if os.path.exists(response_file):
            with open(response_file) as f:
                response = json.load(f)
            decision = response.get("decision", "").upper()
            if decision == "APPROVED":
                print(f"✅ HR action approved — {approval_id}")
                return True
            elif decision == "REJECTED":
                print(f"❌ HR action rejected — {approval_id}: {response.get('reason', '')}")
                return False
        _t.sleep(30)
        elapsed += 30

    print(f"⏰ HR approval timed out — {approval_id}. NOT proceeding.")
    return False


# ── HR context helpers ────────────────────────────────────────────────────────

def create_hr_context(hr_name: str, run_mode: str, project_id: str = None) -> dict:
    return {
        "framework": "protean-pursuits-hr",
        "hr_id": f"HR-{uuid.uuid4().hex[:8].upper()}",
        "hr_name": hr_name,
        "run_mode": run_mode.upper(),
        "project_id": project_id,
        "owner": "Protean Pursuits LLC",
        "created_at": datetime.utcnow().isoformat(),
        "status": "INITIATED",
        "artifacts": [],
        "events": [],
    }


def save_context(context: dict) -> str:
    os.makedirs("logs", exist_ok=True)
    path = f"logs/{context['hr_id']}.json"
    with open(path, "w") as f:
        json.dump(context, f, indent=2)
    return path


def log_event(context: dict, event_type: str, detail: str = "") -> None:
    context["events"].append({
        "event_type": event_type,
        "detail": detail,
        "timestamp": datetime.utcnow().isoformat(),
    })
    save_context(context)


def save_artifact(context: dict, name: str, artifact_type: str,
                  content: str, output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = f"{output_dir}/{context['hr_id']}_{artifact_type}_{ts}.md"
    with open(path, "w") as f:
        f.write(content)
    context["artifacts"].append({
        "name": name, "type": artifact_type, "path": path,
        "status": "PENDING_REVIEW",
        "created_at": datetime.utcnow().isoformat(),
    })
    log_event(context, f"{artifact_type}_COMPLETE", path)
    print(f"\n💾 [{artifact_type}] Saved: {path}")
    return path


# ── Agent factory ─────────────────────────────────────────────────────────────

def build_hr_orchestrator() -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/qwen3:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800,
    )
    return Agent(
        role="HR Team Orchestrator",
        goal=(
            "Coordinate the HR Team to produce structured, legally-compliant HR "
            "deliverables — recruiting, onboarding, performance, policy, culture, "
            "and benefits — ensuring no action affecting any person is taken "
            "without explicit human approval."
        ),
        backstory=(
            "You are the Chief People Officer equivalent at Protean Pursuits LLC — "
            "a senior HR leader with 20 years of experience building people functions "
            "for high-growth technology companies across the US and internationally. "
            "You have deep expertise in talent acquisition, performance management, "
            "compensation design, employment law, and organisational culture. "
            "You lead six specialist agents — Recruiting Specialist, Onboarding "
            "Specialist, Performance & Compensation Specialist, Policy & Compliance "
            "Specialist, Culture & Engagement Specialist, and Benefits Specialist. "
            "Two non-negotiable rules: (1) every HR output is held for human "
            "approval before any action affecting a person is taken — no exceptions; "
            "(2) every output involving compensation, performance, disciplinary "
            "matters, or personal data is flagged SENSITIVE. "
            "You are a strategic advisor: you challenge decisions that carry legal "
            "or cultural risk, surface jurisdictional issues proactively, and "
            "recommend external employment counsel when exposure warrants it."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=True,
    )


# ── Runner ────────────────────────────────────────────────────────────────────

def run_hr_orchestrator(context: dict, brief: str = "") -> str:
    """
    Entry point called by hr_flow.py and hr_intake_flow.py.

    Args:
        context: Project context dict (from load_context or stub).
        brief:   Plain-English HR brief (may also live in context["brief"]).

    Returns:
        String output from the HR Team Orchestrator agent.
    """
    resolved_brief = brief or context.get("brief", "")
    if not resolved_brief:
        raise ValueError(
            "run_hr_orchestrator: no brief provided. "
            "Pass via 'brief' argument or context['brief']."
        )

    project = context.get("project", "ad-hoc")
    run_mode = context.get("run_mode", "FULL_CYCLE").upper()
    mode_description = HR_MODES.get(run_mode, "General HR request")

    agent = build_hr_orchestrator()

    task_description = f"""
You are the HR Team Orchestrator for the Protean Pursuits system.

PROJECT: {project}
RUN MODE: {run_mode} — {mode_description}

BRIEF:
{resolved_brief}

CONTEXT:
{context.get("raw", "")}

{HR_INSTRUCTION}

Based on the brief and run mode, engage the relevant specialist agents and
produce the complete HR deliverable.

MANDATORY OUTPUT STRUCTURE:
1. LEGAL COMPLIANCE BLOCK (jurisdiction, statutes considered, external counsel flag)
2. Complete HR deliverable appropriate to the run mode
3. SENSITIVE DATA FLAGS — list any content requiring restricted access
4. OPEN QUESTIONS — numbered list of decisions requiring human input

⚠️  HR ACTION GATE: This output must be approved by the human before any
action is taken on any person's employment, compensation, or status.
"""

    task = Task(
        description=task_description,
        expected_output=(
            "A complete HR deliverable appropriate to the run mode. Must open with "
            "the legal compliance block, flag all sensitive content, and end with "
            "an OPEN QUESTIONS section. No action on any person may be taken "
            "without human approval."
        ),
        agent=agent,
    )

    crew = Crew(agents=[agent], tasks=[task], verbose=True)
    result = crew.kickoff()
    output_str = str(result)

    if project and project != "ad-hoc":
        output_dir = f"output/{project}/hr"
        os.makedirs(output_dir, exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        out_path = f"{output_dir}/orchestrator_{ts}.md"
        with open(out_path, "w") as f:
            f.write(output_str)
        print(f"💾 HR Orchestrator output saved: {out_path}")

    return output_str
