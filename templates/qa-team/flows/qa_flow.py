"""
templates/qa-team/flows/qa_flow.py

QA Team (Standalone) — orchestrated flow.
Cross-team QA crew — can audit any team's deliverables.

Run modes:
    functional          Functional Testing Specialist
    performance         Performance Testing Specialist
    security            Security Testing Specialist  (🟢/🟡/🔴 rating)
    accessibility       Accessibility Auditor
    data_quality        Data Quality Analyst
    legal_review        Legal Completeness Reviewer
    marketing_review    Marketing Compliance Reviewer
    test_cases          Test Case Developer
    full                All agents in sequence

HITL gate: QA_SIGN_OFF
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, "/home/mfelkey/qa-team")

from core.context_loader import load_context, save_output  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

TEAM = "qa"


def _notify(title, message):
    try:
        from core.notifications import send_pushover
        send_pushover(title=title, message=message)
    except Exception as e:
        logger.warning(f"Pushover notification failed: {e}")


def _load_agents(keys):
    from agents.orchestrator.orchestrator import build_qa_orchestrator
    from agents.functional_testing.functional_agent import build_functional_testing_specialist
    from agents.performance_testing.performance_agent import build_performance_testing_specialist
    from agents.security_testing.security_agent import build_security_testing_specialist
    from agents.accessibility_audit.accessibility_audit_agent import build_accessibility_auditor
    from agents.data_quality.data_quality_agent import build_data_quality_analyst
    from agents.legal_completeness.legal_qa_agent import build_legal_completeness_reviewer
    from agents.marketing_compliance.marketing_qa_agent import build_marketing_compliance_reviewer
    from agents.test_case_development.test_case_agent import build_test_case_developer

    builders = {
        "orchestrator":                    build_qa_orchestrator,
        "functional_testing_specialist":   build_functional_testing_specialist,
        "performance_testing_specialist":  build_performance_testing_specialist,
        "security_testing_specialist":     build_security_testing_specialist,
        "accessibility_auditor":           build_accessibility_auditor,
        "data_quality_analyst":            build_data_quality_analyst,
        "legal_completeness_reviewer":     build_legal_completeness_reviewer,
        "marketing_compliance_reviewer":   build_marketing_compliance_reviewer,
        "test_case_developer":             build_test_case_developer,
    }
    return {k: builders[k]() for k in keys if k in builders}


def _run_mode(mode, agent_keys, task, context, save):
    from crewai import Crew, Task

    agents = _load_agents(agent_keys)
    agent_list = list(agents.values())
    context_block = context.get("raw", "") or "No context provided."

    tasks = []
    for i, (key, agent) in enumerate(agents.items()):
        prefix = "" if i == 0 else "Use the output of the previous task as input context.\n\n"
        tasks.append(Task(
            description=f"{prefix}{task}\n\nProject context:\n{context_block}",
            expected_output=(
                f"Complete QA deliverable from {key.replace('_', ' ')}. "
                f"No placeholders. Ends with QA_SIGN_OFF gate summary."
            ),
            agent=agent,
        ))

    crew = Crew(agents=agent_list, tasks=tasks, verbose=True)
    _notify(f"PP QA — {mode}", f"Starting: {task[:80]}")

    result = crew.kickoff()
    output_str = str(result)

    print("\n" + "="*60)
    print(f"QA TEAM OUTPUT — {mode.upper()}")
    print("="*60)
    print(output_str)
    print("="*60 + "\n")

    if save:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = save_output(output_str, context.get("project"), TEAM, f"{mode}_{timestamp}.md")
        if path:
            logger.info(f"Saved to {path}")

    _notify(f"PP QA — {mode} complete", f"Project: {context.get('project') or 'ad-hoc'}")
    return output_str


def run_functional(context, task, save=False):
    return _run_mode("functional", ["functional_testing_specialist"], task, context, save)

def run_performance(context, task, save=False):
    return _run_mode("performance", ["performance_testing_specialist"], task, context, save)

def run_security(context, task, save=False):
    return _run_mode("security", ["security_testing_specialist"], task, context, save)

def run_accessibility(context, task, save=False):
    return _run_mode("accessibility", ["accessibility_auditor"], task, context, save)

def run_data_quality(context, task, save=False):
    return _run_mode("data_quality", ["data_quality_analyst"], task, context, save)

def run_legal_review(context, task, save=False):
    return _run_mode("legal_review", ["legal_completeness_reviewer"], task, context, save)

def run_marketing_review(context, task, save=False):
    return _run_mode("marketing_review", ["marketing_compliance_reviewer"], task, context, save)

def run_test_cases(context, task, save=False):
    return _run_mode("test_cases", ["test_case_developer"], task, context, save)

def run_full(context, task, save=False):
    return _run_mode("full", [
        "orchestrator", "functional_testing_specialist", "performance_testing_specialist",
        "security_testing_specialist", "accessibility_auditor", "data_quality_analyst",
        "legal_completeness_reviewer", "marketing_compliance_reviewer", "test_case_developer",
    ], task, context, save)


MODES = [
    "functional", "performance", "security", "accessibility",
    "data_quality", "legal_review", "marketing_review", "test_cases", "full",
]


def main():
    parser = argparse.ArgumentParser(prog="qa_flow.py", description="QA Team (Standalone) flow.")
    parser.add_argument("--mode", required=True, choices=MODES)
    parser.add_argument("--task", required=True)
    parser.add_argument("--project", default=None)
    parser.add_argument("--context-file", dest="context_file", default=None)
    parser.add_argument("--context", default=None)
    parser.add_argument("--save", action="store_true", default=False)
    args = parser.parse_args()

    if args.save and not args.project:
        parser.error("--save requires --project.")

    context = load_context(project=args.project, context_file=args.context_file, context_str=args.context)
    globals()[f"run_{args.mode}"](context=context, task=args.task, save=args.save)


if __name__ == "__main__":
    main()
