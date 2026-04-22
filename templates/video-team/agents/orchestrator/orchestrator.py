"""
agents/orchestrator/orchestrator.py

Protean Pursuits — Video Team Orchestrator

Responsibilities:
- Load project context and video brief
- Inject per-project avatar config from context
- Sequence agents based on run mode
- Fire three HITL gates: VIDEO_TOOL_SELECTION, SCRIPT_REVIEW, VIDEO_FINAL
- Save and return updated context with all artifacts

Run modes:
  BRIEF_ONLY  — tool evaluation + script + visual + audio (no API calls)
  SHORT_FORM  — full pipeline, <60s social (TikTok, Reels, Shorts)
  LONG_FORM   — full pipeline, 2–10min (YouTube, website)
  AVATAR      — full pipeline, avatar/spokesperson foregrounded
  DEMO        — script + audio + production only (screen recording input)
  EXPLAINER   — full pipeline, animated explainer / motion graphics
  VOICEOVER   — script + audio + production (no visual generation)
  FULL        — all modes sequenced as a campaign package
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))

import os
import json
import uuid
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from crewai import Agent, LLM

load_dotenv("config/.env")


# ── Notifications ─────────────────────────────────────────────────────────────

def _send_sms(message: str) -> bool:
    try:
        sms_address = (
            os.getenv("HUMAN_PHONE_NUMBER", "").replace("+1", "") + "@txt.att.net"
        )
        msg = MIMEText(message[:160])
        msg["From"] = os.getenv("OUTLOOK_ADDRESS")
        msg["To"] = sms_address
        msg["Subject"] = ""
        with smtplib.SMTP("smtp-mail.outlook.com", 587) as s:
            s.starttls()
            s.login(os.getenv("OUTLOOK_ADDRESS"), os.getenv("OUTLOOK_PASSWORD"))
            s.send_message(msg)
        return True
    except Exception as e:
        print(f"⚠️  SMS failed: {e}")
        return False


def _send_email(subject: str, body: str) -> bool:
    try:
        msg = MIMEMultipart()
        msg["From"] = os.getenv("OUTLOOK_ADDRESS")
        msg["To"] = os.getenv("HUMAN_EMAIL")
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP("smtp-mail.outlook.com", 587) as s:
            s.starttls()
            s.login(os.getenv("OUTLOOK_ADDRESS"), os.getenv("OUTLOOK_PASSWORD"))
            s.send_message(msg)
        return True
    except Exception as e:
        print(f"⚠️  Email failed: {e}")
        return False


def notify_human(subject: str, message: str) -> None:
    _send_sms(f"[VIDEO] {subject}\n{message}")
    _send_email(f"[VIDEO] {subject}", message)


# ── HITL approval gate ────────────────────────────────────────────────────────

def request_human_approval(
    gate_type: str,
    artifact_path: str,
    summary: str,
    timeout_hours: int = 24,
) -> bool:
    """
    Write an approval request, notify human, poll for response.
    gate_type: VIDEO_TOOL_SELECTION | SCRIPT_REVIEW | VIDEO_FINAL
    Returns True if approved, False if rejected or timed out.
    """
    import time

    approval_dir = "logs/approvals"
    os.makedirs(approval_dir, exist_ok=True)
    approval_id = f"APPROVAL-{uuid.uuid4().hex[:8].upper()}"
    request_file = f"{approval_dir}/{approval_id}.json"
    response_file = f"{approval_dir}/{approval_id}.response.json"

    request = {
        "approval_id": approval_id,
        "gate_type": gate_type,
        "artifact_path": artifact_path,
        "summary": summary,
        "requested_at": datetime.utcnow().isoformat(),
        "status": "PENDING",
    }
    with open(request_file, "w") as f:
        json.dump(request, f, indent=2, default=str)

    notify_human(
        subject=f"[APPROVAL REQUIRED] {gate_type} — {approval_id}",
        message=(
            f"Gate: {gate_type}\n"
            f"Summary: {summary}\n"
            f"Artifact: {artifact_path}\n"
            f"Approval ID: {approval_id}\n\n"
            f"To approve, write to {response_file}:\n"
            f'  {{"decision": "APPROVED"}}\n\n'
            f"To reject:\n"
            f'  {{"decision": "REJECTED", "reason": "your reason"}}\n\n'
            f"Timeout: {timeout_hours} hours."
        ),
    )

    print(f"\n⏸️  [{gate_type}] Approval required — {approval_id}")
    print(f"   Waiting for: {response_file}\n")

    elapsed = 0
    timeout = timeout_hours * 3600
    while elapsed < timeout:
        if os.path.exists(response_file):
            with open(response_file) as f:
                resp = json.load(f)
            decision = resp.get("decision", "").upper()
            if decision == "APPROVED":
                print(f"✅ [{gate_type}] Approved — {approval_id}")
                return True
            elif decision == "REJECTED":
                reason = resp.get("reason", "No reason given")
                print(f"❌ [{gate_type}] Rejected — {approval_id}: {reason}")
                return False
        time.sleep(30)
        elapsed += 30

    print(f"⏰ [{gate_type}] Timed out — {approval_id}. NOT proceeding.")
    return False


# ── Context helpers ───────────────────────────────────────────────────────────

def create_video_context(
    project_name: str,
    run_mode: str,
    project_id: str = None,
    avatar_config: dict = None,
) -> dict:
    """
    Initialise a video-team project context.
    avatar_config: per-project avatar definition (optional).
      {
        "avatar_id": str,          # HeyGen avatar ID or equivalent
        "name": str,               # display name for the spokesperson
        "style": str,              # "professional" | "casual" | "custom"
        "voice_id": str,           # TTS voice ID
        "language": str,           # e.g. "en-US"
        "custom_notes": str        # any extra direction
      }
    """
    return {
        "framework": "protean-pursuits",
        "team": "video-team",
        "video_id": f"VID-{uuid.uuid4().hex[:8].upper()}",
        "project_id": project_id or f"PROJ-{uuid.uuid4().hex[:8].upper()}",
        "project_name": project_name,
        "run_mode": run_mode.upper(),
        "created_at": datetime.utcnow().isoformat(),
        "status": "INITIATED",
        "tool_selection": {},        # populated after VIDEO_TOOL_SELECTION gate
        "avatar_config": avatar_config or {},
        "artifacts": [],
        "events": [],
    }


def save_context(context: dict) -> str:
    os.makedirs("logs", exist_ok=True)
    path = f"logs/{context['video_id']}.json"
    with open(path, "w") as f:
        json.dump(context, f, indent=2, default=str)
    return path


def log_event(context: dict, event_type: str, detail: str = "") -> None:
    context["events"].append({
        "event_type": event_type,
        "detail": detail,
        "timestamp": datetime.utcnow().isoformat(),
    })
    save_context(context)


def save_artifact(
    context: dict,
    name: str,
    artifact_type: str,
    content: str,
    output_dir: str,
) -> str:
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = f"{output_dir}/{context['video_id']}_{artifact_type}_{ts}.md"
    with open(path, "w") as f:
        f.write(content)
    context["artifacts"].append({
        "name": name,
        "type": artifact_type,
        "path": path,
        "created_at": datetime.utcnow().isoformat(),
        "agent": artifact_type,
    })
    save_context(context)
    print(f"💾 {artifact_type} saved: {path}")
    return path


# ── Output standards injected into every task ────────────────────────────────

VIDEO_STANDARDS = """
OUTPUT STANDARDS (apply to all video team outputs):
- Brand-agnostic: use PROJECT_NAME_PLACEHOLDER for all brand references. Actual
  brand voice, colors, and tone come from the project brief — never assume.
