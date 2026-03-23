"""
flows/strategy_flow.py

Protean Pursuits — Strategy Team Flows

Four run modes:
  BRIEF       — on-demand, single agent
  FULL_REPORT — all 11 agents, sequential, full strategy package
  COMPETITIVE — recurring competitive intelligence update
  OKR_CYCLE   — quarterly OKR planning cycle

All outputs require human review before forwarding to the
Protean Pursuits Orchestrator for implementation.

Usage:
  python flows/strategy_flow.py --mode brief --agent competitive_intel
      --scope project --project-id PROJ-TEMPLATE --name "PROJECT_NAME_PLACEHOLDER"

  python flows/strategy_flow.py --mode full_report
      --scope company --name "Protean Pursuits LLC"

  python flows/strategy_flow.py --mode competitive
      --scope project --project-id PROJ-TEMPLATE --name "PROJECT_NAME_PLACEHOLDER"

  python flows/strategy_flow.py --mode okr_cycle --quarter Q3-2026
      --scope company --name "Protean Pursuits LLC"
"""

import sys
sys.path.insert(0, "/home/mfelkey/strategy-team")

import os
import json
import argparse
from datetime import datetime
from crewai import Task, Crew, Process
from dotenv import load_dotenv

from agents.orchestrator.orchestrator import (
    build_strategy_orchestrator, create_strategy_context,
    save_context, log_event, save_artifact,
    notify_human, request_human_review,
    CONFIDENCE_INSTRUCTION, SCOPE_COMPANY, SCOPE_PROJECT
)

from agents.business_model.business_model_agent import build_business_model_agent
from agents.gtm.gtm_agent import build_gtm_agent
from agents.product_strategy.product_strategy_agent import build_product_strategy_agent
from agents.partnership.partnership_agent import build_partnership_agent
from agents.competitive_intel.competitive_intel_agent import build_competitive_intel_agent
from agents.financial_strategy.financial_strategy_agent import build_financial_strategy_agent
from agents.okr_planning.okr_agent import build_okr_agent
from agents.risk_scenario.risk_agent import build_risk_agent
from agents.brand_positioning.brand_agent import build_brand_agent
from agents.talent_org.talent_agent import build_talent_agent
from agents.technology_strategy.tech_strategy_agent import build_tech_strategy_agent

load_dotenv("config/.env")

AGENT_REGISTRY = {
    "business_model":     build_business_model_agent,
    "gtm":                build_gtm_agent,
    "product_strategy":   build_product_strategy_agent,
    "partnership":        build_partnership_agent,
    "competitive_intel":  build_competitive_intel_agent,
    "financial_strategy": build_financial_strategy_agent,
    "okr_planning":       build_okr_agent,
    "risk_scenario":      build_risk_agent,
    "brand_positioning":  build_brand_agent,
    "talent_org":         build_talent_agent,
    "technology_strategy":build_tech_strategy_agent,
}

FULL_REPORT_SEQUENCE = [
    "competitive_intel",
    "business_model",
    "product_strategy",
    "gtm",
    "partnership",
    "financial_strategy",
    "brand_positioning",
    "technology_strategy",
    "talent_org",
    "risk_scenario",
    "okr_planning",
]


def _scope_context(context: dict) -> str:
    if context["scope"] == SCOPE_PROJECT:
        return (
            f"Project: {context['name']} (ID: {context.get('project_id', 'N/A')})\n"
            f"Scope: Project-specific strategy (builds on Protean Pursuits company baseline)\n"
        )
    return (
        f"Company: {context['name']}\n"
        f"Scope: Company-level strategy (applies across all Protean Pursuits projects)\n"
    )


def _run_agent_task(agent_key: str, context: dict,
                    extra_brief: str = "") -> tuple:
    """Run a single agent task and return (result_str, output_path)."""
    agent = AGENT_REGISTRY[agent_key]()
    scope_ctx = _scope_context(context)
    artifact_type = agent_key.upper()
    output_dir = f"output/briefs" if context["run_mode"] == "BRIEF" else f"output/reports"

    task = Task(
        description=f"""
You are the Protean Pursuits {agent.role}.

{scope_ctx}
Strategy ID: {context['strategy_id']}
Run mode: {context['run_mode']}

{extra_brief}

{CONFIDENCE_INSTRUCTION}

Produce a complete {artifact_type} strategy document. Structure your output with:
1. Executive Summary (3-5 sentences, key recommendations only)
2. Situation Analysis (current state, relevant context)
3. Strategic Recommendations (each with confidence level tag)
4. Implementation Considerations (sequencing, dependencies, risks)
5. Success Metrics (how we measure whether this strategy is working)
6. Open Questions (what the human must decide or validate)

Output as well-formatted markdown. Every recommendation must carry a confidence tag.
""",
        expected_output=f"Complete {artifact_type} strategy document in markdown with confidence tags.",
        agent=agent
    )

    crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)
    print(f"\n🧠 [{artifact_type}] Running {agent.role}...\n")
    result = crew.kickoff()
    result_str = str(result)

    path = save_artifact(context, f"{artifact_type} Strategy", artifact_type,
                         result_str, output_dir)
    return result_str, path


