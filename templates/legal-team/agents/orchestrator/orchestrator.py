"""
agents/orchestrator/orchestrator.py

Protean Pursuits — Legal Team Orchestrator

Professional posture: In-house counsel equivalent
- Give direct recommendations
- Flag when external counsel is required
- All outputs carry risk level and jurisdiction tags
- HIGH/CRITICAL risk outputs trigger immediate human notification
- All outputs require human review before use

Jurisdictions: US, EU, UK, Australia, India, Singapore/HK/Asia
Industries: SaaS, Data/Analytics, Sports Betting/Gambling,
            Financial Services, Healthcare/HIPAA, E-Commerce,
            Publishing & AI

Risk levels (required on all outputs):
  LOW      — standard matter, low exposure, no external counsel needed
  MEDIUM   — moderate complexity or exposure, internal review sufficient
  HIGH     — significant exposure or complexity, external counsel recommended
  CRITICAL — immediate legal risk, do not proceed without external counsel

External counsel flag (required where applicable):
  [EXTERNAL COUNSEL REQUIRED: reason]
  [EXTERNAL COUNSEL RECOMMENDED: reason]
  [EXTERNAL COUNSEL NOT REQUIRED: rationale]
"""

import os
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, LLM

load_dotenv("config/.env")


# ── Jurisdiction constants ────────────────────────────────────────────────────

JURISDICTIONS = {
    "US":        "United States (Federal + all 50 states)",
    "EU":        "European Union (including GDPR, EU commercial law)",
    "UK":        "United Kingdom (post-Brexit, English law)",
    "AU":        "Australia (federal + state/territory law)",
    "IN":        "India (Indian Contract Act, IT Act, PDPB)",
    "SG":        "Singapore (Companies Act, PDPA)",
    "HK":        "Hong Kong (common law, PDPO)",
    "MULTI":     "Multi-jurisdiction (specify in brief)",
}

# ── Industry regulatory contexts ──────────────────────────────────────────────

INDUSTRY_CONTEXTS = {
    "SAAS":          "SaaS / software products (ToS, SLAs, acceptable use, IP ownership)",
    "DATA":          "Data products & analytics (data licensing, resale, provenance, output ownership)",
    "GAMBLING":      "Sports betting / gambling (UK Gambling Act, US PASPA/state regs, AU Interactive Gambling Act)",
    "FINANCIAL":     "Financial services (SEC, FCA, ASIC, MAS regulations)",
    "HEALTHCARE":    "Healthcare / HIPAA (PHI, BAAs, HITECH, state health privacy laws)",
    "ECOMMERCE":     "E-commerce / consumer (consumer protection, distance selling, refund obligations)",
    "PUBLISHING_AI": "Publishing & AI (AI-generated content ownership, training data licensing, copyright fair use, model output liability)",
}

# ── Risk level constants ──────────────────────────────────────────────────────

RISK_LOW      = "LOW"
RISK_MEDIUM   = "MEDIUM"
RISK_HIGH     = "HIGH"
RISK_CRITICAL = "CRITICAL"

RISK_DEFINITIONS = {
    "LOW":      "Standard matter, low exposure. Internal review sufficient. No external counsel needed.",
    "MEDIUM":   "Moderate complexity or exposure. Internal review sufficient with caveats noted.",
    "HIGH":     "Significant exposure or complexity. External counsel recommended before proceeding.",
    "CRITICAL": "Immediate legal risk or highly complex jurisdiction issue. Do NOT proceed without external counsel.",
}

RISK_INSTRUCTION = """
RISK LEVEL REQUIREMENT — MANDATORY ON ALL OUTPUTS:
Every legal output must include a risk assessment block at the top:

---
RISK LEVEL: [LOW | MEDIUM | HIGH | CRITICAL]
JURISDICTION(S): [list all applicable]
EXTERNAL COUNSEL: [REQUIRED | RECOMMENDED | NOT REQUIRED] — [one sentence reason]
DISCLAIMER: This output was produced by a paraprofessional legal team operating
as in-house counsel equivalent. It does not constitute legal advice from a
licensed attorney. Documents marked EXTERNAL COUNSEL REQUIRED or RECOMMENDED
must be reviewed by qualified legal counsel before use or execution.
---

Risk level definitions:
- LOW:      Standard matter, low exposure, no external counsel needed
- MEDIUM:   Moderate complexity or exposure, internal review sufficient
- HIGH:     Significant exposure, external counsel recommended
- CRITICAL: Immediate risk, do NOT proceed without external counsel

Never omit the risk assessment block. Never understate risk to avoid escalation.
"""

