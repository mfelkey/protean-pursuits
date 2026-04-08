"""
flows/finance_agent_flow.py

Finance Group — single-agent direct flow.
Targets one Finance specialist by agent key.

Agents live at templates/dev-team/agents/finance/.
All outputs open with FINANCE RATING: 🟢/🟡/🔴
and end with OPEN QUESTIONS.

Usage:
    python flows/finance_agent_flow.py \\
        --agent roi_analyst \\
        --task "ROI analysis for $2M platform build" \\
        --project parallaxedge [--save]

Via pp_flow.py:
    python flows/pp_flow.py --team finance --agent roi_analyst \\
        --task "ROI for $2M platform build" --project parallaxedge
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "teams" / "finance-team"))

from core.context_loader import load_context, save_agent_direct_output  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

AGENT_REGISTRY = {
    "finance_orchestrator": {
        "builder":     "agents.dev.finance.finance_orchestrator.build_finance_orchestrator",
        "produces":    "FSP",
        "description": "Sequences crew, cross-checks outputs, synthesises FSP, fires CP-4.5",
    },
    "cost_analyst": {
        "builder":     "agents.dev.finance.cost_analyst.build_cost_analyst",
        "produces":    "CEA",
        "description": "Cost Estimation Analysis — always runs first in full mode",
    },
    "roi_analyst": {
        "builder":     "agents.dev.finance.roi_analyst.build_roi_analyst",
        "produces":    "ROI",
        "description": "Return on Investment analysis — always runs",
    },
    "infra_finance_modeler": {
        "builder":     "agents.dev.finance.infra_finance_modeler.build_infra_finance_modeler",
        "produces":    "ICM",
        "description": "Infrastructure Cost Model — always runs",
    },
    "billing_architect": {
        "builder":     "agents.dev.finance.billing_architect.build_billing_architect",
        "produces":    "BPS",
        "description": "Billing & Payments Spec — skipped if no billing language in PRD",
    },
    "pricing_specialist": {
        "builder":     "agents.dev.finance.pricing_specialist.build_pricing_specialist",
        "produces":    "PRI",
        "description": "Pricing & Revenue model — skipped for internal tool projects",
    },
    "financial_statements_modeler": {
        "builder":     "agents.dev.finance.financial_statements.build_financial_statements_modeler",
        "produces":    "FSR",
        "description": "Financial Statements Report — always runs",
    },
    "strategic_corp_finance_specialist": {
        "builder":     "agents.dev.finance.strategic_corp_finance.build_strategic_corp_finance_specialist",
        "produces":    "SCF",
        "description": "Strategic Corporate Finance — always runs last",
    },
}


def _import_builder(dotpath: str):
    parts = dotpath.rsplit(".", 1)
    module = __import__(parts[0], fromlist=[parts[1]])
    return getattr(module, parts[1])


def run_agent(agent_key: str, task: str, context: dict,
              save: bool = False) -> str:
    if agent_key not in AGENT_REGISTRY:
        _print_registry()
        sys.exit(f"[finance_agent_flow] Unknown agent key '{agent_key}'.")

    entry = AGENT_REGISTRY[agent_key]
    logger.info(f"Finance agent direct: {agent_key} → {entry['produces']}")

    try:
        build_fn = _import_builder(entry["builder"])
        agent = build_fn()
    except ImportError as e:
        sys.exit(
            f"[finance_agent_flow] Cannot import {agent_key}.\n"
            f"  Expected at: {entry['builder']}\n"
            f"  Error: {e}"
        )

    from crewai import Crew, Task
    context_block = context.get("raw", "") or "No context provided."

    task_obj = Task(
        description=(
            f"{task}\n\nProject context:\n{context_block}\n\n"
            "OUTPUT STANDARDS:\n"
            "- Open with FINANCE RATING: 🟢/🟡/🔴\n"
            "- Advisory only — never block or mandate action\n"
            "- Include LOW/MID/HIGH scenarios where applicable\n"
            "- End with OPEN QUESTIONS section"
        ),
        expected_output=(
            f"Complete {entry['produces']} from {agent_key.replace('_', ' ')}. "
            f"Opens with FINANCE RATING: 🟢/🟡/🔴. "
            f"No placeholders. Ends with OPEN QUESTIONS."
        ),
        agent=agent,
    )

    crew = Crew(agents=[agent], tasks=[task_obj], verbose=True)
    result = crew.kickoff()
    output_str = str(result)

    print("\n" + "=" * 60)
    print(f"FINANCE AGENT DIRECT — {agent_key.upper()}")
    print("=" * 60)
    print(output_str)
    print("=" * 60 + "\n")

    if save:
        path = save_agent_direct_output(
            content=output_str,
            project=context.get("project"),
            agent_key=f"finance_{agent_key}",
        )
        if path:
            logger.info(f"Saved to {path}")
        else:
            logger.warning("--save specified but no --project. Output not saved.")

    return output_str


def _print_registry():
    print("\nAvailable Finance agents:")
    for key, entry in AGENT_REGISTRY.items():
        print(f"  {key:<40} → {entry['produces']:<6}  {entry['description']}")
    print()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="finance_agent_flow.py",
        description=(
            "Finance Group — single specialist direct.\n\n"
            "All outputs open with FINANCE RATING: 🟢/🟡/🔴\n"
            "and end with OPEN QUESTIONS."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--agent", required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--project", default=None)
    parser.add_argument("--context-file", dest="context_file", default=None)
    parser.add_argument("--context", default=None)
    parser.add_argument("--save", action="store_true", default=False)
    parser.add_argument("--list-agents", action="store_true", default=False)
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.list_agents:
        _print_registry()
        sys.exit(0)

    if args.save and not args.project:
        parser.error("--save requires --project.")

    context = load_context(
        project=args.project,
        context_file=args.context_file,
        context_str=args.context,
    )

    run_agent(agent_key=args.agent, task=args.task,
              context=context, save=args.save)


if __name__ == "__main__":
    main()
