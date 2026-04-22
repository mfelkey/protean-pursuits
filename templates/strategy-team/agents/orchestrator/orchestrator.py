"""
agents/orchestrator/orchestrator.py

Protean Pursuits — Strategy Team Orchestrator

Responsibilities:
- Accept strategy requests (project-specific or company-level)
- Route to appropriate agents based on run mode
- Enforce confidence-level tagging on all outputs
- Submit completed strategy packages to Protean Pursuits Orchestrator
  for human review before any implementation
- Track strategy versioning (company baseline vs project overrides)

Run modes:
- BRIEF       — on-demand, single agent
- FULL_REPORT — all agents, sequential, full strategy package
- COMPETITIVE — recurring competitive intelligence update
- OKR_CYCLE   — quarterly OKR planning cycle

Human-in-the-loop: ALL outputs require human review before
forwarding to Protean Pursuits Orchestrator for implementation.

Confidence levels (required on every recommendation):
- HIGH   — strong evidence, clear precedent, low uncertainty
- MEDIUM — reasonable evidence, some assumptions, moderate uncertainty
- LOW    — limited evidence, significant assumptions, high uncertainty
"""

import os
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, LLM

load_dotenv("config/.env")


# ── Confidence level constants ────────────────────────────────────────────────

CONFIDENCE_HIGH   = "HIGH"
CONFIDENCE_MEDIUM = "MEDIUM"
CONFIDENCE_LOW    = "LOW"

CONFIDENCE_DEFINITIONS = {
    "HIGH":   "Strong evidence, clear precedent, low uncertainty. Recommend proceeding.",
    "MEDIUM": "Reasonable evidence, some assumptions, moderate uncertainty. Recommend with caveats.",
    "LOW":    "Limited evidence, significant assumptions, high uncertainty. Treat as hypothesis.",
}

CONFIDENCE_INSTRUCTION = """
CONFIDENCE LEVEL REQUIREMENT — MANDATORY FOR ALL RECOMMENDATIONS:
Every recommendation, finding, or strategic assertion must be tagged with a
confidence level using this exact format at the end of the item:
  [CONFIDENCE: HIGH | Supporting evidence: ...]
  [CONFIDENCE: MEDIUM | Key assumption: ...]
  [CONFIDENCE: LOW | Primary uncertainty: ...]

Definitions:
- HIGH:   Strong evidence, clear market precedent, low uncertainty
- MEDIUM: Reasonable evidence, some assumptions, moderate uncertainty
- LOW:    Limited evidence, significant assumptions, high uncertainty

Never omit confidence tags. Every recommendation without one is incomplete.
"""


# ── Scope constants ───────────────────────────────────────────────────────────

SCOPE_COMPANY = "COMPANY"
SCOPE_PROJECT = "PROJECT"


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


def notify_human(subject: str, message: str) -> None:
    send_sms(f"[STRATEGY-TEAM] {subject}\n{message}")
    send_email(f"[STRATEGY-TEAM] {subject}", message)


# ── Human-in-the-loop approval gate ──────────────────────────────────────────

