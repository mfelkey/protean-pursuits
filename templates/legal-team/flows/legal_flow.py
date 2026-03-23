"""
flows/legal_flow.py

Protean Pursuits — Legal Team Flows

Four run modes:
  DRAFT      — draft a legal document (single agent or orchestrated)
  REVIEW     — review an external document for risks
  COMPLIANCE — regulatory compliance analysis
  MATTER     — multi-agent complex matter (e.g. product launch legal package)

All outputs:
  - Carry risk level (LOW / MEDIUM / HIGH / CRITICAL)
  - HIGH/CRITICAL trigger immediate human notification
  - All require human review before use

Usage:
  python flows/legal_flow.py --mode draft --type NDA
      --jurisdiction US --industry SAAS --name "Vendor NDA — Acme Corp"

  python flows/legal_flow.py --mode review --file docs/vendor_contract.md
      --jurisdiction UK --name "Acme Vendor Agreement Review"

  python flows/legal_flow.py --mode compliance --industry GAMBLING
      --jurisdiction UK,US,AU --name "PROJECT_NAME_PLACEHOLDER Pre-Launch Compliance"

  python flows/legal_flow.py --mode matter --name "PROJECT_NAME_PLACEHOLDER Launch Legal Package"
      --jurisdiction US,UK,AU,EU --industry GAMBLING,DATA,SAAS
      --project-id PROJ-TEMPLATE
"""

import sys
sys.path.insert(0, "/home/mfelkey/legal-team")

import os
import json
import argparse
from datetime import datetime
from crewai import Task, Crew, Process
from dotenv import load_dotenv

from agents.orchestrator.orchestrator import (
    build_legal_orchestrator, create_legal_context,
    save_context, log_event, save_artifact,
    notify_human, request_human_review, escalate_risk,
    RISK_LOW, RISK_MEDIUM, RISK_HIGH, RISK_CRITICAL,
    RISK_INSTRUCTION, JURISDICTION_INSTRUCTION,
    JURISDICTIONS, INDUSTRY_CONTEXTS
)
from agents.contract_drafting.contract_agent import build_contract_agent
from agents.document_review.review_agent import build_review_agent
from agents.privacy_data.privacy_agent import build_privacy_agent
from agents.ip_licensing.ip_agent import build_ip_agent
from agents.corporate_entity.corporate_agent import build_corporate_agent
from agents.employment_contractor.employment_agent import build_employment_agent
from agents.regulatory_compliance.compliance_agent import build_compliance_agent
from agents.litigation_dispute.litigation_agent import build_litigation_agent

load_dotenv("config/.env")

# Document type → agent mapping
DRAFT_AGENT_MAP = {
    "NDA":              build_contract_agent,
    "MSA":              build_contract_agent,
    "SOW":              build_contract_agent,
    "SAAS_AGREEMENT":   build_contract_agent,
    "API_LICENCE":      build_contract_agent,
    "DPA":              build_privacy_agent,
    "PRIVACY_POLICY":   build_privacy_agent,
    "COOKIE_POLICY":    build_privacy_agent,
    "TERMS_OF_SERVICE": build_contract_agent,
    "AFFILIATE":        build_contract_agent,
    "CONTRACTOR":       build_employment_agent,
    "EMPLOYMENT":       build_employment_agent,
    "IP_ASSIGNMENT":    build_ip_agent,
    "DATA_LICENCE":     build_ip_agent,
    "OPERATING_AGREEMENT": build_corporate_agent,
    "CEASE_DESIST":     build_litigation_agent,
    "DEMAND_LETTER":    build_litigation_agent,
}

MATTER_AGENTS = {
    "contract":    build_contract_agent,
    "review":      build_review_agent,
    "privacy":     build_privacy_agent,
    "ip":          build_ip_agent,
    "corporate":   build_corporate_agent,
    "employment":  build_employment_agent,
    "compliance":  build_compliance_agent,
    "litigation":  build_litigation_agent,
}


def _jurisdiction_brief(jurisdiction: str) -> str:
    juris_list = [j.strip() for j in jurisdiction.upper().split(",")]
    descriptions = [JURISDICTIONS.get(j, j) for j in juris_list]
    return f"Jurisdiction(s): {', '.join(descriptions)}"


def _industry_brief(industry: str) -> str:
    if not industry:
        return ""
    ind_list = [i.strip() for i in industry.upper().split(",")]
    descriptions = [INDUSTRY_CONTEXTS.get(i, i) for i in ind_list]
    return f"Industry context(s): {', '.join(descriptions)}"


def _detect_risk_from_output(output: str) -> str:
    """Extract risk level from agent output."""
    for level in [RISK_CRITICAL, RISK_HIGH, RISK_MEDIUM, RISK_LOW]:
        if f"RISK LEVEL: {level}" in output.upper():
            return level
    return RISK_MEDIUM  # default if not detected


