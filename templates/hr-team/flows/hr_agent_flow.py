"""
templates/hr-team/flows/hr_agent_flow.py

HR Team — single-agent direct flow.
Bypasses the HR Orchestrator; targets one specialist agent by registry key.

GUARDRAILS (enforced at flow level — cannot be bypassed):
  - Humans-only workforce model — never recommends replacing a person with AI
  - All outputs carry mandatory cross-team flags: Legal / Finance / Strategy / QA
  - All outputs require human approval before any action affecting a person is taken

Usage:
    python templates/hr-team/flows/hr_agent_flow.py \\
        --agent recruiting_specialist \\
        --task "Draft job description for Senior Python Engineer" \\
        --project parallaxedge [--save]
"""

import argparse
import importlib
import logging
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))
_TEAM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_TEAM_ROOT))

from core.context_loader import load_context, save_agent_direct_output  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# HR guardrail injected into every task description
# ---------------------------------------------------------------------------
_HR_GUARDRAIL = (
    "\n\n--- HR TEAM GUARDRAILS (mandatory — do not omit) ---\n"
    "1. HUMANS-ONLY WORKFORCE MODEL: Never recommend replacing any person with AI.\n"
    "2. CROSS-TEAM FLAGS: Every output must end with mandatory flags for: "
    "Legal / Finance / Strategy / QA.\n"
    "3. HUMAN APPROVAL REQUIRED: All outputs require human approval before any "
    "action affecting a person is taken.\n"
    "---"
)

AGENT_REGISTRY = {
    "recruiting_specialist": {
        "module":   "agents.hr.recruiting.recruiting_agent",
        "build_fn": "build_recruiting_specialist",
        "description": "Recruiting Specialist — job descriptions, candidate pipeline, offer letters",
    },
    "onboarding_specialist": {
        "module":   "agents.hr.onboarding.onboarding_agent",
        "build_fn": "build_onboarding_specialist",
        "description": "Onboarding Specialist — onboarding plans, day-one checklists",
    },
    "performance_comp_specialist": {
        "module":   "agents.hr.performance_comp.performance_comp_agent",
        "build_fn": "build_performance_comp_specialist",
        "description": "Performance & Compensation Specialist — review frameworks, comp analysis",
    },
    "policy_compliance_specialist": {
        "module":   "agents.hr.policy_compliance.policy_compliance_agent",
        "build_fn": "build_policy_compliance_specialist",
        "description": "Policy & Compliance Specialist — HR policies, compliance audits",
    },
    "culture_engagement_specialist": {
        "module":   "agents.hr.culture_engagement.culture_engagement_agent",
        "build_fn": "build_culture_engagement_specialist",
        "description": "Culture & Engagement Specialist — engagement surveys, culture programs",
    },
    "benefits_specialist": {
        "module":   "agents.hr.benefits.benefits_agent",
        "build_fn": "build_benefits_specialist",
        "description": "Benefits Specialist — benefits analysis, total compensation",
    },
}


def run_agent(agent_key: str, task: str, context: dict, save: bool = False):
    if agent_key not in AGENT_REGISTRY:
        _print_registry()
        sys.exit(f"[hr_agent_flow] ERROR: Unknown agent key '{agent_key}'.")

    entry = AGENT_REGISTRY[agent_key]
    logger.info(f"HR agent direct: {agent_key} — {entry['description']}")

    try:
        mod = importlib.import_module(entry["module"])
    except ModuleNotFoundError as e:
        sys.exit(f"[hr_agent_flow] ERROR: Cannot import '{entry['module']}'.\n  Original error: {e}")

    build_fn = getattr(mod, entry["build_fn"], None)
    if build_fn is None:
        sys.exit(f"[hr_agent_flow] ERROR: '{entry['build_fn']}' not found in '{entry['module']}'.")

    from crewai import Crew, Task

    agent = build_fn()
    task_obj = Task(
        description=(
            f"{task}\n\n"
            f"Context:\n{context.get('raw', '') or 'No context provided.'}"
            f"{_HR_GUARDRAIL}"
        ),
        expected_output=(
            f"Complete HR deliverable from {entry['description']}. "
            f"No placeholders. All sections fully populated. "
            f"Must end with CROSS-TEAM FLAGS section (Legal / Finance / Strategy / QA) "
            f"and HUMAN APPROVAL REQUIRED notice."
        ),
        agent=agent,
    )

    crew = Crew(agents=[agent], tasks=[task_obj], verbose=True)
    result = crew.kickoff()
    output_str = str(result)

    print("\n" + "="*60)
    print(f"HR AGENT DIRECT OUTPUT — {agent_key.upper()}")
    print("="*60)
    print(output_str)
    print("="*60 + "\n")

    if save:
        path = save_agent_direct_output(output_str, context.get("project"), agent_key)
        if path:
            logger.info(f"Saved to {path}")
        else:
            logger.warning("--save specified but no --project set. Output not saved.")

    return output_str


def _print_registry():
    print("\nAvailable HR agents:")
    for key, entry in AGENT_REGISTRY.items():
        print(f"  {key:<35} {entry['description']}")
    print()


def main():
    parser = argparse.ArgumentParser(
        prog="hr_agent_flow.py",
        description=(
            "HR Team — single agent direct.\n"
            "All HR guardrails (humans-only, cross-team flags, human approval) "
            "are enforced regardless of which agent is targeted."
        ),
    )
    parser.add_argument("--agent", required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--project", default=None)
    parser.add_argument("--context-file", dest="context_file", default=None)
    parser.add_argument("--context", default=None)
    parser.add_argument("--save", action="store_true", default=False)
    parser.add_argument("--list-agents", action="store_true", default=False)
    args = parser.parse_args()

    if args.list_agents:
        _print_registry()
        sys.exit(0)
    if args.save and not args.project:
        parser.error("--save requires --project.")

    context = load_context(project=args.project, context_file=args.context_file, context_str=args.context)
    run_agent(agent_key=args.agent, task=args.task, context=context, save=args.save)


if __name__ == "__main__":
    main()