def request_human_review(artifact_path: str, summary: str,
                          run_mode: str, timeout_hours: int = 48) -> bool:
    """
    All strategy outputs require human review before forwarding to
    the Protean Pursuits Orchestrator for implementation.
    Returns True if approved, False if rejected or timed out.
    """
    import time

    approval_dir = "logs/approvals"
    os.makedirs(approval_dir, exist_ok=True)
    review_id = f"REVIEW-{uuid.uuid4().hex[:8].upper()}"
    review_file = f"{approval_dir}/{review_id}.json"
    response_file = f"{approval_dir}/{review_id}.response.json"

    review_request = {
        "review_id": review_id,
        "run_mode": run_mode,
        "artifact_path": artifact_path,
        "summary": summary,
        "requested_at": datetime.utcnow().isoformat(),
        "status": "PENDING"
    }
    with open(review_file, "w") as f:
        json.dump(review_request, f, indent=2, default=str)

    notify_human(
        subject=f"[STRATEGY REVIEW] {run_mode} — {review_id}",
        message=(
            f"Mode: {run_mode}\n"
            f"Summary: {summary}\n"
            f"Artifact: {artifact_path}\n"
            f"Review ID: {review_id}\n\n"
            f"Review this strategy output before it is forwarded to the\n"
            f"Protean Pursuits Orchestrator for implementation.\n\n"
            f"To approve: write to {response_file}:\n"
            f'  {{"decision": "APPROVED"}}\n\n'
            f"To reject with feedback:\n"
            f'  {{"decision": "REJECTED", "reason": "your feedback"}}\n\n'
            f"Timeout: {timeout_hours} hours."
        )
    )

    print(f"\n⏸️  [STRATEGY REVIEW] {run_mode} — {review_id}")
    print(f"   Artifact: {artifact_path}")
    print(f"   Waiting for human review...\n")

    elapsed = 0
    timeout = timeout_hours * 3600
    while elapsed < timeout:
        if os.path.exists(response_file):
            with open(response_file) as f:
                response = json.load(f)
            decision = response.get("decision", "").upper()
            if decision == "APPROVED":
                print(f"✅ Strategy output approved — {review_id}")
                return True
            elif decision == "REJECTED":
                reason = response.get("reason", "No reason given")
                print(f"❌ Strategy output rejected — {review_id}: {reason}")
                return False
        import time as _t
        _t.sleep(30)
        elapsed += 30

    print(f"⏰ Review timed out — {review_id}. NOT forwarding to Orchestrator.")
    return False


# ── Strategy context ──────────────────────────────────────────────────────────

def create_strategy_context(name: str, scope: str,
                             project_id: str = None) -> dict:
    """
    scope: 'COMPANY' | 'PROJECT'
    project_id: required if scope is PROJECT
    """
    return {
        "framework": "protean-pursuits-strategy",
        "strategy_id": f"STRAT-{uuid.uuid4().hex[:8].upper()}",
        "name": name,
        "scope": scope,
        "project_id": project_id,
        "owner": "Protean Pursuits LLC",
        "created_at": datetime.utcnow().isoformat(),
        "status": "INITIATED",
        "run_mode": None,
        "artifacts": [],
        "events": [],
        "confidence_summary": {}
    }


def save_context(context: dict) -> str:
    os.makedirs("logs", exist_ok=True)
    path = f"logs/{context['strategy_id']}.json"
    with open(path, "w") as f:
        json.dump(context, f, indent=2, default=str)
    return path


def log_event(context: dict, event_type: str, detail: str = "") -> None:
    context["events"].append({
        "event_type": event_type,
        "detail": detail,
        "timestamp": datetime.utcnow().isoformat()
    })
    save_context(context)


