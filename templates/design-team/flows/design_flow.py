"""
flows/design_flow.py

Protean Pursuits — Design Team Flows

Run modes:
  BRIEF       — single agent, on-demand
  UX_SPRINT   — research → wireframe → usability (product feature)
  BRAND_BUILD — brand identity + design system (new product)
  AUDIT       — accessibility + usability audit of existing product
  FULL_DESIGN — all agents, complete design package

Usage:
  python flows/design_flow.py --mode brief --agent ui_design
      --name "PROJECT_NAME_PLACEHOLDER Signal Card Component" --project-id PROJ-TEMPLATE

  python flows/design_flow.py --mode ux_sprint
      --name "PROJECT_NAME_PLACEHOLDER Bet Tracker Feature" --project-id PROJ-TEMPLATE

  python flows/design_flow.py --mode brand_build
      --name "PROJECT_NAME_PLACEHOLDER Brand System" --project-id PROJ-TEMPLATE

  python flows/design_flow.py --mode audit
      --name "PROJECT_NAME_PLACEHOLDER Accessibility Audit" --project-id PROJ-TEMPLATE
"""

import sys
sys.path.insert(0, "/home/mfelkey/design-team")

import os
import json
import argparse
from datetime import datetime
from crewai import Task, Crew, Process
from dotenv import load_dotenv

from agents.orchestrator.orchestrator import (
    build_design_orchestrator, create_design_context,
    save_context, log_event, save_artifact,
    notify_human, request_human_review, DESIGN_INSTRUCTION
)
from agents.ux_research.ux_research_agent import build_ux_research_agent
from agents.wireframing.wireframing_agent import build_wireframing_agent
from agents.ui_design.ui_design_agent import build_ui_design_agent
from agents.brand_identity.brand_identity_agent import build_brand_identity_agent
from agents.motion_animation.motion_agent import build_motion_agent
from agents.design_system.design_system_agent import build_design_system_agent
from agents.accessibility.accessibility_agent import build_accessibility_agent
from agents.usability.usability_agent import build_usability_agent

load_dotenv("config/.env")

AGENT_REGISTRY = {
    "ux_research":    build_ux_research_agent,
    "wireframing":    build_wireframing_agent,
    "ui_design":      build_ui_design_agent,
    "brand_identity": build_brand_identity_agent,
    "motion":         build_motion_agent,
    "design_system":  build_design_system_agent,
    "accessibility":  build_accessibility_agent,
    "usability":      build_usability_agent,
}

OUTPUT_DIRS = {
    "ux_research":    "output/research",
    "wireframing":    "output/specs",
    "ui_design":      "output/specs",
    "brand_identity": "output/assets",
    "motion":         "output/specs",
    "design_system":  "output/systems",
    "accessibility":  "output/specs",
    "usability":      "output/research",
}


def _run_agent(agent_key: str, context: dict, brief: str,
               prior: str = "") -> tuple:
    agent = AGENT_REGISTRY[agent_key]()
    task = Task(
        description=f"""
You are the Protean Pursuits {agent.role}.
Project: {context['project_name']} (ID: {context.get('project_id', 'N/A')})
Design ID: {context['design_id']}

Brief: {brief}

{f"Prior design outputs for context:{chr(10)}{prior}" if prior else ""}

{DESIGN_INSTRUCTION}
""",
        expected_output=f"Complete {agent_key} design output with annotations and open questions.",
        agent=agent
    )
    crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)
    print(f"\n🎨 [{agent_key.upper()}] Running...\n")
    result = str(crew.kickoff())
    path = save_artifact(context, f"{agent_key.upper()} Output", agent_key.upper(),
                         result, OUTPUT_DIRS.get(agent_key, "output/specs"))
    return result, path


def run_brief(context: dict, agent_key: str, brief: str = "") -> dict:
    context["run_mode"] = "BRIEF"
    result, path = _run_agent(agent_key, context, brief or f"Standard {agent_key} output for this project.")
    approved = request_human_review(path, f"{agent_key.upper()} — {context['project_name']}")
    context["status"] = "BRIEF_APPROVED" if approved else "BRIEF_REJECTED"
    log_event(context, context["status"], path)
    save_context(context)
    return context


