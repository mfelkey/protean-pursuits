"""
flows/intake_flow.py

Protean Pursuits — Project Intake Flow

Two modes:
  1. Discovery Mode  — interactive intake interview → draft PRD → human approval
  2. Brief Mode      — PRD/brief provided           → classify → kickoff

Usage:
  python flows/intake_flow.py --mode discovery --name "My Project"
  python flows/intake_flow.py --mode brief --name "ParallaxEdge" --prd docs/Parallax_PRD_v1_8.md
"""

import sys
sys.path.insert(0, "/home/mfelkey/protean-pursuits")

import os
import json
import argparse
from datetime import datetime
from crewai import Agent, Task, Crew, Process, LLM
from dotenv import load_dotenv

from agents.orchestrator.orchestrator import (
    build_orchestrator, create_project_context, save_context,
    log_event, notify_human, request_human_approval, spinup_project_repo
)
from agents.project_manager.project_manager import build_project_manager, run_project_kickoff

load_dotenv("config/.env")

ALL_TEAMS = ["dev", "ds", "marketing", "design", "qa", "legal", "strategy"]

TEAM_DESCRIPTIONS = {
    "dev":       "Software development — frontend, backend, infrastructure",
    "ds":        "Data science — ML models, pipelines, analytics",
    "marketing": "Go-to-market — content, social, email, campaigns",
    "design":    "UX/UI design — wireframes, mockups, design system",
    "qa":        "Quality assurance — test plans, acceptance, sign-off",
    "legal":     "Legal/compliance — policies, risk, regulatory review",
    "strategy":  "Strategy — market research, business case, OKRs",
}


# ── Discovery Mode ────────────────────────────────────────────────────────────

def run_discovery_intake(project_name: str) -> dict:
    """
    Run a structured discovery interview and produce a draft PRD.
    Human approves the PRD before any team work begins.
    """
    context = create_project_context(project_name, mode="DISCOVERY")
    orchestrator = build_orchestrator()

    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/qwen3:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    discovery_task = Task(
        description=f"""
You are the Protean Pursuits Orchestrator running a Discovery intake interview
for a new project named: "{project_name}"

Produce a structured Discovery Summary that captures everything needed to write
a PRD. Cover ALL of the following areas:

1. PROBLEM STATEMENT
   - What problem does this project solve?
   - Who experiences this problem (target user/customer)?
   - What is the current workaround and why is it inadequate?

2. PRODUCT VISION
   - What does success look like in 1 year?
   - What is the core value proposition in one sentence?
   - What is the product NOT (deliberate exclusions)?

3. TARGET AUDIENCE
   - Primary users (who, demographics, technical level)
   - Secondary users (if any)
   - Key personas (2-3, described in 2-3 sentences each)

4. SUCCESS CRITERIA
   - Top 3-5 measurable KPIs for Year 1
   - Definition of "launch-ready"

5. CONSTRAINTS
   - Timeline (hard deadlines if any)
   - Budget (rough order of magnitude)
   - Technology constraints or preferences
   - Legal/regulatory considerations

6. TEAM COMPOSITION RECOMMENDATION
   Available teams: {json.dumps(TEAM_DESCRIPTIONS, indent=2)}
   - Which teams are needed and why?
   - Any teams that are explicitly NOT needed?

7. RISK IDENTIFICATION
   - Top 3 risks to successful delivery
   - Any known blockers or dependencies on external parties

8. OPEN QUESTIONS
   - What does the Orchestrator need to confirm with the human
     before writing the PRD?

Output the complete Discovery Summary as well-formatted markdown.
This will be reviewed by the human and used to generate the PRD.
""",
        expected_output="Complete Discovery Summary in markdown.",
        agent=orchestrator
    )

    crew = Crew(agents=[orchestrator], tasks=[discovery_task],
                process=Process.sequential, verbose=True)

    print(f"\n🔍 Orchestrator running discovery intake — {project_name}...\n")
    result = crew.kickoff()

    os.makedirs("logs", exist_ok=True)
    discovery_path = f"logs/{context['project_id']}_DISCOVERY.md"
    with open(discovery_path, "w") as f:
        f.write(str(result))

    context["artifacts"].append({
        "name": "Discovery Summary",
        "type": "DISCOVERY",
        "path": discovery_path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "Orchestrator"
    })
    log_event(context, "DISCOVERY_COMPLETE", discovery_path)
    save_context(context)

    notify_human(
        subject=f"Discovery complete — {project_name}",
        message=(
            f"Project ID: {context['project_id']}\n"
            f"Discovery summary: {discovery_path}\n\n"
            f"Please review. The Orchestrator will generate a draft PRD "
            f"once you confirm the discovery summary is accurate."
        )
    )

    # Human approves discovery before PRD generation
    approved = request_human_approval(
        gate_type="PRD",
        artifact_path=discovery_path,
        summary=f"Discovery summary for '{project_name}' — approve to proceed to PRD generation"
    )

    if not approved:
        context["status"] = "DISCOVERY_REJECTED"
        log_event(context, "DISCOVERY_REJECTED", discovery_path)
        save_context(context)
        print("❌ Discovery rejected. Stopping.")
        return context

    # Generate PRD from discovery
    context = run_prd_generation(context, discovery_path)
    return context