def save_artifact(context: dict, name: str, artifact_type: str,
                  content: str, output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = f"{output_dir}/{context['strategy_id']}_{artifact_type}_{timestamp}.md"
    with open(path, "w") as f:
        f.write(content)
    context["artifacts"].append({
        "name": name,
        "type": artifact_type,
        "path": path,
        "scope": context["scope"],
        "project_id": context.get("project_id"),
        "status": "PENDING_REVIEW",
        "created_at": datetime.utcnow().isoformat()
    })
    log_event(context, f"{artifact_type}_COMPLETE", path)
    print(f"\n💾 [{artifact_type}] Saved: {path}")
    return path


# ── Strategy Orchestrator agent ───────────────────────────────────────────────

def build_strategy_orchestrator() -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/qwen3:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    return Agent(
        role="Strategy Team Orchestrator",
        goal=(
            "Coordinate the Strategy Team to produce rigorous, confidence-tagged "
            "strategy outputs — at company level or project level — and submit "
            "completed packages for human review before forwarding to the Protean "
            "Pursuits Orchestrator for implementation."
        ),
        backstory=(
            "You are the Strategy Team Lead at Protean Pursuits LLC — a seasoned "
            "strategist with 20 years of experience advising technology companies, "
            "startups, and multi-product portfolios on business strategy, market "
            "positioning, and organisational design. You have worked across every "
            "layer of strategy: corporate, business unit, product, and functional. "
            "You operate at two scopes simultaneously. At company level you maintain "
            "the Protean Pursuits baseline strategy — the overarching business model, "
            "competitive positioning, partnership framework, and OKR architecture "
            "that applies across all projects. At project level you produce "
            "project-specific strategy overrides that build on the company baseline "
            "and address the particular market, competitive, and execution context "
            "of each individual project. "
            "You coordinate eleven specialist agents — Business Model, GTM, Product "
            "Strategy, Partnership, Competitive Intelligence, Financial Strategy, "
            "OKR/Planning, Risk & Scenario, Brand & Positioning, Talent & Org, and "
            "Technology Strategy. You brief each agent with the right context, "
            "review their outputs for quality and confidence-level compliance, and "
            "synthesise them into coherent strategy packages. "
            "You enforce one non-negotiable rule: every recommendation in every "
            "output must carry a confidence level (HIGH / MEDIUM / LOW) with "
            "supporting evidence or stated assumption. No recommendation ships "
            "without it. "
            "You never forward strategy outputs to the Protean Pursuits Orchestrator "
            "without human review. Strategy shapes implementation — human judgment "
            "is required before any strategy becomes an action."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=True
    )

import os
from crewai import Crew, Task

def run_strategy_orchestrator(context: dict, brief: str = "") -> str:
    """
    Entry point called by strategy_intake_flow.py.

    Builds the Strategy Team Orchestrator agent, issues a Task derived from
    the project context and brief, runs a single-agent Crew, saves output
    to output/<project>/strategy/, and returns the result string.

    All outputs require human review before forwarding to the Protean
    Pursuits Orchestrator for implementation. Every recommendation must
    carry a confidence level (HIGH / MEDIUM / LOW).

    Args:
        context: Project context dict (from load_context or stub).
        brief:   Plain-English strategy brief (may also live in context["brief"]).

    Returns:
        String output from the Strategy Team Orchestrator agent.
    """
    # ── Resolve brief ──────────────────────────────────────────────────────────
    resolved_brief = brief or context.get("brief", "")
    if not resolved_brief:
        raise ValueError(
            "run_strategy_orchestrator: no brief provided. "
            "Pass via 'brief' argument or context['brief']."
        )

    project = context.get("project", "ad-hoc")

    # ── Build agent ────────────────────────────────────────────────────────────
    agent = build_strategy_orchestrator()

    # ── Build task ─────────────────────────────────────────────────────────────
    task_description = f"""
You are the Strategy Team Orchestrator for the Protean Pursuits system.

PROJECT: {project}

BRIEF:
{resolved_brief}

CONTEXT:
{context.get("raw", "")}

{CONFIDENCE_INSTRUCTION}

Based on the brief above, select the appropriate run mode (positioning,
business_model, competitive, gtm, okr, financial, partnership, product,
risk, talent, technology, or full), engage the relevant specialist agents,
and produce the complete strategy deliverable.

SCOPE DETERMINATION:
- If the brief references a specific project, treat this as PROJECT scope
  and align with the company-level baseline strategy.
- If the brief is company-wide, treat this as COMPANY scope and update
  the baseline strategy accordingly.

MANDATORY OUTPUT STANDARDS:
- Every recommendation must carry a confidence level tag:
  [CONFIDENCE: HIGH | MEDIUM | LOW] with supporting evidence or stated assumption
- No recommendation ships without a confidence tag — omission is a defect
- End with OPEN ITEMS listing decisions requiring human approval before
  this strategy is forwarded to the Protean Pursuits Orchestrator
"""

    task = Task(
        description=task_description,
        expected_output=(
            "A complete strategy deliverable (brand positioning framework, business "
            "model canvas, competitive landscape, GTM plan, OKR framework, financial "
            "strategy, partnership framework, product strategy, risk register, org "
            "design, technology strategy, or full strategy package) appropriate to "
            "the requested mode. Every recommendation must carry a [CONFIDENCE: ...] "
            "tag. Must end with OPEN ITEMS section."
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
        output_dir = f"output/{project}/strategy"
        os.makedirs(output_dir, exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        out_path = f"{output_dir}/orchestrator_{ts}.md"
        with open(out_path, "w") as f:
            f.write(output_str)
        print(f"💾 Strategy Orchestrator output saved: {out_path}")

    return output_str