- Platform-specific: tailor every output to the target platform's specs,
  algorithm behavior, and audience expectations.
- Compliance first: no guaranteed outcomes, no misleading claims, no copyright
  violations. Flag any risk in an OPEN ISSUES section.
- Handoff-ready: every brief must be complete enough for an API or human
  executor to proceed without follow-up questions.
- Open questions: end every output with a numbered list of decisions or
  assets still required from the human before execution.
"""


# ── Orchestrator agent ────────────────────────────────────────────────────────

def build_video_orchestrator() -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/qwen3:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800,
    )
    return Agent(
        role="Video Team Orchestrator",
        goal=(
            "Coordinate the Video Team to produce complete, platform-optimised "
            "video production packages — from tool selection and scripting through "
            "API-generated renders — for any Protean Pursuits project."
        ),
        backstory=(
            "You are the Executive Video Producer at Protean Pursuits LLC — a "
            "creative and technical leader with 15 years of experience producing "
            "AI-assisted video content for technology, data, and analytics brands. "
            "You lead eight specialist agents: Tool Intelligence Analyst, Script & "
            "Narrative Writer, Visual Director, Avatar & Spokesperson Producer, "
            "Audio & Music Producer, API Production Engineer, and Compliance & "
            "Brand Reviewer. "
            "You sequence them intelligently based on the run mode and project brief. "
            "You never allow an API call to run before a human has approved the tool "
            "selection and the script. You never mark a video as publishable without "
            "a human final approval. "
            "You are platform-fluent: you know the grammar of TikTok, Reels, Shorts, "
            "YouTube long-form, website hero video, product demos, explainers, and "
            "avatar-driven spokesperson content. You adapt the crew's work to each "
            "format's requirements without the human needing to specify every detail. "
            "You synthesise all specialist outputs into a coherent Video Package (VP) "
            "cover document at the end of every run, indexing all artifacts and "
            "flagging any open items before human review."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=True,
    )

import os
from crewai import Crew, Task

def run_video_orchestrator(context: dict, brief: str = "") -> str:
    """
    Entry point called by video_intake_flow.py.

    Builds the Video Team Orchestrator agent, issues a Task derived from
    the project context and brief, runs a single-agent Crew, saves output
    to output/<project>/video/, and returns the result string.

    Three HITL gates fire inside the pipeline:
      VIDEO_TOOL_SELECTION → SCRIPT_REVIEW → VIDEO_FINAL
    Nothing publishes without all three gates passing.

    Args:
        context: Project context dict (from load_context or stub).
        brief:   Plain-English video brief (may also live in context["brief"]).

    Returns:
        String output from the Video Team Orchestrator agent.
    """
    # ── Resolve brief ──────────────────────────────────────────────────────────
    resolved_brief = brief or context.get("brief", "")
    if not resolved_brief:
        raise ValueError(
            "run_video_orchestrator: no brief provided. "
            "Pass via 'brief' argument or context['brief']."
        )

    project = context.get("project", "ad-hoc")

    # ── Build agent ────────────────────────────────────────────────────────────
    agent = build_video_orchestrator()

    # ── Build task ─────────────────────────────────────────────────────────────
    task_description = f"""