# ── Mode: BRIEF ───────────────────────────────────────────────────────────────

def run_brief(context: dict, agent_key: str, brief: str = "") -> dict:
    context["run_mode"] = "BRIEF"
    log_event(context, "BRIEF_STARTED", agent_key)

    if agent_key not in AGENT_REGISTRY:
        print(f"❌ Unknown agent: {agent_key}. Available: {list(AGENT_REGISTRY.keys())}")
        return context

    result_str, path = _run_agent_task(agent_key, context, brief)

    approved = request_human_review(
        artifact_path=path,
        summary=f"{agent_key.upper()} brief — {context['name']}",
        run_mode="BRIEF"
    )

    status = "APPROVED" if approved else "REJECTED"
    for a in context["artifacts"]:
        if a["path"] == path:
            a["status"] = status

    context["status"] = f"BRIEF_{status}"
    log_event(context, f"BRIEF_{status}", path)
    save_context(context)

    if approved:
        notify_human(
            subject=f"Strategy brief approved — forwarding to Orchestrator",
            message=(
                f"Brief: {agent_key.upper()}\n"
                f"Project/Company: {context['name']}\n"
                f"Artifact: {path}\n\n"
                f"This brief has been approved and is ready for the "
                f"Protean Pursuits Orchestrator to action."
            )
        )

    return context


# ── Mode: FULL_REPORT ─────────────────────────────────────────────────────────

def run_full_report(context: dict, brief: str = "") -> dict:
    context["run_mode"] = "FULL_REPORT"
    log_event(context, "FULL_REPORT_STARTED")

    notify_human(
        subject=f"Full Strategy Report started — {context['name']}",
        message=(
            f"Strategy ID: {context['strategy_id']}\n"
            f"Scope: {context['scope']}\n"
            f"Agents: {len(FULL_REPORT_SEQUENCE)}\n"
            f"Sequence: {' → '.join(FULL_REPORT_SEQUENCE)}\n\n"
            f"Each agent will run sequentially. You will receive a single "
            f"review request when the full report is complete."
        )
    )

    results = {}
    for agent_key in FULL_REPORT_SEQUENCE:
        # Build cumulative context from prior outputs for each agent
        prior_context = ""
        if results:
            prior_context = "PRIOR STRATEGY OUTPUTS (for context and consistency):\n"
            for k, v in results.items():
                prior_context += f"\n--- {k.upper()} SUMMARY ---\n{v[:800]}...\n"

        result_str, path = _run_agent_task(agent_key, context,
                                            brief + "\n\n" + prior_context)
        results[agent_key] = result_str

    # Synthesise into a cover document
    orchestrator = build_strategy_orchestrator()
    synth_task = Task(
        description=f"""
You are the Strategy Team Orchestrator for Protean Pursuits.
Synthesise the following 11 strategy outputs into a single Executive Strategy Summary.

{_scope_context(context)}

Outputs to synthesise:
{json.dumps({k: v[:600] for k, v in results.items()}, indent=2)}

Produce:
1. ONE-PAGE EXECUTIVE SUMMARY
   - Top 3 strategic priorities (with confidence levels)
   - Top 3 risks (with confidence levels)
   - Recommended next actions for human review

2. CROSS-STRATEGY CONSISTENCY CHECK
   - Any conflicts or tensions between agent outputs
   - Recommendations for resolution

3. FORWARDING MEMO TO PROTEAN PURSUITS ORCHESTRATOR
   - What this strategy package authorises the Orchestrator to action
   - What requires further human decision before actioning
   - Sequencing recommendation (what to implement first)

{CONFIDENCE_INSTRUCTION}
""",
        expected_output="Executive Strategy Summary with consistency check and forwarding memo.",
        agent=orchestrator
    )

    crew = Crew(agents=[orchestrator], tasks=[synth_task],
                process=Process.sequential, verbose=True)
    synthesis = str(crew.kickoff())
    synth_path = save_artifact(context, "Executive Strategy Summary",
                               "EXEC_SUMMARY", synthesis, "output/reports")

    # Single human review for the full package
    approved = request_human_review(
        artifact_path=synth_path,
        summary=f"Full Strategy Report — {context['name']} ({len(FULL_REPORT_SEQUENCE)} agents)",
        run_mode="FULL_REPORT"
    )

    status = "APPROVED" if approved else "REJECTED"
    context["status"] = f"FULL_REPORT_{status}"
    log_event(context, f"FULL_REPORT_{status}", synth_path)
    save_context(context)
    return context


