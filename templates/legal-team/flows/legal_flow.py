"""
templates/legal-team/flows/legal_flow.py

Legal Team — orchestrated flow.

Run modes:
    contract      Contract Drafter
    review        Document Reviewer
    ip            IP & Licensing Specialist
    privacy       Privacy & Data Counsel
    regulatory    Regulatory Compliance Specialist
    employment    Employment & Contractor Counsel
    corporate     Corporate Entity Specialist
    dispute       Litigation & Dispute Specialist
    full          All agents in sequence

HITL gate: LEGAL_REVIEW
Authorized SME caller — may invoke the SME Group.

Usage:
    python templates/legal-team/flows/legal_flow.py \\
        --mode privacy --project parallaxedge \\
        --task "GDPR and CCPA assessment for user data collection"
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))

from core.context_loader import load_context, save_output  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

TEAM = "legal"


def _notify(title, message):
    try:
        from core.notifications import send_pushover
        send_pushover(title=title, message=message)
    except Exception as e:
        logger.warning(f"Pushover notification failed: {e}")


def _load_agents(keys: list):
    from agents.orchestrator.orchestrator import build_legal_orchestrator
    from agents.contract_drafting.contract_agent import build_contract_drafter
    from agents.document_review.review_agent import build_document_reviewer
    from agents.corporate_entity.corporate_agent import build_corporate_entity_specialist
    from agents.ip_licensing.ip_agent import build_ip_licensing_specialist
    from agents.privacy_data.privacy_agent import build_privacy_data_counsel
    from agents.regulatory_compliance.compliance_agent import build_regulatory_compliance_specialist
    from agents.employment_contractor.employment_agent import build_employment_contractor_counsel
    from agents.litigation_dispute.litigation_agent import build_litigation_dispute_specialist

    builders = {
        "orchestrator":                    build_legal_orchestrator,
        "contract_drafter":               build_contract_drafter,
        "document_reviewer":              build_document_reviewer,
        "corporate_entity_specialist":    build_corporate_entity_specialist,
        "ip_licensing_specialist":        build_ip_licensing_specialist,
        "privacy_data_counsel":           build_privacy_data_counsel,
        "regulatory_compliance_specialist": build_regulatory_compliance_specialist,
        "employment_contractor_counsel":  build_employment_contractor_counsel,
        "litigation_dispute_specialist":  build_litigation_dispute_specialist,
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
                f"Complete legal deliverable from {key.replace('_', ' ')}. "
                f"No placeholders. All sections fully populated. "
                f"Ends with LEGAL_REVIEW gate summary."
            ),
            agent=agent,
        ))

    crew = Crew(agents=agent_list, tasks=tasks, verbose=True)
    _notify(f"PP Legal — {mode}", f"Starting: {task[:80]}")

    result = crew.kickoff()
    output_str = str(result)

    print("\n" + "="*60)
    print(f"LEGAL TEAM OUTPUT — {mode.upper()}")
    print("="*60)
    print(output_str)
    print("="*60 + "\n")

    if save:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = save_output(output_str, context.get("project"), TEAM, f"{mode}_{timestamp}.md")
        if path:
            logger.info(f"Saved to {path}")

    _notify(f"PP Legal — {mode} complete", f"Project: {context.get('project') or 'ad-hoc'}")
    return output_str


def run_contract(context, task, save=False):
    return _run_mode("contract", ["contract_drafter"], task, context, save)

def run_review(context, task, save=False):
    return _run_mode("review", ["document_reviewer"], task, context, save)

def run_ip(context, task, save=False):
    return _run_mode("ip", ["ip_licensing_specialist"], task, context, save)

def run_privacy(context, task, save=False):
    return _run_mode("privacy", ["privacy_data_counsel"], task, context, save)

def run_regulatory(context, task, save=False):
    return _run_mode("regulatory", ["regulatory_compliance_specialist"], task, context, save)

def run_employment(context, task, save=False):
    return _run_mode("employment", ["employment_contractor_counsel"], task, context, save)

def run_corporate(context, task, save=False):
    return _run_mode("corporate", ["corporate_entity_specialist"], task, context, save)

def run_dispute(context, task, save=False):
    return _run_mode("dispute", ["litigation_dispute_specialist"], task, context, save)

def run_full(context, task, save=False):
    return _run_mode("full", [
        "orchestrator", "contract_drafter", "document_reviewer",
        "corporate_entity_specialist", "ip_licensing_specialist",
        "privacy_data_counsel", "regulatory_compliance_specialist",
        "employment_contractor_counsel", "litigation_dispute_specialist",
    ], task, context, save)


MODES = ["contract", "review", "ip", "privacy", "regulatory", "employment", "corporate", "dispute", "full"]


def main():
    parser = argparse.ArgumentParser(prog="legal_flow.py", description="Legal Team flow.")
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