def run_ux_sprint(context: dict, brief: str = "") -> dict:
    context["run_mode"] = "UX_SPRINT"
    results = {}
    for agent_key in ["ux_research", "wireframing", "usability"]:
        prior = "\n\n".join([f"--- {k.upper()} ---\n{v[:600]}..." for k, v in results.items()])
        result, _ = _run_agent(agent_key, context, brief, prior)
        results[agent_key] = result
    path = list(context["artifacts"])[-1]["path"] if context["artifacts"] else ""
    approved = request_human_review(path, f"UX Sprint — {context['project_name']}")
    context["status"] = "UX_SPRINT_APPROVED" if approved else "UX_SPRINT_REJECTED"
    log_event(context, context["status"])
    save_context(context)
    return context


def run_brand_build(context: dict, brief: str = "") -> dict:
    context["run_mode"] = "BRAND_BUILD"
    results = {}
    for agent_key in ["brand_identity", "design_system", "motion", "accessibility"]:
        prior = "\n\n".join([f"--- {k.upper()} ---\n{v[:600]}..." for k, v in results.items()])
        result, _ = _run_agent(agent_key, context, brief, prior)
        results[agent_key] = result

    # Synthesise brand package
    orch = build_design_orchestrator()
    synth = Task(
        description=f"""
Synthesise these brand design outputs into a Brand Package Cover Document
for {context['project_name']}. Include: brand summary, token index,
component reference table, and implementation priority list.
Outputs: {json.dumps({k: v[:400] for k, v in results.items()}, indent=2)}
{DESIGN_INSTRUCTION}
""",
        expected_output="Brand Package Cover Document.",
        agent=orch
    )
    crew = Crew(agents=[orch], tasks=[synth], process=Process.sequential, verbose=True)
    cover = str(crew.kickoff())
    cover_path = save_artifact(context, "Brand Package Cover", "BRAND_PACKAGE",
                               cover, "output/systems")
    approved = request_human_review(cover_path, f"Brand Build — {context['project_name']}")
    context["status"] = "BRAND_BUILD_APPROVED" if approved else "BRAND_BUILD_REJECTED"
    log_event(context, context["status"], cover_path)
    save_context(context)
    return context


def run_audit(context: dict, brief: str = "") -> dict:
    context["run_mode"] = "AUDIT"
    results = {}
    for agent_key in ["accessibility", "usability"]:
        result, _ = _run_agent(agent_key, context, f"Audit existing product. {brief}")
        results[agent_key] = result
    path = context["artifacts"][-1]["path"] if context["artifacts"] else ""
    approved = request_human_review(path, f"Design Audit — {context['project_name']}")
    context["status"] = "AUDIT_APPROVED" if approved else "AUDIT_REJECTED"
    log_event(context, context["status"])
    save_context(context)
    return context


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Protean Pursuits — Design Team")
    parser.add_argument("--mode", choices=["brief", "ux_sprint", "brand_build", "audit", "full_design"], required=True)
    parser.add_argument("--name", type=str, required=True)
    parser.add_argument("--project-id", type=str, default=None)
    parser.add_argument("--agent", type=str, default=None)
    parser.add_argument("--brief", type=str, default="")
    args = parser.parse_args()

    context = create_design_context(args.name, args.mode.upper(), args.project_id)
    print(f"\n🎨 Protean Pursuits Design Team | {args.mode.upper()} | {args.name}\n")

    if args.mode == "brief":
        if not args.agent:
            print(f"❌ --agent required. Options: {list(AGENT_REGISTRY.keys())}")
            exit(1)
        context = run_brief(context, args.agent, args.brief)
    elif args.mode == "ux_sprint":
        context = run_ux_sprint(context, args.brief)
    elif args.mode == "brand_build":
        context = run_brand_build(context, args.brief)
    elif args.mode == "audit":
        context = run_audit(context, args.brief)

    print(f"\n✅ Done. Design ID: {context['design_id']} | Status: {context['status']}")
