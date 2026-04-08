"""
flows/finance_intake_flow.py

Protean Pursuits — Finance Team Intake Flow

Entry point for routing project briefs to the Finance Team Orchestrator.
Finance Group is advisory only — never auto-blocks the pipeline.
CP-4.5 HITL gate fires on FSP completion.

Auto-skip rules (enforced by Finance Orchestrator):
  BPS (Billing Architect)  — skipped if no billing language in PRD
  PRI (Pricing Specialist) — skipped for internal tool projects

Usage:
    python flows/finance_intake_flow.py \\
        --project parallaxedge \\
        --brief "Full financial analysis for ParallaxEdge sports betting platform" \\
        --save

Via pp_flow.py:
    python flows/pp_flow.py --team finance \\
        --project parallaxedge \\
        --task "Full financial analysis for ParallaxEdge" \\
        --save
"""

import argparse
import importlib
import logging
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "teams" / "finance-team"))

from core.context_loader import load_context, save_output  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

TEAM = "finance"


# ── Notifications ─────────────────────────────────────────────────────────────

def _notify(title: str, message: str):
    try:
        from core.notifications import send_pushover
        send_pushover(title=title, message=message)
    except Exception as e:
        logger.warning(f"Pushover notification failed: {e}")


# ── Orchestrator import ───────────────────────────────────────────────────────

def _import_orchestrator():
    """Import run_finance_orchestrator from teams/finance-team/."""
    try:
        from agents.orchestrator.orchestrator import run_finance_orchestrator
        return run_finance_orchestrator
    except ImportError as e:
        sys.exit(
            f"[finance_intake_flow] ERROR: Cannot import Finance Team orchestrator.\n"
            f"  Expected at: teams/finance-team/agents/orchestrator/orchestrator.py\n"
            f"  Original error: {e}"
        )


# ── Main runner ───────────────────────────────────────────────────────────────

def run(brief: str, context: dict, save: bool = False) -> str:
    run_finance_orchestrator = _import_orchestrator()

    project = context.get("project") or "ad-hoc"
    logger.info(f"Finance intake — project: {project}")
    _notify("PP Finance — intake", f"Project: {project} | Brief: {brief[:80]}")

    result = run_finance_orchestrator(brief=brief, context=context)
    output_str = str(result)

    print("\n" + "=" * 60)
    print("FINANCE TEAM OUTPUT")
    print("=" * 60)
    print(output_str)
    print("=" * 60 + "\n")

    if save and context.get("project"):
        from datetime import datetime
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = save_output(
            content=output_str,
            project=context["project"],
            team=TEAM,
            filename=f"intake_{ts}.md",
        )
        if path:
            logger.info(f"Saved to {path}")

    _notify("PP Finance — intake complete", f"Project: {project}")
    return output_str


# ── CLI ───────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="finance_intake_flow.py",
        description=(
            "Protean Pursuits — Finance Team intake flow.\n\n"
            "Advisory only. CP-4.5 HITL gate fires on FSP completion.\n"
            "BPS and PRI auto-skip rules enforced by the Finance Orchestrator."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--brief", "--task", dest="brief", required=True,
                        help="Plain-English project brief.")
    parser.add_argument("--project", default=None,
                        help="Project name — loads output/<project>/context.json.")
    parser.add_argument("--context-file", dest="context_file", default=None,
                        help="Path to context file.")
    parser.add_argument("--context", default=None,
                        help="Inline context string.")
    parser.add_argument("--save", action="store_true", default=False,
                        help="Save output to disk (requires --project).")
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

    run(brief=args.brief, context=context, save=args.save)


if __name__ == "__main__":
    main()
