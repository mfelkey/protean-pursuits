"""
flows/finance_flow.py

Protean Pursuits — Finance Group Flow

Finance Group is a dev-team sub-crew — agents live at
templates/dev-team/agents/finance/. This flow provides direct
access without going through the full dev-team pipeline.

Advisory only — Finance Group NEVER auto-blocks the pipeline.
CP-4.5 HITL gate fires on FSP completion.

Auto-skip rules (enforced by Finance Orchestrator):
  BPS (Billing Architect)  — skipped if no billing language in PRD
  PRI (Pricing Specialist) — skipped for internal tool projects

Run modes:
    full        Full Finance Group sub-crew — all applicable agents,
                synthesized into FSP. CP-4.5 gate fires.
    cost        Cost Analyst only — CEA
    roi         ROI Analyst only — ROI
    infra       Infrastructure Finance Modeler only — ICM
    billing     Billing Architect only — BPS
    pricing     Pricing Specialist only — PRI
    statements  Financial Statements Modeler only — FSR
    strategy    Strategic Corporate Finance Specialist only — SCF

Every Finance output opens with FINANCE RATING: 🟢/🟡/🔴
and ends with OPEN QUESTIONS.

Usage:
    python flows/finance_flow.py --mode full \\
        --project parallaxedge \\
        --task "Full financial analysis for ParallaxEdge sports betting platform"

    python flows/finance_flow.py --mode roi \\
        --task "ROI analysis for $2M platform build" \\
        --context "SaaS betting platform, B2C, target 50k MAU year 1"

Via pp_flow.py:
    python flows/pp_flow.py --team finance --mode full \\
        --project parallaxedge --task "Full financial analysis" --save

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

from core.context_loader import load_context, save_output  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

TEAM = "finance"

MODES = [
    "full", "cost", "roi", "infra",
    "billing", "pricing", "statements", "strategy",
]


# ── Notifications ─────────────────────────────────────────────────────────────

def _notify(title: str, message: str):
    try:
        from core.notifications import send_pushover
        send_pushover(title=title, message=message)
    except Exception as e:
        logger.warning(f"Pushover notification failed: {e}")


# ── Agent loader ──────────────────────────────────────────────────────────────

def _load_agents(keys: list) -> dict:
    from agents.dev.finance.finance_orchestrator import build_finance_orchestrator
    from agents.dev.finance.cost_analyst import build_cost_analyst
    from agents.dev.finance.roi_analyst import build_roi_analyst
    from agents.dev.finance.infra_finance_modeler import build_infra_finance_modeler
    from agents.dev.finance.billing_architect import build_billing_architect
    from agents.dev.finance.pricing_specialist import build_pricing_specialist
    from agents.dev.finance.financial_statements import build_financial_statements_modeler
    from agents.dev.finance.strategic_corp_finance import build_strategic_corp_finance_specialist

    builders = {
        "finance_orchestrator":             build_finance_orchestrator,
        "cost_analyst":                     build_cost_analyst,
        "roi_analyst":                      build_roi_analyst,
        "infra_finance_modeler":            build_infra_finance_modeler,
        "billing_architect":                build_billing_architect,
        "pricing_specialist":               build_pricing_specialist,
        "financial_statements_modeler":     build_financial_statements_modeler,
        "strategic_corp_finance_specialist":build_strategic_corp_finance_specialist,
    }
    return {k: builders[k]() for k in keys if k in builders}


# ── Core runner ───────────────────────────────────────────────────────────────

def _run_mode(mode: str, agent_keys: list, task: str,
              context: dict, save: bool) -> str:
    from crewai import Crew, Task

    agents = _load_agents(agent_keys)
    agent_list = list(agents.values())
    context_block = context.get("raw", "") or "No context provided."

    tasks = []
    for i, (key, agent) in enumerate(agents.items()):
        prefix = "" if i == 0 else (
            "Use the output of the previous task as input context.\n\n"
        )
        tasks.append(Task(
            description=(
                f"{prefix}{task}\n\nProject context:\n{context_block}\n\n"
                "OUTPUT STANDARDS:\n"
                "- Open with FINANCE RATING: 🟢/🟡/🔴\n"
                "- Advisory only — never block or mandate action\n"
                "- Include LOW/MID/HIGH scenarios for cost and ROI analyses\n"
                "- End with OPEN QUESTIONS section"
            ),
            expected_output=(
                f"Complete Finance deliverable from {key.replace('_', ' ')}. "
                f"Opens with FINANCE RATING: 🟢/🟡/🔴. "
                f"No placeholders. Ends with OPEN QUESTIONS."
            ),
            agent=agent,
        ))

    crew = Crew(agents=agent_list, tasks=tasks, verbose=True)
    _notify(f"PP Finance — {mode}", f"Starting: {task[:80]}")

    result = crew.kickoff()
    output_str = str(result)

    print("\n" + "=" * 60)
    print(f"FINANCE GROUP OUTPUT — {mode.upper()}")
    print("=" * 60)
    print(output_str)
    print("=" * 60 + "\n")

    if save and context.get("project"):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = save_output(
            output_str, context.get("project"), TEAM,
            f"{mode}_{ts}.md"
        )
        if path:
            logger.info(f"Saved to {path}")

    _notify(f"PP Finance — {mode} complete",
            f"Project: {context.get('project') or 'ad-hoc'}")
    return output_str


# ── Mode runners ──────────────────────────────────────────────────────────────

def run_full(context: dict, task: str, save: bool = False) -> str:
    """
    Full Finance Group sub-crew.
    Finance Orchestrator sequences all applicable agents,
    cross-checks outputs, synthesizes FSP, and fires CP-4.5 HITL gate.
    BPS and PRI auto-skip rules enforced by the Finance Orchestrator.
    """
    # Delegate to the Finance Orchestrator's own run function if available,
    # otherwise run the full crew directly.
    try:
        from agents.dev.finance.finance_orchestrator import run_finance_crew
        _notify("PP Finance — full", f"Starting Finance Group: {task[:80]}")
        result = run_finance_crew(context=context.get("data", context), task=task, save=save)
        _notify("PP Finance — full complete",
                f"FSP ready. Project: {context.get('project') or 'ad-hoc'}")
        return str(result)
    except (ImportError, AttributeError):
        # Fallback: run all agents as a crew
        logger.info("Finance Orchestrator run_finance_crew not found — running full crew directly.")
        return _run_mode("full", [
            "finance_orchestrator",
            "cost_analyst",
            "roi_analyst",
            "infra_finance_modeler",
            "billing_architect",
            "pricing_specialist",
            "financial_statements_modeler",
            "strategic_corp_finance_specialist",
        ], task, context, save)


def run_cost(context: dict, task: str, save: bool = False) -> str:
    return _run_mode("cost", ["cost_analyst"], task, context, save)


def run_roi(context: dict, task: str, save: bool = False) -> str:
    return _run_mode("roi", ["roi_analyst"], task, context, save)


def run_infra(context: dict, task: str, save: bool = False) -> str:
    return _run_mode("infra", ["infra_finance_modeler"], task, context, save)


def run_billing(context: dict, task: str, save: bool = False) -> str:
    return _run_mode("billing", ["billing_architect"], task, context, save)


def run_pricing(context: dict, task: str, save: bool = False) -> str:
    return _run_mode("pricing", ["pricing_specialist"], task, context, save)


def run_statements(context: dict, task: str, save: bool = False) -> str:
    return _run_mode("statements", ["financial_statements_modeler"], task, context, save)


def run_strategy(context: dict, task: str, save: bool = False) -> str:
    return _run_mode("strategy", ["strategic_corp_finance_specialist"], task, context, save)


# ── CLI ───────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="finance_flow.py",
        description=(
            "Finance Group flow — direct access to Finance sub-crew agents.\n\n"
            "Advisory only. CP-4.5 HITL gate fires on full mode FSP completion.\n"
            "BPS and PRI auto-skip rules enforced by the Finance Orchestrator."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--mode", required=True, choices=MODES)
    parser.add_argument("--task", required=True)
    parser.add_argument("--project", default=None)
    parser.add_argument("--context-file", dest="context_file", default=None)
    parser.add_argument("--context", default=None)
    parser.add_argument("--save", action="store_true", default=False)
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.save and not args.project:
        parser.error("--save requires --project.")

    context = load_context(
        project=args.project,
        context_file=args.context_file,
        context_str=args.context,
    )

    globals()[f"run_{args.mode}"](context=context, task=args.task, save=args.save)


if __name__ == "__main__":
    main()