# ── Brief Mode ────────────────────────────────────────────────────────────────

def run_brief_intake(project_name: str, prd_path: str,
                     teams: list = None, timeline_weeks: int = 12,
                     budget_usd: float = 50000.0) -> dict:
    """
    Ingest an existing PRD/brief and proceed directly to kickoff.
    Human confirms team selection and repo spin-up before work begins.
    """
    context = create_project_context(project_name, mode="BRIEF")
    orchestrator = build_orchestrator()

    with open(prd_path) as f:
        prd_content = f.read()

    # Classify and recommend teams if not provided
    if not teams:
        classify_task = Task(
            description=f"""
You are the Protean Pursuits Orchestrator.
Review this PRD and recommend which teams are needed.

Available teams: {json.dumps(TEAM_DESCRIPTIONS, indent=2)}

PRD (excerpt):
{prd_content[:3000]}

Output a JSON object with this exact structure:
{{
  "recommended_teams": ["team1", "team2", ...],
  "rationale": {{
    "team1": "one sentence reason",
    "team2": "one sentence reason"
  }},
  "excluded_teams": {{
    "team_name": "one sentence reason for exclusion"
  }}
}}

Output ONLY the JSON object. No preamble, no markdown fences.
""",
            expected_output="JSON object with recommended_teams, rationale, excluded_teams.",
            agent=orchestrator
        )
        crew = Crew(agents=[orchestrator], tasks=[classify_task],
                    process=Process.sequential, verbose=True)
        result = crew.kickoff()
        try:
            recommendation = json.loads(str(result))
            teams = recommendation.get("recommended_teams", ["dev", "marketing"])
            print(f"\n🤖 Orchestrator recommends teams: {teams}")
        except Exception:
            teams = ["dev", "marketing"]
            print(f"⚠️  Could not parse team recommendation. Defaulting to: {teams}")

    # Store PRD in context
    context["artifacts"].append({
        "name": "Product Requirements Document",
        "type": "PRD",
        "path": prd_path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "Human"
    })
    log_event(context, "PRD_INGESTED", prd_path)

    # Human approves team selection and repo spin-up
    approved = request_human_approval(
        gate_type="REPO_SPINUP",
        artifact_path=prd_path,
        summary=(
            f"Proceed with '{project_name}' ({context['project_id']})?\n"
            f"Teams: {', '.join(teams)}\n"
            f"Timeline: {timeline_weeks} weeks | Budget: ${budget_usd:,.2f}"
        )
    )

    if not approved:
        context["status"] = "INTAKE_REJECTED"
        save_context(context)
        print("❌ Intake rejected.")
        return context

    # Spin up project repo
    target_dir = f"projects/{context['project_id']}_{project_name.replace(' ', '_')}"
    context = spinup_project_repo(context, teams, target_dir)

    # Hand off to Project Manager
    context, plan_path = run_project_kickoff(
        context, prd_path, teams, timeline_weeks, budget_usd
    )

    notify_human(
        subject=f"Project active — {project_name}",
        message=(
            f"Project: {project_name} ({context['project_id']})\n"
            f"Teams: {', '.join(teams)}\n"
            f"Timeline: {timeline_weeks} weeks | Budget: ${budget_usd:,.2f}\n"
            f"Project dir: {target_dir}\n"
            f"Kickoff plan: {plan_path}\n\n"
            f"All Team Leads have been briefed. Work has begun."
        )
    )

    return context