You are the Video Team Orchestrator for the Protean Pursuits system.

PROJECT: {project}

BRIEF:
{resolved_brief}

CONTEXT:
{context.get("raw", "")}

{VIDEO_STANDARDS}

Based on the brief above, select the appropriate run mode (BRIEF_ONLY,
SHORT_FORM, LONG_FORM, AVATAR, DEMO, EXPLAINER, VOICEOVER, or FULL),
engage the relevant specialist agents, and produce the complete video
production package.

MANDATORY GATE SEQUENCE — nothing proceeds without each approval:
  1. VIDEO_TOOL_SELECTION gate — tool evaluation report, human must approve
     before any creative work or API calls begin
  2. SCRIPT_REVIEW gate — script approved before production work begins
  3. VIDEO_FINAL gate — compliance review approved before any publish action

MANDATORY OUTPUT STRUCTURE:
1. Tool Selection Brief (platform, tools, rationale)
2. Script / Narrative
3. Visual Direction Brief
4. Audio & Music Brief
5. Avatar/Spokesperson notes (if applicable)
6. Production API call spec (if applicable)
7. Compliance & Brand Review
8. Video Package (VP) cover document indexing all artifacts
9. OPEN ITEMS — decisions or assets still required from the human

Do not invoke any external API without explicit human approval at
VIDEO_TOOL_SELECTION and SCRIPT_REVIEW gates.
"""

    task = Task(
        description=task_description,
        expected_output=(
            "A complete video production package appropriate to the selected run mode "
            "(BRIEF_ONLY through FULL). Must include tool selection brief, script, "
            "visual direction, audio brief, compliance review, and a VP cover document "
            "indexing all artifacts. Must end with OPEN ITEMS section."
        ),
        agent=agent,
    )

    # ── Run crew ───────────────────────────────────────────────────────────────
    crew = Crew(agents=[agent], tasks=[task], verbose=True)
    result = crew.kickoff()
    output_str = str(result)

    # ── Persist output ─────────────────────────────────────────────────────────
    if project and project != "ad-hoc":
        from datetime import datetime
        output_dir = f"output/{project}/video"
        os.makedirs(output_dir, exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        out_path = f"{output_dir}/orchestrator_{ts}.md"
        with open(out_path, "w") as f:
            f.write(output_str)
        print(f"💾 Video Orchestrator output saved: {out_path}")

    return output_str

