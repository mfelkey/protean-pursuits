"""
flows/hr_flow.py

Protean Pursuits — HR Team Flows

Run modes:
  RECRUIT      — end-to-end hiring process for a role or team
  ONBOARD      — new hire onboarding plan for an individual or cohort
  REVIEW       — performance review cycle or individual review support
  POLICY       — draft or update an HR policy or handbook section
  CULTURE      — culture health check or engagement initiative
  BENEFITS     — benefits design or review
  FULL_CYCLE   — all agents, complete HR package for a project/initiative

Humans only: all recommendations assume a human workforce.
All outputs require human approval before any action affecting a person is taken.

Usage:
  python flows/hr_flow.py --mode recruit
      --name "Senior Backend Engineer" --project-id PROJ-TEMPLATE
      --brief "Python/FastAPI, 8+ years, remote-first, IC track"

  python flows/hr_flow.py --mode onboard
      --name "Q1 2026 Engineering Cohort" --project-id PROJ-TEMPLATE

  python flows/hr_flow.py --mode review
      --name "H1 2026 Performance Cycle" --project-id PROJ-TEMPLATE

  python flows/hr_flow.py --mode policy --agent policy_compliance
      --name "Remote Work Policy Update" --project-id PROJ-TEMPLATE

  python flows/hr_flow.py --mode culture
      --name "Q2 Engagement Survey" --project-id PROJ-TEMPLATE

  python flows/hr_flow.py --mode benefits
      --name "2026 Benefits Refresh" --project-id PROJ-TEMPLATE

  python flows/hr_flow.py --mode full_cycle
      --name "PROJECT_NAME_PLACEHOLDER People Package" --project-id PROJ-TEMPLATE
"""

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))

import os
import json
import argparse
from datetime import datetime
from crewai import Task, Crew, Process
from dotenv import load_dotenv

from agents.hr.orchestrator.orchestrator import (
    build_hr_orchestrator, create_hr_context,
    save_context, log_event, save_artifact,
    notify_human, request_human_review, HR_INSTRUCTION
)
from agents.hr.recruiting.recruiting_agent         import build_recruiting_agent
from agents.hr.onboarding.onboarding_agent         import build_onboarding_agent
from agents.hr.performance_comp.performance_comp_agent import build_performance_comp_agent
from agents.hr.policy_compliance.policy_compliance_agent import build_policy_compliance_agent
from agents.hr.culture_engagement.culture_engagement_agent import build_culture_engagement_agent
from agents.hr.benefits.benefits_agent             import build_benefits_agent

load_dotenv("config/.env")

# ── Agent registry ─────────────────────────────────────────────────────────────

AGENT_REGISTRY = {
    "recruiting":         build_recruiting_agent,
    "onboarding":         build_onboarding_agent,
    "performance_comp":   build_performance_comp_agent,
    "policy_compliance":  build_policy_compliance_agent,
    "culture_engagement": build_culture_engagement_agent,
    "benefits":           build_benefits_agent,
}

OUTPUT_DIRS = {
    "recruiting":         "output/recruiting",
    "onboarding":         "output/onboarding",
    "performance_comp":   "output/reports",
    "policy_compliance":  "output/policies",
    "culture_engagement": "output/reports",
    "benefits":           "output/policies",
}


# ── Core runner ────────────────────────────────────────────────────────────────

def _run_agent(agent_key: str, context: dict, brief: str,
               prior: str = "") -> tuple:
    agent = AGENT_REGISTRY[agent_key]()
    task  = Task(
        description=f"""
You are the Protean Pursuits {agent.role}.
Project: {context['project_name']} (ID: {context.get('project_id', 'N/A')})
HR ID: {context['hr_id']}

Brief: {brief}

{f"Prior HR outputs for context:{chr(10)}{prior}" if prior else ""}

{HR_INSTRUCTION}
""",
        expected_output=(
            f"Complete {agent_key} HR output ending with "
            f"CROSS-TEAM FLAGS and OPEN QUESTIONS sections."
        ),
        agent=agent
    )
    crew   = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)
    print(f"\n👥 [{agent_key.upper()}] Running...\n")
    result = str(crew.kickoff())
    path   = save_artifact(
        context, f"{agent_key.upper()} Output", agent_key.upper(),
        result, OUTPUT_DIRS.get(agent_key, "output/reports")
    )
    return result, path


# ── Run modes ──────────────────────────────────────────────────────────────────

def run_recruit(context: dict, brief: str = "") -> dict:
    """Recruiting only — job description, sourcing plan, interview guide, offer template."""
    context["run_mode"] = "RECRUIT"
    result, path = _run_agent(
        "recruiting", context,
        brief or f"Full recruiting package for: {context['project_name']}"
    )
    approved = request_human_review(path, f"Recruiting — {context['project_name']}")
    context["status"] = "RECRUIT_APPROVED" if approved else "RECRUIT_REJECTED"
    log_event(context, context["status"], path)
    save_context(context)
    return context


def run_onboard(context: dict, brief: str = "") -> dict:
    """Onboarding plan — pre-day-1 through 90 days."""
    context["run_mode"] = "ONBOARD"
    result, path = _run_agent(
        "onboarding", context,
        brief or f"Complete onboarding plan for: {context['project_name']}"
    )
    approved = request_human_review(path, f"Onboarding — {context['project_name']}")
    context["status"] = "ONBOARD_APPROVED" if approved else "ONBOARD_REJECTED"
    log_event(context, context["status"], path)
    save_context(context)
    return context


