"""
teams/finance-team/agents/orchestrator/orchestrator.py

Protean Pursuits — Finance Team Orchestrator

Finance Group is a dev-team sub-crew — specialist agents live at
templates/dev-team/agents/finance/. This orchestrator imports from
that location and provides the run_finance_orchestrator() entry point
for flows/finance_intake_flow.py.

Advisory only — Finance Group NEVER auto-blocks the pipeline.
CP-4.5 HITL gate fires on FSP completion.

Auto-skip rules (enforced by Finance Orchestrator):
  BPS (Billing Architect)  — skipped if no billing language in PRD
  PRI (Pricing Specialist) — skipped for internal tool projects

Every Finance output opens with FINANCE RATING: 🟢/🟡/🔴
and ends with OPEN QUESTIONS.
"""

import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from crewai import Agent, LLM

load_dotenv("config/.env")

# Ensure templates/dev-team is on path for finance agent imports
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
import sys
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


# ── Notification helpers ──────────────────────────────────────────────────────

def send_pushover(subject: str, message: str, priority: int = 1) -> bool:
    """Send Pushover push notification."""
    import urllib.request, urllib.parse, json
    user_key  = os.getenv("PUSHOVER_USER_KEY", "")
    api_token = os.getenv("PUSHOVER_API_TOKEN", "")
    if not user_key or not api_token:
        print("⚠️  Pushover credentials not set")
        return False
    try:
        data = urllib.parse.urlencode({
            "token": api_token, "user": user_key,
            "title": subject[:250], "message": message[:1024],
            "priority": priority,
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://api.pushover.net/1/messages.json",
            data=data, method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            if result.get("status") == 1:
                print(f"📱 Pushover sent: {subject[:60]}")
                return True
            print(f"⚠️  Pushover error: {result}")
            return False
    except Exception as e:
        print(f"⚠️  Pushover failed: {e}")
        return False


def send_sms(message: str) -> bool:
    return send_pushover("Notification", message, priority=1)


def send_email(subject: str, body: str) -> bool:
    return send_pushover(subject, body, priority=0)


def notify_human(subject: str, message: str) -> None:
    send_sms(f"[FINANCE-TEAM] {subject}\n{message}")
    send_email(f"[FINANCE-TEAM] {subject}", message)


# ── CP-4.5 HITL gate ─────────────────────────────────────────────────────────

def request_human_approval(artifact_path: str, summary: str,
                            timeout_hours: int = 48) -> bool:
    """
    CP-4.5 gate — fires on FSP completion.
    Advisory only — Finance Group never auto-blocks the pipeline.
    Returns True if approved, False if rejected or timed out.
    """
    import time as _t

    approval_dir = "logs/approvals"
    os.makedirs(approval_dir, exist_ok=True)
    approval_id = f"CP45-{uuid.uuid4().hex[:8].upper()}"
    response_file = f"{approval_dir}/{approval_id}.response.json"

    with open(f"{approval_dir}/{approval_id}.json", "w") as f:
        json.dump({
            "approval_id": approval_id,
            "gate": "CP-4.5",
            "artifact_path": artifact_path,
            "summary": summary,
            "requested_at": datetime.utcnow().isoformat(),
            "status": "PENDING"
        }, f, indent=2)

    notify_human(
        subject=f"[CP-4.5 FINANCE REVIEW] {approval_id}",
        message=(
            f"Finance Summary Package (FSP) is ready for review.\n\n"
            f"Summary: {summary}\n"
            f"FSP: {artifact_path}\n\n"
            f"Advisory only — pipeline is not blocked. Review at your convenience.\n\n"
            f"Approve: write to {response_file}:\n"
            f'  {{"decision": "APPROVED"}}\n\n'
            f"Reject with feedback: {{'decision': 'REJECTED', 'reason': '...'}}\n"
            f"Timeout: {timeout_hours}h"
        )
    )
    print(f"\n⏸️  [CP-4.5] Finance review gate — {approval_id}")
    print(f"   FSP: {artifact_path}")

    elapsed = 0
    while elapsed < timeout_hours * 3600:
        if os.path.exists(response_file):
            with open(response_file) as f:
                resp = json.load(f)
            decision = resp.get("decision", "").upper()
            if decision == "APPROVED":
                print(f"✅ CP-4.5 approved — {approval_id}")
                return True
            elif decision == "REJECTED":
                print(f"❌ CP-4.5 rejected — {approval_id}: {resp.get('reason', '')}")
                return False
        _t.sleep(30)
        elapsed += 30

    print(f"⏰ CP-4.5 timed out — {approval_id}.")
    return False


# ── Finance context ───────────────────────────────────────────────────────────

def create_finance_context(project_name: str, run_mode: str,
                            project_id: str = None) -> dict:
    return {
        "framework": "protean-pursuits-finance",
        "finance_id": f"FIN-{uuid.uuid4().hex[:8].upper()}",
        "project_name": project_name,
        "run_mode": run_mode,
        "project_id": project_id,
        "created_at": datetime.utcnow().isoformat(),
        "status": "INITIATED",
        "finance_rating": None,
        "artifacts": [],
        "events": []
    }


def save_context(context: dict) -> str:
    os.makedirs("logs", exist_ok=True)
    path = f"logs/{context['finance_id']}.json"
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


# ── Finance Orchestrator agent ────────────────────────────────────────────────

def build_finance_orchestrator() -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/qwen3:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800,
    )

    return Agent(
        role="Finance Team Orchestrator",
        goal=(
            "Coordinate the Finance Group to produce complete financial analysis "
            "packages — cost, ROI, infrastructure, billing, pricing, statements, "
            "and strategic corporate finance — synthesised into a Finance Summary "
            "Package (FSP) with CP-4.5 HITL gate on completion."
        ),
        backstory=(
            "You are the Chief Financial Officer equivalent at Protean Pursuits LLC — "
            "a senior finance professional with 20 years of experience advising "
            "technology companies on financial planning, unit economics, and "
            "strategic corporate finance. "
            "You coordinate seven specialist agents: Cost Analyst, ROI Analyst, "
            "Infrastructure Finance Modeler, Billing Architect, Pricing Specialist, "
            "Financial Statements Modeler, and Strategic Corporate Finance Specialist. "
            "You apply two auto-skip rules: (1) Billing Architect is skipped if "
            "there is no billing language in the PRD; (2) Pricing Specialist is "
            "skipped for internal tool projects. "
            "You are advisory only — you never auto-block the pipeline. Your role "
            "is to give the human the financial picture they need to make informed "
            "decisions. Every output opens with FINANCE RATING: 🟢/🟡/🔴 and ends "
            "with OPEN QUESTIONS. On FSP completion you fire the CP-4.5 HITL gate."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=True,
    )


# ── Run function ──────────────────────────────────────────────────────────────

def run_finance_orchestrator(brief: str, context: dict) -> str:
    """
    Instantiate the Finance Team Orchestrator, run it against the brief, return output.

    Called by flows/finance_intake_flow.py via:
        run_finance_orchestrator = _import_orchestrator()
        result = run_finance_orchestrator(brief=brief_text, context=project_context)
    """
    from crewai import Crew, Task

    agent = build_finance_orchestrator()
    context_block = (
        context.get("raw", "")
        or (json.dumps(context, indent=2) if context else "No context provided.")
    )

    task = Task(
        description=(
            f"Project brief:\n{brief}\n\n"
            f"Project context:\n{context_block}\n\n"
            "Coordinate the Finance Group to produce a complete financial analysis "
            "package for this project. Sequence Cost Analyst, ROI Analyst, "
            "Infrastructure Finance Modeler, Financial Statements Modeler, and "
            "Strategic Corporate Finance Specialist. Apply auto-skip rules: skip "
            "Billing Architect if no billing language in the brief; skip Pricing "
            "Specialist if this is an internal tool project. "
            "Synthesise all outputs into a Finance Summary Package (FSP). "
            "Advisory only — do not block the pipeline. "
            "Every output opens with FINANCE RATING: 🟢/🟡/🔴. "
            "End with OPEN QUESTIONS."
        ),
        expected_output=(
            "Complete Finance Summary Package (FSP). Opens with FINANCE RATING: "
            "🟢/🟡/🔴. Covers cost, ROI, infrastructure, and strategic finance. "
            "No placeholders. Ends with OPEN QUESTIONS."
        ),
        agent=agent,
    )

    crew = Crew(agents=[agent], tasks=[task], verbose=True)
    result = crew.kickoff()
    return str(result)