# ── Mode: COMPETITIVE ─────────────────────────────────────────────────────────

def run_competitive_update(context: dict, focus: str = "") -> dict:
    context["run_mode"] = "COMPETITIVE"
    log_event(context, "COMPETITIVE_UPDATE_STARTED")

    result_str, path = _run_agent_task(
        "competitive_intel", context,
        f"This is a recurring competitive intelligence update.\n"
        f"Focus areas: {focus if focus else 'full landscape scan'}\n"
        f"Produce: new developments since last update, threat level changes, "
        f"and updated strategic implications. Flag anything requiring immediate attention."
    )

    approved = request_human_review(
        artifact_path=path,
        summary=f"Competitive Intelligence Update — {context['name']}",
        run_mode="COMPETITIVE"
    )

    context["status"] = "COMPETITIVE_APPROVED" if approved else "COMPETITIVE_REJECTED"
    log_event(context, context["status"], path)
    save_context(context)
    return context


# ── Mode: OKR_CYCLE ───────────────────────────────────────────────────────────

def run_okr_cycle(context: dict, quarter: str,
                  prior_okr_path: str = None) -> dict:
    context["run_mode"] = "OKR_CYCLE"
    log_event(context, "OKR_CYCLE_STARTED", quarter)

    prior_okr = ""
    if prior_okr_path and os.path.exists(prior_okr_path):
        with open(prior_okr_path) as f:
            prior_okr = f.read()[:2000]

    result_str, path = _run_agent_task(
        "okr_planning", context,
        f"Quarter: {quarter}\n"
        f"Prior quarter OKRs (for continuity and retrospective):\n{prior_okr}\n\n"
        f"Produce: {quarter} OKR set at {'company' if context['scope'] == SCOPE_COMPANY else 'project'} "
        f"level. Include retrospective on prior quarter if prior OKRs provided. "
        f"Flag any OKR that is an output metric rather than an outcome metric."
    )

    approved = request_human_review(
        artifact_path=path,
        summary=f"{quarter} OKR Cycle — {context['name']}",
        run_mode="OKR_CYCLE"
    )

    context["status"] = "OKR_APPROVED" if approved else "OKR_REJECTED"
    log_event(context, context["status"], path)
    save_context(context)
    return context


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Protean Pursuits — Strategy Team")
    parser.add_argument("--mode", choices=["brief", "full_report", "competitive", "okr_cycle"],
                        required=True)
    parser.add_argument("--name", type=str, required=True,
                        help="Company or project name")
    parser.add_argument("--scope", choices=["company", "project"], default="company")
    parser.add_argument("--project-id", type=str, default=None)
    parser.add_argument("--agent", type=str, default=None,
                        help="Agent key for brief mode")
    parser.add_argument("--brief", type=str, default="",
                        help="Additional context or focus for the run")
    parser.add_argument("--quarter", type=str, default=None,
                        help="Quarter for OKR cycle (e.g. Q3-2026)")
    parser.add_argument("--prior-okr", type=str, default=None,
                        help="Path to prior quarter OKR file")
    args = parser.parse_args()

    scope = SCOPE_PROJECT if args.scope == "project" else SCOPE_COMPANY
    context = create_strategy_context(args.name, scope, args.project_id)

    print(f"\n🧠 Protean Pursuits Strategy Team")
    print(f"   Mode: {args.mode.upper()}")
    print(f"   Scope: {scope}")
    print(f"   Name: {args.name}")
    print(f"   Started: {datetime.utcnow().isoformat()}\n")

    if args.mode == "brief":
        if not args.agent:
            print(f"❌ --agent required for brief mode. Options: {list(AGENT_REGISTRY.keys())}")
            exit(1)
        context = run_brief(context, args.agent, args.brief)

    elif args.mode == "full_report":
        context = run_full_report(context, args.brief)

    elif args.mode == "competitive":
        context = run_competitive_update(context, args.brief)

    elif args.mode == "okr_cycle":
        if not args.quarter:
            print("❌ --quarter required for okr_cycle mode (e.g. Q3-2026)")
            exit(1)
        context = run_okr_cycle(context, args.quarter, args.prior_okr)

    print(f"\n✅ Strategy Team run complete.")
    print(f"   Strategy ID: {context['strategy_id']}")
    print(f"   Status: {context['status']}")
    print(f"   Artifacts: {len(context['artifacts'])}")