def run_review(context: dict, brief: str = "") -> dict:
    """Performance review framework — review templates, calibration guide, comp cycle."""
    context["run_mode"] = "REVIEW"
    result, path = _run_agent(
        "performance_comp", context,
        brief or f"Performance review cycle support for: {context['project_name']}"
    )
    approved = request_human_review(path, f"Performance Review — {context['project_name']}")
    context["status"] = "REVIEW_APPROVED" if approved else "REVIEW_REJECTED"
    log_event(context, context["status"], path)
    save_context(context)
    return context


def run_policy(context: dict, agent_key: str = "policy_compliance",
               brief: str = "") -> dict:
    """Draft or update an HR policy. Defaults to policy_compliance agent."""
    if agent_key not in AGENT_REGISTRY:
        print(f"❌ Unknown agent '{agent_key}'. Options: {list(AGENT_REGISTRY.keys())}")
        return context
    context["run_mode"] = "POLICY"
    result, path = _run_agent(
        agent_key, context,
        brief or f"Draft HR policy for: {context['project_name']}"
    )
    approved = request_human_review(path, f"Policy — {context['project_name']}")
    context["status"] = "POLICY_APPROVED" if approved else "POLICY_REJECTED"
    log_event(context, context["status"], path)
    save_context(context)
    return context


def run_culture(context: dict, brief: str = "") -> dict:
    """Culture health check or engagement initiative."""
    context["run_mode"] = "CULTURE"
    result, path = _run_agent(
        "culture_engagement", context,
        brief or f"Culture & engagement initiative for: {context['project_name']}"
    )
    approved = request_human_review(path, f"Culture — {context['project_name']}")
    context["status"] = "CULTURE_APPROVED" if approved else "CULTURE_REJECTED"
    log_event(context, context["status"], path)
    save_context(context)
    return context


def run_benefits(context: dict, brief: str = "") -> dict:
    """Benefits design or review."""
    context["run_mode"] = "BENEFITS"
    result, path = _run_agent(
        "benefits", context,
        brief or f"Benefits programme design for: {context['project_name']}"
    )
    approved = request_human_review(path, f"Benefits — {context['project_name']}")
    context["status"] = "BENEFITS_APPROVED" if approved else "BENEFITS_REJECTED"
    log_event(context, context["status"], path)
    save_context(context)
    return context


def run_full_cycle(context: dict, brief: str = "") -> dict:
    """
    All six agents in sequence, then orchestrator synthesises a People Package.
    Sequence: recruiting → onboarding → performance_comp → policy_compliance
              → culture_engagement → benefits → synthesis
    """
    context["run_mode"] = "FULL_CYCLE"
    sequence = [
        "recruiting", "onboarding", "performance_comp",
        "policy_compliance", "culture_engagement", "benefits"
    ]
    results = {}
    for agent_key in sequence:
        prior = "\n\n".join(
            [f"--- {k.upper()} ---\n{v[:500]}..." for k, v in results.items()]
        )
        result, _ = _run_agent(agent_key, context, brief, prior)
        results[agent_key] = result

    # Orchestrator synthesis — People Package cover document
    orch  = build_hr_orchestrator()
    synth = Task(
        description=f"""
Synthesise these HR specialist outputs into a People Package Cover Document
for {context['project_name']}.

Include:
- Executive summary of all HR workstreams
- Cross-team flags consolidated from all agents (Legal / Finance / Strategy / QA)
- Open items requiring human decisions before any action is taken
- Recommended sequencing: what to action first, second, third
- ⚠️ REQUIRES HUMAN APPROVAL items consolidated list

Specialist outputs:
{json.dumps({k: v[:400] for k, v in results.items()}, indent=2)}

{HR_INSTRUCTION}
""",
        expected_output="People Package Cover Document in markdown.",
        agent=orch
    )
    crew  = Crew(agents=[orch], tasks=[synth], process=Process.sequential, verbose=True)
    cover = str(crew.kickoff())
    cover_path = save_artifact(
        context, "People Package Cover", "PEOPLE_PACKAGE",
        cover, "output/reports"
    )

    approved = request_human_review(cover_path, f"Full HR Cycle — {context['project_name']}")
    context["status"] = "FULL_CYCLE_APPROVED" if approved else "FULL_CYCLE_REJECTED"
    log_event(context, context["status"], cover_path)
    save_context(context)
    return context


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Protean Pursuits — HR Team")
    parser.add_argument(
        "--mode",
        choices=["recruit", "onboard", "review", "policy",
                 "culture", "benefits", "full_cycle"],
        required=True
    )
    parser.add_argument("--name",       type=str, required=True,
                        help="Role name, cohort name, or initiative name")
    parser.add_argument("--project-id", type=str, default=None)
    parser.add_argument("--agent",      type=str, default=None,
                        help="Specific agent key (used with --mode policy)")
    parser.add_argument("--brief",      type=str, default="",
                        help="Additional context for the agents")
    args = parser.parse_args()

    context = create_hr_context(args.name, args.mode.upper(), args.project_id)
    print(f"\n👥 Protean Pursuits HR Team | {args.mode.upper()} | {args.name}\n")

    dispatch = {
        "recruit":    lambda: run_recruit(context, args.brief),
        "onboard":    lambda: run_onboard(context, args.brief),
        "review":     lambda: run_review(context, args.brief),
        "policy":     lambda: run_policy(context, args.agent or "policy_compliance", args.brief),
        "culture":    lambda: run_culture(context, args.brief),
        "benefits":   lambda: run_benefits(context, args.brief),
        "full_cycle": lambda: run_full_cycle(context, args.brief),
    }

    context = dispatch[args.mode]()
    print(f"\n✅ Done. HR ID: {context['hr_id']} | Status: {context['status']}")