# ── PRD generation (from discovery) ──────────────────────────────────────────

def run_prd_generation(context: dict, discovery_path: str) -> dict:
    """Generate a draft PRD from a completed discovery summary."""
    orchestrator = build_orchestrator()

    with open(discovery_path) as f:
        discovery_content = f.read()

    prd_task = Task(
        description=f"""
You are the Protean Pursuits Orchestrator.
Generate a draft Product Requirements Document (PRD) from this discovery summary.

Discovery Summary:
{discovery_content}

Produce a complete PRD with the following sections:
1. Executive Summary (product vision, value proposition, launch target)
2. Scope — In Scope / Out of Scope table, phased if needed
3. User Stories with acceptance criteria (US-01 format)
4. Functional Requirements (FR-01 format)
5. Non-Functional Requirements (performance, security, accessibility)
6. Data model overview (key entities and relationships)
7. External dependencies and integrations
8. Risk register (top 5 risks: probability, impact, mitigation)
9. Pre-development requirements / blockers
10. Pre-launch checklist

Mark the document clearly as DRAFT — PENDING HUMAN APPROVAL.
Output as well-formatted markdown.
""",
        expected_output="Draft PRD in markdown, marked DRAFT.",
        agent=orchestrator
    )

    crew = Crew(agents=[orchestrator], tasks=[prd_task],
                process=Process.sequential, verbose=True)
    print(f"\n📄 Orchestrator generating draft PRD...\n")
    result = crew.kickoff()

    prd_path = f"logs/{context['project_id']}_PRD_DRAFT.md"
    with open(prd_path, "w") as f:
        f.write(str(result))

    context["artifacts"].append({
        "name": "Draft PRD",
        "type": "PRD_DRAFT",
        "path": prd_path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "Orchestrator"
    })
    log_event(context, "PRD_DRAFT_COMPLETE", prd_path)
    save_context(context)

    notify_human(
        subject=f"Draft PRD ready — {context['project_name']}",
        message=f"Draft PRD: {prd_path}\nApprove to proceed with team assignment."
    )

    approved = request_human_approval(
        gate_type="PRD",
        artifact_path=prd_path,
        summary=f"Draft PRD for '{context['project_name']}' — approve to proceed with team spin-up"
    )

    if approved:
        context["status"] = "PRD_APPROVED"
        log_event(context, "PRD_APPROVED", prd_path)
    else:
        context["status"] = "PRD_REJECTED"
        log_event(context, "PRD_REJECTED", prd_path)

    save_context(context)
    return context


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Protean Pursuits — Project Intake")
    parser.add_argument("--mode", choices=["discovery", "brief"], required=True)
    parser.add_argument("--name", type=str, required=True, help="Project name")
    parser.add_argument("--prd", type=str, default=None, help="Path to PRD (brief mode)")
    parser.add_argument("--teams", type=str, default=None,
                        help="Comma-separated team list (brief mode, optional)")
    parser.add_argument("--weeks", type=int, default=12, help="Timeline in weeks")
    parser.add_argument("--budget", type=float, default=50000.0, help="Budget in USD")
    args = parser.parse_args()

    print(f"\n🚀 Protean Pursuits — {args.mode.title()} Intake")
    print(f"   Project: {args.name}")
    print(f"   Started: {datetime.utcnow().isoformat()}\n")

    if args.mode == "discovery":
        context = run_discovery_intake(args.name)
    else:
        if not args.prd:
            print("❌ --prd required for brief mode")
            exit(1)
        teams = args.teams.split(",") if args.teams else None
        context = run_brief_intake(
            args.name, args.prd, teams, args.weeks, args.budget
        )

    print(f"\n✅ Intake complete.")
    print(f"   Project ID: {context['project_id']}")
    print(f"   Status: {context['status']}")
