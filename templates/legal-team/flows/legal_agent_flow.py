"""
templates/legal-team/flows/legal_agent_flow.py

Legal Team — single-agent direct flow.
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
    "contract_drafter": {
        "module":   "agents.contract_drafting.contract_agent",
        "build_fn": "build_contract_drafter",
        "description": "Contract Drafter — agreements, NDAs, service contracts",
    },
    "document_reviewer": {
        "module":   "agents.document_review.review_agent",
        "build_fn": "build_document_reviewer",
        "description": "Document Reviewer — redlines, risk memos",
    },
    "corporate_entity_specialist": {
        "module":   "agents.corporate_entity.corporate_agent",
        "build_fn": "build_corporate_entity_specialist",
        "description": "Corporate Entity Specialist — entity structure, governance",
    },
    "ip_licensing_specialist": {
        "module":   "agents.ip_licensing.ip_agent",
        "build_fn": "build_ip_licensing_specialist",
        "description": "IP & Licensing Specialist — IP assessment, licensing framework",
    },
    "privacy_data_counsel": {
        "module":   "agents.privacy_data.privacy_agent",
        "build_fn": "build_privacy_data_counsel",
        "description": "Privacy & Data Counsel — GDPR, CCPA, privacy impact assessments",
    },
    "regulatory_compliance_specialist": {
        "module":   "agents.regulatory_compliance.compliance_agent",
        "build_fn": "build_regulatory_compliance_specialist",
        "description": "Regulatory Compliance Specialist — compliance gap reports",
    },
    "employment_contractor_counsel": {
        "module":   "agents.employment_contractor.employment_agent",
        "build_fn": "build_employment_contractor_counsel",
        "description": "Employment & Contractor Counsel — employment agreements, contractor frameworks",
    },
    "litigation_dispute_specialist": {
        "module":   "agents.litigation_dispute.litigation_agent",
        "build_fn": "build_litigation_dispute_specialist",
        "description": "Litigation & Dispute Specialist — dispute assessment, strategy memos",
    },
}


def run_agent(agent_key: str, task: str, context: dict, save: bool = False):
    if agent_key not in AGENT_REGISTRY:
        _print_registry()
        sys.exit(f"[legal_agent_flow] ERROR: Unknown agent key '{agent_key}'.")

    entry = AGENT_REGISTRY[agent_key]
    logger.info(f"Legal agent direct: {agent_key} — {entry['description']}")

    try:
        mod = importlib.import_module(entry["module"])
    except ModuleNotFoundError as e:
        sys.exit(f"[legal_agent_flow] ERROR: Cannot import '{entry['module']}'.\n  Original error: {e}")

    build_fn = getattr(mod, entry["build_fn"], None)
    if build_fn is None:
        sys.exit(f"[legal_agent_flow] ERROR: '{entry['build_fn']}' not found in '{entry['module']}'.")

    from crewai import Crew, Task

    agent = build_fn()
    task_obj = Task(
        description=f"{task}\n\nContext:\n{context.get('raw', '') or 'No context provided.'}",
        expected_output=f"Complete legal deliverable from {entry['description']}. No placeholders.",
        agent=agent,
    )

    crew = Crew(agents=[agent], tasks=[task_obj], verbose=True)
    result = crew.kickoff()
    output_str = str(result)

    print("\n" + "="*60)
    print(f"LEGAL AGENT DIRECT OUTPUT — {agent_key.upper()}")
    print("="*60)
    print(output_str)
    print("="*60 + "\n")

    if save:
        path = save_agent_direct_output(output_str, context.get("project"), agent_key)
        if path:
            logger.info(f"Saved to {path}")

    return output_str


def _print_registry():
    print("\nAvailable Legal agents:")
    for key, entry in AGENT_REGISTRY.items():
        print(f"  {key:<35} {entry['description']}")
    print()


def main():
    parser = argparse.ArgumentParser(prog="legal_agent_flow.py", description="Legal Team — single agent direct.")
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
