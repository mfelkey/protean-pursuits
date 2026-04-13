"""
templates/qa-team/flows/qa_agent_flow.py

QA Team — single-agent direct flow.
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

AGENT_REGISTRY = {
    "functional_testing_specialist": {
        "module":   "agents.functional_testing.functional_agent",
        "build_fn": "build_functional_testing_specialist",
        "description": "Functional Testing Specialist — functional test results, bug reports",
    },
    "performance_testing_specialist": {
        "module":   "agents.performance_testing.performance_agent",
        "build_fn": "build_performance_testing_specialist",
        "description": "Performance Testing Specialist — benchmarks, bottleneck analysis",
    },
    "security_testing_specialist": {
        "module":   "agents.security_testing.security_agent",
        "build_fn": "build_security_testing_specialist",
        "description": "Security Testing Specialist — security test report 🟢/🟡/🔴",
    },
    "accessibility_auditor": {
        "module":   "agents.accessibility_audit.accessibility_audit_agent",
        "build_fn": "build_accessibility_auditor",
        "description": "Accessibility Auditor — WCAG 2.1 AA audit",
    },
    "data_quality_analyst": {
        "module":   "agents.data_quality.data_quality_agent",
        "build_fn": "build_data_quality_analyst",
        "description": "Data Quality Analyst — data quality scorecard",
    },
    "legal_completeness_reviewer": {
        "module":   "agents.legal_completeness.legal_qa_agent",
        "build_fn": "build_legal_completeness_reviewer",
        "description": "Legal Completeness Reviewer — legal completeness report",
    },
    "marketing_compliance_reviewer": {
        "module":   "agents.marketing_compliance.marketing_qa_agent",
        "build_fn": "build_marketing_compliance_reviewer",
        "description": "Marketing Compliance Reviewer — marketing compliance report",
    },
    "test_case_developer": {
        "module":   "agents.test_case_development.test_case_agent",
        "build_fn": "build_test_case_developer",
        "description": "Test Case Developer — test case library",
    },
}


def run_agent(agent_key: str, task: str, context: dict, save: bool = False):
    if agent_key not in AGENT_REGISTRY:
        _print_registry()
        sys.exit(f"[qa_agent_flow] ERROR: Unknown agent key '{agent_key}'.")

    entry = AGENT_REGISTRY[agent_key]
    logger.info(f"QA agent direct: {agent_key}")

    try:
        mod = importlib.import_module(entry["module"])
    except ModuleNotFoundError as e:
        sys.exit(f"[qa_agent_flow] ERROR: Cannot import '{entry['module']}'.\n  Original error: {e}")

    build_fn = getattr(mod, entry["build_fn"], None)
    if build_fn is None:
        sys.exit(f"[qa_agent_flow] ERROR: '{entry['build_fn']}' not found in '{entry['module']}'.")

    from crewai import Crew, Task

    agent = build_fn()
    task_obj = Task(
        description=f"{task}\n\nContext:\n{context.get('raw', '') or 'No context provided.'}",
        expected_output=f"Complete deliverable from {entry['description']}. No placeholders.",
        agent=agent,
    )

    crew = Crew(agents=[agent], tasks=[task_obj], verbose=True)
    result = crew.kickoff()
    output_str = str(result)

    print("\n" + "="*60)
    print(f"QA AGENT DIRECT OUTPUT — {agent_key.upper()}")
    print("="*60)
    print(output_str)
    print("="*60 + "\n")

    if save:
        path = save_agent_direct_output(output_str, context.get("project"), agent_key)
        if path:
            logger.info(f"Saved to {path}")

    return output_str


def _print_registry():
    print("\nAvailable QA agents:")
    for key, entry in AGENT_REGISTRY.items():
        print(f"  {key:<35} {entry['description']}")
    print()


def main():
    parser = argparse.ArgumentParser(prog="qa_agent_flow.py", description="QA Team — single agent direct.")
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
