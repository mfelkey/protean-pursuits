"""
agents/orchestrator/orchestrator.py

Protean Pursuits — Design Team Orchestrator

Scope: Portfolio-wide — serves Dev, Marketing, Strategy, Legal, and any
       other team requiring design outputs.

Tooling: Tool-agnostic — outputs are detailed design specifications,
         component definitions, brand guidelines, and annotated assets
         that can be executed in any design tool (Figma, Sketch, Adobe XD,
         CSS, etc.)

Run modes:
  BRIEF        — single agent, on-demand
  UX_SPRINT    — research → wireframe → usability, for a product feature
  BRAND_BUILD  — brand identity + design system, for a new product
  AUDIT        — accessibility + usability audit of existing product
  FULL_DESIGN  — all agents, full design package

Human-in-the-loop: all outputs require human review before handoff
to implementation teams.
"""

import os
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, LLM

load_dotenv("config/.env")


DESIGN_INSTRUCTION = """
DESIGN OUTPUT STANDARDS — MANDATORY:

1. TOOL-AGNOSTIC SPECS: All outputs must be implementable in any design
   tool or directly in code. Use precise values: hex colors, px/rem sizing,
   named tokens, grid specifications. Never reference tool-specific features.

2. ACCESSIBILITY FIRST: Every design output must consider WCAG 2.1 AA
   compliance from the start. Flag any element that may fail contrast,
   keyboard navigation, or screen reader requirements.

3. ANNOTATION REQUIREMENT: Every wireframe, component spec, or layout
   must include annotations explaining interaction behaviour, states
   (default, hover, focus, disabled, error), and responsive behaviour.

4. HANDOFF READINESS: Outputs must be complete enough for a developer
   to implement without follow-up questions. Include: spacing, typography
   scale, color tokens, component states, breakpoints.

5. OPEN QUESTIONS: End every output with a list of design decisions that
   require human input before implementation begins.
"""


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
        return True
    except Exception as e:
        print(f"⚠️  Email failed: {e}")
        return False


def notify_human(subject: str, message: str) -> None:
    send_sms(f"[DESIGN-TEAM] {subject}\n{message}")
    send_email(f"[DESIGN-TEAM] {subject}", message)


def request_human_review(artifact_path: str, summary: str,
                          timeout_hours: int = 48) -> bool:
    import time as _t
    approval_dir = "logs/approvals"
    os.makedirs(approval_dir, exist_ok=True)
    review_id = f"DESIGN-{uuid.uuid4().hex[:8].upper()}"
    response_file = f"{approval_dir}/{review_id}.response.json"

    with open(f"{approval_dir}/{review_id}.json", "w") as f:
        json.dump({"review_id": review_id, "artifact_path": artifact_path,
                   "summary": summary, "requested_at": datetime.utcnow().isoformat(),
                   "status": "PENDING"}, f, indent=2)

    notify_human(
        subject=f"[DESIGN REVIEW] {review_id}",
        message=(
            f"Summary: {summary}\nArtifact: {artifact_path}\n\n"
            f"Approve: write to {response_file}:\n"
            f'  {{"decision": "APPROVED"}}\n'
            f"Reject: {{'decision': 'REJECTED', 'reason': '...'}}\n"
            f"Timeout: {timeout_hours}h"
        )
    )
    print(f"\n⏸️  [DESIGN REVIEW] {review_id} — {summary}")

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
        _t.sleep(30)
        elapsed += 30
    print(f"⏰ Timed out — {review_id}")
    return False


def create_design_context(project_name: str, design_type: str,
                           project_id: str = None) -> dict:
    return {
        "framework": "protean-pursuits-design",
        "design_id": f"DESIGN-{uuid.uuid4().hex[:8].upper()}",
        "project_name": project_name,
        "design_type": design_type,
        "project_id": project_id,
        "created_at": datetime.utcnow().isoformat(),
        "status": "INITIATED",
        "artifacts": [],
        "events": []
    }


def save_context(context: dict) -> str:
    os.makedirs("logs", exist_ok=True)
    path = f"logs/{context['design_id']}.json"
    with open(path, "w") as f:
        json.dump(context, f, indent=2)
    return path


def log_event(context: dict, event_type: str, detail: str = "") -> None:
    context["events"].append({"event_type": event_type, "detail": detail,
                               "timestamp": datetime.utcnow().isoformat()})
    save_context(context)


def save_artifact(context: dict, name: str, artifact_type: str,
                  content: str, output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = f"{output_dir}/{context['design_id']}_{artifact_type}_{ts}.md"
    with open(path, "w") as f:
        f.write(content)
    context["artifacts"].append({"name": name, "type": artifact_type, "path": path,
                                  "status": "PENDING_REVIEW",
                                  "created_at": datetime.utcnow().isoformat()})
    log_event(context, f"{artifact_type}_COMPLETE", path)
    print(f"\n💾 [{artifact_type}] Saved: {path}")
    return path


def build_design_orchestrator() -> Agent:
    llm = LLM(model=os.getenv("TIER1_MODEL", "ollama/qwen3:32b"),
               base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
               timeout=1800)
    return Agent(
        role="Design Team Orchestrator",
        goal=(
            "Coordinate the Design Team to produce portfolio-wide design outputs — "
            "research, wireframes, UI specs, brand systems, motion guidelines, and "
            "accessibility audits — for any Protean Pursuits project or team."
        ),
        backstory=(
            "You are the Design Director at Protean Pursuits LLC — a design leader "
            "with 18 years of experience building design systems and product experiences "
            "for data-driven technology products. You serve every team in the portfolio: "
            "Dev needs component specs and interaction flows, Marketing needs brand "
            "assets and campaign visuals, Strategy needs clear data visualisations and "
            "presentation frameworks, Legal needs well-structured document templates. "
            "You lead eight specialist agents — UX Research, Wireframing & Prototyping, "
            "UI Design & Component Library, Brand & Visual Identity, Motion & Animation, "
            "Design System Management, Accessibility, and Usability. You orchestrate "
            "them based on the project's needs, ensure consistency between outputs, "
            "and synthesise complex design packages for human review. "
            "You are tool-agnostic: your outputs are precise, implementable design "
            "specifications that work in any tool or directly in code. You never "
            "produce vague directional guidance — every output contains the exact "
            "values, tokens, states, and annotations a builder needs."
        ),
        llm=llm, verbose=True, allow_delegation=True
    )
