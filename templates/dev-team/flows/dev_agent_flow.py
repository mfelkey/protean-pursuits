"""
templates/dev-team/flows/dev_agent_flow.py

Dev Team — single-agent direct flow.
Bypasses the Dev Team orchestrator; targets one agent by registry key.

Usage:
    python templates/dev-team/flows/dev_agent_flow.py \\
        --agent technical_architect \\
        --task "Design system architecture for a real-time odds feed service" \\
        --project parallaxedge [--save]
"""

import argparse
import importlib
import logging
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.context_loader import load_context, save_agent_direct_output  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

AGENT_REGISTRY = {
    # Planning
    "product_manager": {
        "module":   "agents.dev.strategy.product_manager",
        "build_fn": "build_product_manager",
        "description": "Product Manager — PRD, user stories, acceptance criteria",
    },
    "business_analyst": {
        "module":   "agents.dev.strategy.business_analyst",
        "build_fn": "build_business_analyst",
        "description": "Business Analyst — BAD, stakeholder map, process flows",
    },
    "scrum_master": {
        "module":   "agents.dev.strategy.scrum_master",
        "build_fn": "build_scrum_master",
        "description": "Scrum Master — Sprint Plan, backlog, story points",
    },
    "technical_architect": {
        "module":   "agents.dev.strategy.technical_architect",
        "build_fn": "build_technical_architect",
        "description": "Technical Architect — TAD, system design, data flows, deployment model",
    },
    "security_reviewer": {
        "module":   "agents.dev.strategy.security_reviewer",
        "build_fn": "build_security_reviewer",
        "description": "Security Reviewer — SRR 🟢/🟡/🔴",
    },
    "ux_designer": {
        "module":   "agents.dev.strategy.ux_designer",
        "build_fn": "build_ux_designer",
        "description": "UX/UI Designer — UXD, every screen and interaction",
    },
    "ux_content_guide": {
        "module":   "agents.dev.strategy.ux_content_guide",
        "build_fn": "build_ux_content_guide",
        "description": "UX Content Guide — UI Content Guide, labels, errors, copy",
    },
    # Build
    "senior_developer": {
        "module":   "agents.dev.build.senior_developer",
        "build_fn": "build_senior_developer",
        "description": "Senior Developer — TIP, technical implementation plan",
    },
    "backend_developer": {
        "module":   "agents.dev.build.backend_developer",
        "build_fn": "build_backend_developer",
        "description": "Backend Developer — BIR, server-side implementation",
    },
    "frontend_developer": {
        "module":   "agents.dev.build.frontend_developer",
        "build_fn": "build_frontend_developer",
        "description": "Frontend Developer — FIR, client-side implementation",
    },
    "dba": {
        "module":   "agents.dev.build.database_administrator",
        "build_fn": "build_database_administrator",
        "description": "Database Administrator — DBAR, schema, queries, indexes",
    },
    "devops_engineer": {
        "module":   "agents.dev.build.devops_engineer",
        "build_fn": "build_devops_engineer",
        "description": "DevOps Engineer — DIR, CI/CD, infra-as-code, secrets management",
    },
    # Quality
    "qa_lead": {
        "module":   "agents.dev.quality.qa_lead",
        "build_fn": "build_qa_lead",
        "description": "QA Lead — MTP, master test plan",
    },
    "test_automation_engineer": {
        "module":   "agents.dev.quality.test_automation_engineer",
        "build_fn": "build_test_automation_engineer",  # VERIFY fn name
        "description": "Test Automation Engineer — TAR, runnable test suite",
    },
    # Docs
    "devex_writer": {
        "module":   "agents.dev.docs.devex_writer",
        "build_fn": "build_devex_writer",
        "description": "DevEx Writer — API docs, README, developer guides",
    },
    "technical_writer": {
        "module":   "agents.dev.docs.technical_writer",
        "build_fn": "build_technical_writer",
        "description": "Technical Writer — user guides, runbooks, release notes, KB articles",
    },
}


def run_agent(agent_key: str, task: str, context: dict, save: bool = False):
    if agent_key not in AGENT_REGISTRY:
        _print_registry()
        sys.exit(f"[dev_agent_flow] ERROR: Unknown agent key '{agent_key}'.")

    entry = AGENT_REGISTRY[agent_key]
    logger.info(f"Dev agent direct: {agent_key} — {entry['description']}")

    try:
        mod = importlib.import_module(entry["module"])
    except ModuleNotFoundError as e:
        sys.exit(
            f"[dev_agent_flow] ERROR: Cannot import '{entry['module']}'.\n"
            f"  VERIFY the module path in AGENT_REGISTRY for key '{agent_key}'.\n"
            f"  Original error: {e}"
        )

    build_fn = getattr(mod, entry["build_fn"], None)
    if build_fn is None:
        sys.exit(
            f"[dev_agent_flow] ERROR: '{entry['build_fn']}' not found in '{entry['module']}'.\n"
            f"  VERIFY the build_fn in AGENT_REGISTRY for key '{agent_key}'."
        )

    from crewai import Crew, Task

    agent = build_fn()
    task_obj = Task(
        description=(
            f"{task}\n\n"
            f"Context:\n{context.get('raw', '') or 'No context provided.'}"
        ),
        expected_output=(
            f"Complete deliverable from {entry['description']}. "
            f"No placeholder code. Every function complete. "
            f"TypeScript for frontend; Python type hints on all signatures."
        ),
        agent=agent,
    )

    crew = Crew(agents=[agent], tasks=[task_obj], verbose=True)
    result = crew.kickoff()
    output_str = str(result)

    print("\n" + "="*60)
    print(f"DEV AGENT DIRECT OUTPUT — {agent_key.upper()}")
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
    print("\nAvailable Dev agents:")
    for key, entry in AGENT_REGISTRY.items():
        print(f"  {key:<30} {entry['description']}")
    print()


def main():
    parser = argparse.ArgumentParser(
        prog="dev_agent_flow.py",
        description="Dev Team — run a single agent directly, bypassing the orchestrator.",
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