JURISDICTION_INSTRUCTION = """
JURISDICTION GUIDANCE:
For every legal output, explicitly identify:
1. Which jurisdiction(s) govern the matter
2. Any conflicts between jurisdictions
3. Which jurisdiction's law you have applied and why
4. Any jurisdiction-specific requirements that differ from the default analysis

Primary jurisdictions covered: US (federal + state), EU, UK, Australia, India,
Singapore, Hong Kong. For matters outside these jurisdictions, flag explicitly
that coverage is limited and external counsel in that jurisdiction is required.
"""


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
    send_sms(f"[LEGAL-TEAM] {subject}\n{message}")
    send_email(f"[LEGAL-TEAM] {subject}", message)


def escalate_risk(context: dict, risk_level: str, artifact_path: str,
                  reason: str) -> None:
    """Immediately notify human for HIGH or CRITICAL risk outputs."""
    if risk_level in (RISK_HIGH, RISK_CRITICAL):
        notify_human(
            subject=f"[{risk_level} LEGAL RISK] {context['matter_name']}",
            message=(
                f"Matter: {context['matter_name']} ({context['legal_id']})\n"
                f"Risk Level: {risk_level}\n"
                f"Reason: {reason}\n"
                f"Artifact: {artifact_path}\n\n"
                f"{'DO NOT PROCEED without external counsel review.' if risk_level == RISK_CRITICAL else 'External counsel recommended before proceeding.'}\n\n"
                f"Review this output immediately."
            )
        )
        print(f"\n🚨 [{risk_level}] Risk escalation sent to human — {context['legal_id']}")


# ── Human review gate ─────────────────────────────────────────────────────────

def request_human_review(artifact_path: str, summary: str,
                          risk_level: str, timeout_hours: int = 48) -> bool:
    """
    All legal outputs require human review before use.
    HIGH/CRITICAL also trigger immediate escalation via escalate_risk().
    """
    import time

    approval_dir = "logs/approvals"
    os.makedirs(approval_dir, exist_ok=True)
    review_id = f"LEGAL-{uuid.uuid4().hex[:8].upper()}"
    review_file = f"{approval_dir}/{review_id}.json"
    response_file = f"{approval_dir}/{review_id}.response.json"

    with open(review_file, "w") as f:
        json.dump({
            "review_id": review_id,
            "risk_level": risk_level,
            "artifact_path": artifact_path,
            "summary": summary,
            "requested_at": datetime.utcnow().isoformat(),
            "status": "PENDING"
        }, f, indent=2)

    notify_human(
        subject=f"[LEGAL REVIEW — {risk_level}] {review_id}",
        message=(
            f"Risk Level: {risk_level}\n"
            f"Summary: {summary}\n"
            f"Artifact: {artifact_path}\n"
            f"Review ID: {review_id}\n\n"
            f"{'⚠️  EXTERNAL COUNSEL REQUIRED — do not use this document without counsel review.' if risk_level == RISK_CRITICAL else ''}"
            f"{'⚠️  External counsel recommended before proceeding.' if risk_level == RISK_HIGH else ''}\n\n"
            f"To approve: write to {response_file}:\n"
            f'  {{"decision": "APPROVED"}}\n\n'
            f"To reject with feedback:\n"
            f'  {{"decision": "REJECTED", "reason": "your feedback"}}\n\n'
            f"Timeout: {timeout_hours} hours."
        )
    )

    print(f"\n⏸️  [LEGAL REVIEW — {risk_level}] {review_id}")
    print(f"   Artifact: {artifact_path}\n")

    elapsed = 0
    timeout = timeout_hours * 3600
    while elapsed < timeout:
        if os.path.exists(response_file):
            with open(response_file) as f:
                response = json.load(f)
            decision = response.get("decision", "").upper()
            if decision == "APPROVED":
                print(f"✅ Legal output approved — {review_id}")
                return True
            elif decision == "REJECTED":
                print(f"❌ Legal output rejected — {review_id}: {response.get('reason', '')}")
                return False
        import time as _t
        _t.sleep(30)
        elapsed += 30

    print(f"⏰ Legal review timed out — {review_id}. NOT releasing document.")
    return False