# ── Mode: DRAFT ───────────────────────────────────────────────────────────────

def run_draft(context: dict, doc_type: str, brief: str = "") -> dict:
    context["run_mode"] = "DRAFT"
    log_event(context, "DRAFT_STARTED", doc_type)

    agent_factory = DRAFT_AGENT_MAP.get(doc_type.upper(), build_contract_agent)
    agent = agent_factory()

    task = Task(
        description=f"""
You are the Protean Pursuits {agent.role}.
Draft the following legal document:

Document type: {doc_type}
Matter: {context['matter_name']}
{_jurisdiction_brief(context['jurisdiction'])}
{_industry_brief(context.get('industry', ''))}
Project: {context.get('project_id', 'Company-level')}

Additional brief:
{brief if brief else 'No additional brief provided — use standard form for this document type.'}

{RISK_INSTRUCTION}
{JURISDICTION_INSTRUCTION}

DRAFTING REQUIREMENTS:
1. Label the document: DRAFT — NOT FOR EXECUTION
2. Use [BRACKETED PLACEHOLDERS] for all variable fields
3. Include a definitions section
4. Produce a complete, professionally structured document
5. End with a RISK NOTES section covering the top 3-5 risks in this document
   and any clauses that should be reviewed by external counsel
""",
        expected_output=f"Complete {doc_type} draft with risk assessment block and risk notes.",
        agent=agent
    )

    crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)
    print(f"\n⚖️  [DRAFT — {doc_type}] {context['matter_name']}...\n")
    result = str(crew.kickoff())

    risk_level = _detect_risk_from_output(result)
    path = save_artifact(context, f"{doc_type} Draft", f"DRAFT_{doc_type}",
                         result, "output/drafts", risk_level)

    # Immediate escalation for HIGH/CRITICAL
    escalate_risk(context, risk_level, path,
                  f"{doc_type} draft — {context['jurisdiction']}")

    # Human review gate
    approved = request_human_review(
        artifact_path=path,
        summary=f"{doc_type} draft — {context['matter_name']}",
        risk_level=risk_level
    )

    status = "APPROVED" if approved else "REJECTED"
    for a in context["artifacts"]:
        if a["path"] == path:
            a["status"] = status

    context["status"] = f"DRAFT_{status}"
    log_event(context, f"DRAFT_{status}", path)
    save_context(context)
    return context


# ── Mode: REVIEW ──────────────────────────────────────────────────────────────

def run_review(context: dict, document_path: str, brief: str = "") -> dict:
    context["run_mode"] = "REVIEW"
    log_event(context, "REVIEW_STARTED", document_path)

    if not os.path.exists(document_path):
        print(f"❌ Document not found: {document_path}")
        return context

    with open(document_path) as f:
        document_content = f.read()

    agent = build_review_agent()

    task = Task(
        description=f"""
You are the Protean Pursuits {agent.role}.
Review the following document on behalf of Protean Pursuits LLC:

Matter: {context['matter_name']}
{_jurisdiction_brief(context['jurisdiction'])}
{_industry_brief(context.get('industry', ''))}

Additional review brief:
{brief if brief else 'Full review — identify all material risks.'}

DOCUMENT TO REVIEW:
{document_content}

{RISK_INSTRUCTION}
{JURISDICTION_INSTRUCTION}

REVIEW OUTPUT STRUCTURE (required):
1. PLAIN LANGUAGE SUMMARY (3-5 sentences — what this document does)
2. OVERALL RECOMMENDATION: GO | PROCEED WITH CAUTION | DO NOT SIGN
3. RISK REGISTER (numbered list of every material risk, severity, and recommended action)
4. CLAUSE-BY-CLAUSE FLAGS (list every unusual, one-sided, or problematic clause)
5. REDLINE PRIORITIES (top 3-5 changes Protean Pursuits should request)
6. JURISDICTION ANALYSIS (any governing law issues or cross-border concerns)
7. EXTERNAL COUNSEL NOTE (specific issues that require external counsel input)
""",
        expected_output="Complete document review with risk register and recommendation.",
        agent=agent
    )

    crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)
    print(f"\n⚖️  [REVIEW] {context['matter_name']}...\n")
    result = str(crew.kickoff())

    risk_level = _detect_risk_from_output(result)
    path = save_artifact(context, f"Document Review — {context['matter_name']}",
                         "REVIEW", result, "output/reviews", risk_level)

    escalate_risk(context, risk_level, path,
                  f"Document review — {context['matter_name']}")

    approved = request_human_review(
        artifact_path=path,
        summary=f"Document review — {context['matter_name']}",
        risk_level=risk_level
    )

    context["status"] = "REVIEW_APPROVED" if approved else "REVIEW_REJECTED"
    log_event(context, context["status"], path)
    save_context(context)
    return context


