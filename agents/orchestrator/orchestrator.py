"""
agents/orchestrator/orchestrator.py

Protean Pursuits — Top-level Orchestrator Agent

Responsibilities:
- Discovery interview (open-ended project intake)
- Brief-driven intake (PRD / brief provided)
- Auto-generate PRD from discovery output
- Spin up project repo from template
- Assign teams and kick off work via Project Manager
- Blocker escalation to human
- Cross-project memory and brand context

Human-in-the-loop gates:
- PRD approval before any team work begins
- Repo spin-up confirmation
- Blocker escalation (any severity CRITICAL)
"""

import os
import json
import uuid
import shutil
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, LLM

load_dotenv("config/.env")


# ── Notification helpers ──────────────────────────────────────────────────────

def send_sms(message: str) -> bool:
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


def notify_human(subject: str, message: str, prefix: str = "PROTEAN") -> None:
    send_sms(f"[{prefix}] {subject}\n{message}")
    send_email(f"[{prefix}] {subject}", message)


# ── Human-in-the-loop approval gate ──────────────────────────────────────────

def request_human_approval(gate_type: str, artifact_path: str,
                            summary: str, timeout_hours: int = 24) -> bool:
    """
    Pause and notify human for approval. Blocks until response or timeout.
    gate_type: 'PRD' | 'REPO_SPINUP' | 'BLOCKER' | 'POST' | 'EMAIL' | 'VIDEO' | 'DELIVERABLE'
    Returns True if approved, False if rejected or timed out.
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
            f"Gate type: {gate_type}\n"
            f"Summary: {summary}\n"
            f"Artifact: {artifact_path}\n"
            f"Approval ID: {approval_id}\n\n"
            f"To approve: write to {response_file}:\n"
            f'  {{"decision": "APPROVED"}}\n\n'
            f"To reject:\n"
            f'  {{"decision": "REJECTED", "reason": "your reason"}}\n\n'
            f"Timeout: {timeout_hours} hours."
        )
    )

    print(f"\n⏸️  [{gate_type}] Human approval required — {approval_id}")
    print(f"   Waiting for: {response_file}\n")

    elapsed = 0
    timeout = timeout_hours * 3600
    while elapsed < timeout:
        if os.path.exists(response_file):
            with open(response_file) as f:
                response = json.load(f)
            decision = response.get("decision", "").upper()
            if decision == "APPROVED":
                print(f"✅ [{gate_type}] Approved — {approval_id}")
                return True
            elif decision == "REJECTED":
                reason = response.get("reason", "No reason given")
                print(f"❌ [{gate_type}] Rejected — {approval_id}: {reason}")
                return False
        import time as _t
        _t.sleep(30)
        elapsed += 30

    print(f"⏰ [{gate_type}] Timed out — {approval_id}. NOT proceeding.")
    return False


# ── Project context ───────────────────────────────────────────────────────────

def create_project_context(project_name: str, mode: str = "BRIEF") -> dict:
    """
    Initialize a Protean Pursuits project context.
    mode: 'DISCOVERY' | 'BRIEF'
    """
    return {
        "framework": "protean-pursuits",
        "project_id": f"PROJ-{uuid.uuid4().hex[:8].upper()}",
        "project_name": project_name,
        "owner": "Protean Pursuits LLC",
        "mode": mode,
        "created_at": datetime.utcnow().isoformat(),
        "status": "INITIATED",
        "teams_assigned": [],
        "artifacts": [],
        "blockers": [],
        "events": [],
        "budget": {},
        "timeline": {}
    }


def save_context(context: dict) -> str:
    os.makedirs("logs", exist_ok=True)
    path = f"logs/{context['project_id']}.json"
    with open(path, "w") as f:
        json.dump(context, f, indent=2)
    return path


def log_event(context: dict, event_type: str, detail: str = "") -> None:
    context["events"].append({
        "event_type": event_type,
        "detail": detail,
        "timestamp": datetime.utcnow().isoformat()
    })
    save_context(context)


def escalate_blocker(context: dict, blocker_id: str, severity: str,
                     description: str, owner: str) -> None:
    """Log a blocker and notify human if CRITICAL."""
    blocker = {
        "blocker_id": blocker_id,
        "severity": severity,
        "description": description,
        "owner": owner,
        "raised_at": datetime.utcnow().isoformat(),
        "status": "OPEN"
    }
    context["blockers"].append(blocker)
    log_event(context, f"BLOCKER_{severity}", f"{blocker_id}: {description}")

    if severity == "CRITICAL":
        notify_human(
            subject=f"[CRITICAL BLOCKER] {blocker_id} — {context['project_name']}",
            message=(
                f"Project: {context['project_name']} ({context['project_id']})\n"
                f"Blocker: {blocker_id}\n"
                f"Severity: {severity}\n"
                f"Owner: {owner}\n"
                f"Description: {description}\n\n"
                f"This blocker requires your immediate attention. "
                f"Affected work cannot proceed until resolved."
            )
        )


# ── Repo spin-up from template ────────────────────────────────────────────────

TEAM_TEMPLATES = {
    "dev": "templates/dev_team",
    "ds": "templates/ds_team",
    "marketing": "templates/marketing_team",
    "design": "templates/design_team",
    "qa": "templates/qa_team",
    "legal": "templates/legal_team",
    "strategy": "templates/strategy_team",
}


def spinup_project_repo(context: dict, teams: list,
                         target_dir: str) -> dict:
    """
    Copy selected team templates into a new project directory.
    Requires human approval before executing.
    teams: list of team keys e.g. ['dev', 'ds', 'marketing']
    """
    summary = (
        f"Spin up project repo for '{context['project_name']}' "
        f"({context['project_id']}) with teams: {', '.join(teams)}\n"
        f"Target: {target_dir}"
    )

    approved = request_human_approval(
        gate_type="REPO_SPINUP",
        artifact_path=target_dir,
        summary=summary
    )

    if not approved:
        log_event(context, "REPO_SPINUP_REJECTED", target_dir)
        return context

    os.makedirs(target_dir, exist_ok=True)

    for team in teams:
        template_path = TEAM_TEMPLATES.get(team)
        if not template_path or not os.path.exists(template_path):
            print(f"⚠️  Template not found for team: {team}")
            continue
        dest = os.path.join(target_dir, f"{team}-team")
        shutil.copytree(template_path, dest, dirs_exist_ok=True)

        # Inject project_id into all .py files
        for root, _, files in os.walk(dest):
            for fname in files:
                if fname.endswith(".py"):
                    fpath = os.path.join(root, fname)
                    with open(fpath) as f:
                        content = f.read()
                    content = content.replace("PROJ-TEMPLATE", context["project_id"])
                    content = content.replace("PROJECT_NAME_PLACEHOLDER", context["project_name"])
                    with open(fpath, "w") as f:
                        f.write(content)

        print(f"✅ Spun up {team}-team at {dest}")

    context["teams_assigned"] = teams
    context["status"] = "REPO_SPUNUP"
    log_event(context, "REPO_SPUNUP", f"Teams: {teams} → {target_dir}")
    save_context(context)
    return context


# ── Orchestrator agent ────────────────────────────────────────────────────────

def build_orchestrator() -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/qwen3:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    return Agent(
        role="Protean Pursuits Orchestrator",
        goal=(
            "Take any new project from first contact to active execution — "
            "running discovery interviews or ingesting briefs, generating PRDs, "
            "spinning up project repos from templates, assigning teams via the "
            "Project Manager, and escalating blockers to the human when needed."
        ),
        backstory=(
            "You are the founding intelligence of Protean Pursuits LLC — a Michigan-based "
            "LLC that builds software products, data science platforms, and marketing "
            "programmes across multiple domains. You operate across every project the LLC "
            "undertakes and are responsible for the quality and coherence of everything "
            "that ships under the Protean Pursuits name. "
            "You have two modes of operation. In Discovery Mode you run a structured "
            "intake interview with the human — asking about the problem to solve, the "
            "target audience, the success criteria, the constraints, and the desired "
            "team composition. You synthesise the answers into a draft PRD and submit "
            "it for human approval before any work begins. In Brief Mode you are handed "
            "a PRD or brief and immediately classify the work, identify the required "
            "teams, generate a project context, and hand off to the Project Manager. "
            "You know the full template library: Dev Team, Data Science Team, Marketing "
            "Team, Design Team, QA Team, Legal/Compliance Team, and Strategy Team. You "
            "select only the teams the project genuinely needs. You never spin up a "
            "team without human approval. "
            "You hold the master view across all active projects. You know what every "
            "team lead is working on, what blockers are open, and whether the portfolio "
            "is on track. You produce a Weekly Portfolio Report every Monday. "
            "You are the escalation path of last resort. When a blocker is CRITICAL "
            "and cannot be resolved within the team, you notify the human directly "
            "with full context and a recommended resolution path. "
            "You operate under Protean Pursuits LLC values: quality over speed, "
            "transparency over comfort, and human judgment over automation for "
            "irreversible decisions."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=True
    )
