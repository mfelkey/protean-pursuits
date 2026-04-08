"""
teams/video-team/agents/orchestrator/orchestrator.py

Protean Pursuits — Video Team Orchestrator

HITL gates:
  VIDEO_TOOL_SELECTION  — after Tool Analyst, before any creative work
  SCRIPT_REVIEW         — after Script Writer, before API calls
  VIDEO_FINAL           — after Compliance Reviewer, before any publish action

Run modes: BRIEF_ONLY | SHORT_FORM | LONG_FORM | AVATAR | DEMO | EXPLAINER | VOICEOVER | FULL
"""

import os
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, LLM

load_dotenv("config/.env")


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
    send_sms(f"[VIDEO-TEAM] {subject}\n{message}")
    send_email(f"[VIDEO-TEAM] {subject}", message)


# ── HITL approval gate ────────────────────────────────────────────────────────

def request_human_approval(gate_type: str, artifact_path: str,
                            summary: str, timeout_hours: int = 48) -> bool:
    """
    HITL gates: VIDEO_TOOL_SELECTION | SCRIPT_REVIEW | VIDEO_FINAL
    Returns True if approved, False if rejected or timed out.
    """
    import time as _t

    approval_dir = "logs/approvals"
    os.makedirs(approval_dir, exist_ok=True)
    approval_id = f"VIDEO-{uuid.uuid4().hex[:8].upper()}"
    response_file = f"{approval_dir}/{approval_id}.response.json"

    with open(f"{approval_dir}/{approval_id}.json", "w") as f:
        json.dump({
            "approval_id": approval_id,
            "gate_type": gate_type,
            "artifact_path": artifact_path,
            "summary": summary,
            "requested_at": datetime.utcnow().isoformat(),
            "status": "PENDING"
        }, f, indent=2)

    notify_human(
        subject=f"[{gate_type}] Video approval required — {approval_id}",
        message=(
            f"Gate: {gate_type}\n"
            f"Summary: {summary}\n"
            f"Artifact: {artifact_path}\n\n"
            f"Approve: write to {response_file}:\n"
            f'  {{"decision": "APPROVED"}}\n\n'
            f"Reject: {{'decision': 'REJECTED', 'reason': '...'}}\n"
            f"Timeout: {timeout_hours}h"
        )
    )
    print(f"\n⏸️  [{gate_type}] Video approval — {approval_id}")
    print(f"   Artifact: {artifact_path}")

    elapsed = 0
    while elapsed < timeout_hours * 3600:
        if os.path.exists(response_file):
            with open(response_file) as f:
                resp = json.load(f)
            decision = resp.get("decision", "").upper()
            if decision == "APPROVED":
                print(f"✅ [{gate_type}] Approved — {approval_id}")
                return True
            elif decision == "REJECTED":
                print(f"❌ [{gate_type}] Rejected — {approval_id}: {resp.get('reason', '')}")
                return False
        _t.sleep(30)
        elapsed += 30

    print(f"⏰ [{gate_type}] Timed out — {approval_id}.")
    return False


# ── Video context ─────────────────────────────────────────────────────────────

def create_video_context(project_name: str, run_mode: str,
                          project_id: str = None) -> dict:
    return {
        "framework": "protean-pursuits-video",
        "video_id": f"VID-{uuid.uuid4().hex[:8].upper()}",
        "project_name": project_name,
        "run_mode": run_mode,
        "project_id": project_id,
        "created_at": datetime.utcnow().isoformat(),
        "status": "INITIATED",
        "artifacts": [],
        "events": []
    }


def save_context(context: dict) -> str:
    os.makedirs("logs", exist_ok=True)
    path = f"logs/{context['video_id']}.json"
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


# ── Video Orchestrator agent ──────────────────────────────────────────────────

def build_video_orchestrator() -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/qwen3:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800,
    )

    return Agent(
        role="Video Team Orchestrator",
        goal=(
            "Coordinate the Video Team to produce complete video production packages "
            "— scripts, visual direction, audio, avatar, tool selection, and "
            "compliance — for any Protean Pursuits project, with HITL gates at "
            "tool selection, script review, and final compliance sign-off."
        ),
        backstory=(
            "You are the Video Production Director at Protean Pursuits LLC — a "
            "senior creative director with 15 years of experience producing video "
            "content across social, long-form, explainer, avatar, and demo formats. "
            "You coordinate eight specialist agents: Tool Analyst, Script Writer, "
            "Visual Director, Audio Producer, Avatar Producer, Compliance Reviewer, "
            "and API Engineer. "
            "You enforce three mandatory HITL gates: VIDEO_TOOL_SELECTION (after "
            "Tool Analyst, before any creative work begins), SCRIPT_REVIEW (after "
            "Script Writer, before any API calls are made), and VIDEO_FINAL (after "
            "Compliance Reviewer, before any publish action). Nothing publishes "
            "without passing all three gates. "
            "You are tool-agnostic in your planning — you evaluate tools based on "
            "the project requirements and recommend the best fit, never defaulting "
            "to a specific vendor. "
            "Every output ends with CROSS-TEAM FLAGS and OPEN QUESTIONS."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=True,
    )


# ── Run function ──────────────────────────────────────────────────────────────

def run_video_orchestrator(brief: str, context: dict) -> str:
    """
    Instantiate the Video Team Orchestrator, run it against the brief, return output.

    Called by flows/video_intake_flow.py via:
        run_video_orchestrator = _import_orchestrator()
        result = run_video_orchestrator(brief=brief_text, context=project_context)
    """
    from crewai import Crew, Task

    agent = build_video_orchestrator()
    context_block = (
        context.get("raw", "")
        or (json.dumps(context, indent=2) if context else "No context provided.")
    )

    task = Task(
        description=(
            f"Project brief:\n{brief}\n\n"
            f"Project context:\n{context_block}\n\n"
            "Coordinate the Video Team to produce a complete video production package "
            "for this project. Select the appropriate run mode based on the brief "
            "(BRIEF_ONLY / SHORT_FORM / LONG_FORM / AVATAR / DEMO / EXPLAINER / "
            "VOICEOVER / FULL). Enforce HITL gates at VIDEO_TOOL_SELECTION, "
            "SCRIPT_REVIEW, and VIDEO_FINAL. Nothing publishes without all three "
            "gates passing. End with CROSS-TEAM FLAGS and OPEN QUESTIONS."
        ),
        expected_output=(
            "Complete Video production plan including mode selection, tool "
            "recommendations, script outline, visual direction, and compliance "
            "checklist. No placeholders. Ends with CROSS-TEAM FLAGS and OPEN QUESTIONS."
        ),
        agent=agent,
    )

    crew = Crew(agents=[agent], tasks=[task], verbose=True)
    result = crew.kickoff()
    return str(result)