# ── Mode: COMPLIANCE ──────────────────────────────────────────────────────────

def run_compliance(context: dict, brief: str = "") -> dict:
    context["run_mode"] = "COMPLIANCE"
    log_event(context, "COMPLIANCE_STARTED")

    agent = build_compliance_agent()

    task = Task(
        description=f"""
You are the Protean Pursuits {agent.role}.
Produce a regulatory compliance analysis for:

Matter: {context['matter_name']}
{_jurisdiction_brief(context['jurisdiction'])}
{_industry_brief(context.get('industry', ''))}
Project: {context.get('project_id', 'Company-level')}

Focus: {brief if brief else 'Full pre-launch compliance review'}

{RISK_INSTRUCTION}
{JURISDICTION_INSTRUCTION}

COMPLIANCE OUTPUT STRUCTURE (required):
1. REGULATORY LANDSCAPE (which laws and regulators apply, jurisdiction by jurisdiction)
2. LICENCE/REGISTRATION REQUIREMENTS (what licences or registrations are needed, if any)
3. COMPLIANCE OBLIGATIONS (what the company must do before launch and on an ongoing basis)
4. PRE-LAUNCH CHECKLIST (ordered list of compliance actions with owner and urgency)
5. GAP ANALYSIS (what is currently missing or unresolved)
6. CRITICAL PATH ITEMS (what blocks launch if not resolved)
7. EXTERNAL COUNSEL REQUIREMENTS (which matters need specialist regulatory counsel)
""",
        expected_output="Complete compliance analysis with pre-launch checklist and gap analysis.",
        agent=agent
    )

    crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)
    print(f"\n⚖️  [COMPLIANCE] {context['matter_name']}...\n")
    result = str(crew.kickoff())

    risk_level = _detect_risk_from_output(result)
    path = save_artifact(context, f"Compliance Analysis — {context['matter_name']}",
                         "COMPLIANCE", result, "output/compliance", risk_level)

    escalate_risk(context, risk_level, path,
                  f"Compliance analysis — {context['matter_name']}")

    approved = request_human_review(
        artifact_path=path,
        summary=f"Compliance analysis — {context['matter_name']}",
        risk_level=risk_level
    )

    context["status"] = "COMPLIANCE_APPROVED" if approved else "COMPLIANCE_REJECTED"
    log_event(context, context["status"], path)
    save_context(context)
    return context


# ── Mode: MATTER (multi-agent) ────────────────────────────────────────────────

