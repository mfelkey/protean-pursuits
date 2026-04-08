import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from agents.orchestrator.orchestrator import log_event, save_context, request_human_approval

load_dotenv("config/.env")


def build_email_agent() -> Agent:
    llm = LLM(
        model=os.getenv("TIER2_MODEL", "ollama/qwen3-coder:30b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    return Agent(
        role="Email Agent",
        goal=(
            "Write and structure all PROJECT_NAME_PLACEHOLDER email communications — newsletters, "
            "drip sequences, transactional emails, and re-engagement campaigns — using "
            "CRM segmentation data to personalise at scale, and submit every send for "
            "human approval before execution."
        ),
        backstory=(
            "You are a Senior Email Marketing Strategist and Copywriter with 10 years "
            "of experience building high-performing email programmes for subscription "
            "SaaS and fintech products. You have deep expertise in lifecycle marketing: "
            "you know the difference between an onboarding sequence that converts and "
            "one that churns, and you know how to write a re-engagement email that "
            "doesn't feel desperate. "
            "You use CRM segmentation data to personalise sends: free vs Sharp tier, "
            "sport preference (soccer, NFL, NBA), engagement recency, and geographic "
            "market (US, UK, Australia). You never send the same email to everyone. "
            "You write in the PROJECT_NAME_PLACEHOLDER brand voice without exception: direct, "
            "data-literate, quietly confident. Your subject lines earn the open without "
            "clickbait. Your body copy delivers analytical value in the first paragraph. "
            "Your CTAs are specific and low-friction. "
            "You understand the compliance requirements: CAN-SPAM for US, GDPR/PECR "
            "for UK and EU, responsible gambling footer requirements per jurisdiction. "
            "You never send to users who have self-excluded or opted out. You always "
            "include an unsubscribe mechanism. "
            "You produce a complete Email Production Package for every send: subject "
            "line variants (A/B), preview text, full HTML-ready copy, plain text "
            "fallback, CRM segment definition, send schedule, and compliance checklist. "
            "You never send without explicit human approval."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_email_production(context: dict, email_type: str, segment: str,
                          subject_hint: str, sport: str) -> dict:
    """
    Draft a complete email production package.
    email_type: 'NEWSLETTER' | 'DRIP' | 'REENGAGEMENT' | 'TRANSACTIONAL'
    segment: CRM segment description (e.g., 'Free tier, soccer-interested, US')
    Submits for human approval before saving as sendable.
    Returns updated context.
    """
    ea = build_email_agent()

    email_task = Task(
        description=f"""
You are the PROJECT_NAME_PLACEHOLDER Email Agent. Produce a complete email production package
for the following brief:

Email Type: {email_type}
CRM Segment: {segment}
Subject Hint: {subject_hint}
Sport / Competition: {sport}
Brand Voice: Direct, data-literate, quietly confident. Never hypes. Never guarantees.

BRAND RULES — NEVER VIOLATE:
- No guaranteed wins, guaranteed returns, or certainty of outcome language
- Never say "we predict" — surface opportunities; users decide
- No "beat the bookies" or adversarial framing
- Responsible gambling footer required in all marketing emails

Produce a complete Email Production Package with ALL of the following:

1. SUBJECT LINE VARIANTS (A/B)
   - Subject A: data-led angle (e.g., stat or model output hook)
   - Subject B: curiosity/benefit angle
   - Preview text for each (90 chars max)
   - Predicted open rate rationale

2. EMAIL COPY — FULL DRAFT
   - From name and from address recommendation
   - Personalisation tokens (e.g., {{first_name}}, {{sport_preference}})
   - Header / hero section
   - Body copy (plain language, analytical depth, value-first)
   - CTA block (button text + URL placeholder)
   - Secondary content block (if applicable)
   - Footer (unsubscribe link, company address, responsible gambling notice)

3. PLAIN TEXT FALLBACK
   - Full plain text version of the email

4. CRM SEGMENT DEFINITION
   - Exact segment filter logic (tier, sport preference, engagement, geo)
   - Estimated list size note (placeholder — confirm with CRM data)
   - Suppression rules (self-excluded users, opted-out, prior unsubscribes)

5. SEND SCHEDULE RECOMMENDATION
   - Recommended send day and time (ET and GMT)
   - Rationale (sport schedule alignment, engagement data)

6. COMPLIANCE CHECKLIST
   - CAN-SPAM: physical address included, unsubscribe mechanism present
   - GDPR/PECR: consent basis documented, data processing note
   - Self-excluded users suppressed: confirmed
   - Responsible gambling footer: present and jurisdiction-appropriate
   - No guaranteed outcome language: confirmed
   - No tipster-style claims: confirmed

Output the complete Email Production Package as well-formatted markdown.
""",
        expected_output="A complete Email Production Package with subject lines, full copy, plain text, segment definition, and compliance checklist.",
        agent=ea
    )

    crew = Crew(
        agents=[ea],
        tasks=[email_task],
        process=Process.sequential,
        verbose=True
    )

    print(f"\n📧 Email Agent drafting {email_type} for segment: {segment}...\n")
    result = crew.kickoff()

    os.makedirs("output/emails", exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    draft_path = f"output/emails/{context['campaign_id']}_{email_type}_{timestamp}_DRAFT.md"

    with open(draft_path, "w") as f:
        f.write(str(result))

    print(f"\n💾 Email production package saved: {draft_path}")

    # ── Human-in-the-loop: approval gate ─────────────────────────────────────
    approved = request_human_approval(
        gate_type="EMAIL",
        artifact_path=draft_path,
        summary=f"{email_type} — {segment} — {subject_hint}"
    )

    if approved:
        approved_path = draft_path.replace("_DRAFT.md", "_APPROVED.md")
        os.rename(draft_path, approved_path)
        context["artifacts"].append({
            "name": f"{email_type} Email — {subject_hint}",
            "type": "EMAIL",
            "email_type": email_type,
            "segment": segment,
            "path": approved_path,
            "status": "APPROVED",
            "created_at": datetime.utcnow().isoformat(),
            "created_by": "Email Agent"
        })
        log_event(context, "EMAIL_APPROVED", approved_path)
        context["status"] = "EMAIL_APPROVED"
    else:
        context["artifacts"].append({
            "name": f"{email_type} Email — {subject_hint}",
            "type": "EMAIL",
            "email_type": email_type,
            "segment": segment,
            "path": draft_path,
            "status": "REJECTED",
            "created_at": datetime.utcnow().isoformat(),
            "created_by": "Email Agent"
        })
        log_event(context, "EMAIL_REJECTED", draft_path)
        context["status"] = "EMAIL_REJECTED"

    save_context(context)
    return context


if __name__ == "__main__":
    from agents.orchestrator.orchestrator import create_campaign_context

    context = create_campaign_context(
        campaign_name="World Cup 2026 Launch Week",
        campaign_type="EMAIL"
    )

    context = run_email_production(
        context=context,
        email_type="NEWSLETTER",
        segment="Free tier, soccer-interested, US, registered last 30 days",
        subject_hint="World Cup Day 1 — our model's top signals",
        sport="FIFA World Cup 2026"
    )

    print(f"\n✅ Email agent run complete. Status: {context['status']}")