# ── Legal matter context ──────────────────────────────────────────────────────

def create_legal_context(matter_name: str, matter_type: str,
                          jurisdiction: str, industry: str = None,
                          project_id: str = None) -> dict:
    return {
        "framework": "protean-pursuits-legal",
        "legal_id": f"LEGAL-{uuid.uuid4().hex[:8].upper()}",
        "matter_name": matter_name,
        "matter_type": matter_type,
        "jurisdiction": jurisdiction,
        "industry": industry,
        "project_id": project_id,
        "owner": "Protean Pursuits LLC",
        "created_at": datetime.utcnow().isoformat(),
        "status": "INITIATED",
        "risk_level": None,
        "external_counsel_required": False,
        "artifacts": [],
        "events": []
    }


def save_context(context: dict) -> str:
    os.makedirs("logs", exist_ok=True)
    path = f"logs/{context['legal_id']}.json"
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


def save_artifact(context: dict, name: str, artifact_type: str,
                  content: str, output_dir: str,
                  risk_level: str = RISK_MEDIUM) -> str:
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = f"{output_dir}/{context['legal_id']}_{artifact_type}_{timestamp}.md"
    with open(path, "w") as f:
        f.write(content)
    context["risk_level"] = risk_level
    context["artifacts"].append({
        "name": name,
        "type": artifact_type,
        "path": path,
        "risk_level": risk_level,
        "status": "PENDING_REVIEW",
        "created_at": datetime.utcnow().isoformat()
    })
    log_event(context, f"{artifact_type}_COMPLETE", path)
    print(f"\n💾 [{artifact_type} — {risk_level}] Saved: {path}")
    return path


# ── Legal Orchestrator agent ──────────────────────────────────────────────────

def build_legal_orchestrator() -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/qwen3:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    return Agent(
        role="Legal Team Orchestrator",
        goal=(
            "Coordinate the Legal Team to produce accurate, jurisdiction-aware, "
            "risk-rated legal outputs — drafts, reviews, compliance analyses, and "
            "memos — and ensure all HIGH and CRITICAL risk matters are escalated "
            "to the human immediately and flagged for external counsel."
        ),
        backstory=(
            "You are the General Counsel equivalent at Protean Pursuits LLC — "
            "a senior legal professional with 20 years of experience operating as "
            "in-house counsel for technology companies across multiple jurisdictions. "
            "You have deep expertise across commercial contracts, privacy law, IP, "
            "corporate governance, employment, and regulatory compliance. You have "
            "worked on matters governed by US, EU, UK, Australian, Indian, and "
            "Asian law and understand the material differences between these legal "
            "systems for technology and data companies. "
            "You lead a team of eight specialist agents — Contract Drafting, Document "
            "Review & Risk, Privacy & Data Protection, IP & Licensing, Corporate & "
            "Entity, Employment & Contractor, Regulatory Compliance, and Litigation "
            "& Dispute Risk. You brief each agent with precise matter context, review "
            "their outputs for quality and risk accuracy, and synthesise complex "
            "matters that require multiple specialists. "
            "You operate as in-house counsel equivalent: you give direct "
            "recommendations, you flag clearly when external counsel is required, "
            "and you never understate legal risk to avoid escalation. "
            "You enforce two non-negotiable rules: (1) every output carries a risk "
            "level (LOW / MEDIUM / HIGH / CRITICAL) and external counsel flag; "
            "(2) HIGH and CRITICAL outputs trigger immediate human notification "
            "before the document is released. All documents are marked with the "
            "standard paraprofessional disclaimer — this team produces work product "
            "of the highest quality, but no output constitutes legal advice from a "
            "licensed attorney in any jurisdiction."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=True
    )