def run_matter(context: dict, agents_needed: list, brief: str = "") -> dict:
    """
    Multi-agent matter — runs specified agents sequentially and
    synthesises into a comprehensive legal package.
    agents_needed: list of keys from MATTER_AGENTS
    """
    context["run_mode"] = "MATTER"
    log_event(context, "MATTER_STARTED", str(agents_needed))

    notify_human(
        subject=f"Multi-agent legal matter started — {context['matter_name']}",
        message=(
            f"Legal ID: {context['legal_id']}\n"
            f"Matter: {context['matter_name']}\n"
            f"Jurisdiction(s): {context['jurisdiction']}\n"
            f"Agents: {', '.join(agents_needed)}\n\n"
            f"You will receive a single review request when the full "
            f"legal package is complete."
        )
    )

    results = {}
    highest_risk = RISK_LOW

    for agent_key in agents_needed:
        if agent_key not in MATTER_AGENTS:
            print(f"⚠️  Unknown agent: {agent_key} — skipping")
            continue

        agent = MATTER_AGENTS[agent_key]()
        prior = "\n\n".join([
            f"--- {k.upper()} OUTPUT (excerpt) ---\n{v[:600]}..."
            for k, v in results.items()
        ])

        task = Task(
            description=f"""
You are the Protean Pursuits {agent.role}.
This is part of a multi-agent legal matter.

Matter: {context['matter_name']}
{_jurisdiction_brief(context['jurisdiction'])}
{_industry_brief(context.get('industry', ''))}
Project: {context.get('project_id', 'Company-level')}

Your specific brief:
{brief if brief else f'Produce your standard analysis for this matter from a {agent_key} perspective.'}

Prior agent outputs for context:
{prior if prior else 'No prior outputs yet — you are first.'}

{RISK_INSTRUCTION}
{JURISDICTION_INSTRUCTION}
""",
            expected_output=f"Complete {agent_key} legal analysis with risk assessment block.",
            agent=agent
        )

        crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)
        print(f"\n⚖️  [MATTER — {agent_key.upper()}] Running...\n")
        result = str(crew.kickoff())
        results[agent_key] = result

        risk = _detect_risk_from_output(result)
        path = save_artifact(context, f"{agent_key.upper()} Analysis",
                             f"MATTER_{agent_key.upper()}", result,
                             "output/memos", risk)
        escalate_risk(context, risk, path, f"Matter component: {agent_key}")

        risk_order = [RISK_LOW, RISK_MEDIUM, RISK_HIGH, RISK_CRITICAL]
        if risk_order.index(risk) > risk_order.index(highest_risk):
            highest_risk = risk

    # Synthesise into legal package cover memo
    orchestrator = build_legal_orchestrator()
    synth_task = Task(
        description=f"""
You are the Protean Pursuits Legal Team Orchestrator.
Synthesise the following specialist legal outputs into a single
Legal Package Cover Memo for human review.

Matter: {context['matter_name']}
{_jurisdiction_brief(context['jurisdiction'])}

Specialist outputs:
{json.dumps({k: v[:500] for k, v in results.items()}, indent=2)}

Produce:
1. EXECUTIVE LEGAL SUMMARY (what this package covers, overall risk level)
2. CRITICAL ACTIONS (what must happen before any document is used or any
   action is taken — ordered by urgency)
3. EXTERNAL COUNSEL REQUIREMENTS (consolidated list of all matters requiring
   external counsel, with jurisdiction and specialism needed)
4. DOCUMENT INDEX (list of all documents in this package with their risk levels)
5. FORWARDING NOTE TO PROTEAN PURSUITS ORCHESTRATOR (what this package
   authorises, what requires human decision first)

{RISK_INSTRUCTION}
""",
        expected_output="Legal Package Cover Memo with consolidated risk assessment.",
        agent=orchestrator
    )

    crew = Crew(agents=[orchestrator], tasks=[synth_task],
                process=Process.sequential, verbose=True)
    synthesis = str(crew.kickoff())
    synth_path = save_artifact(context, "Legal Package Cover Memo",
                               "MATTER_COVER_MEMO", synthesis,
                               "output/memos", highest_risk)

    approved = request_human_review(
        artifact_path=synth_path,
        summary=f"Legal Package — {context['matter_name']} ({len(agents_needed)} specialists)",
        risk_level=highest_risk
    )

    context["status"] = "MATTER_APPROVED" if approved else "MATTER_REJECTED"
    log_event(context, context["status"], synth_path)
    save_context(context)
    return context


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Protean Pursuits — Legal Team")
    parser.add_argument("--mode", choices=["draft", "review", "compliance", "matter"],
                        required=True)
    parser.add_argument("--name", type=str, required=True, help="Matter name")
    parser.add_argument("--jurisdiction", type=str, default="US",
                        help="Comma-separated jurisdiction codes (US,UK,EU,AU,IN,SG,HK)")
    parser.add_argument("--industry", type=str, default=None,
                        help="Comma-separated industry codes (SAAS,DATA,GAMBLING,FINANCIAL,HEALTHCARE,ECOMMERCE,PUBLISHING_AI)")
    parser.add_argument("--project-id", type=str, default=None)
    parser.add_argument("--type", type=str, default=None,
                        help="Document type for draft mode (NDA, MSA, DPA, PRIVACY_POLICY, etc.)")
    parser.add_argument("--file", type=str, default=None,
                        help="Path to document for review mode")
    parser.add_argument("--agents", type=str, default=None,
                        help="Comma-separated agent keys for matter mode")
    parser.add_argument("--brief", type=str, default="",
                        help="Additional context or instructions")
    args = parser.parse_args()

    context = create_legal_context(
        matter_name=args.name,
        matter_type=args.mode.upper(),
        jurisdiction=args.jurisdiction,
        industry=args.industry,
        project_id=args.project_id
    )

    print(f"\n⚖️  Protean Pursuits Legal Team")
    print(f"   Mode: {args.mode.upper()}")
    print(f"   Matter: {args.name}")
    print(f"   Jurisdiction: {args.jurisdiction}")
    print(f"   Industry: {args.industry or 'General'}")
    print(f"   Started: {datetime.utcnow().isoformat()}\n")

    if args.mode == "draft":
        if not args.type:
            print(f"❌ --type required for draft mode. Options: {list(DRAFT_AGENT_MAP.keys())}")
            exit(1)
        context = run_draft(context, args.type, args.brief)

    elif args.mode == "review":
        if not args.file:
            print("❌ --file required for review mode")
            exit(1)
        context = run_review(context, args.file, args.brief)

    elif args.mode == "compliance":
        context = run_compliance(context, args.brief)

    elif args.mode == "matter":
        agents = args.agents.split(",") if args.agents else list(MATTER_AGENTS.keys())
        context = run_matter(context, agents, args.brief)

    print(f"\n✅ Legal Team run complete.")
    print(f"   Legal ID: {context['legal_id']}")
    print(f"   Status: {context['status']}")
    print(f"   Risk Level: {context.get('risk_level', 'N/A')}")
    print(f"   Artifacts: {len(context['artifacts'])}")
