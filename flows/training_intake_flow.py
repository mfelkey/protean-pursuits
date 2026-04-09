"""
flows/training_intake_flow.py

Protean Pursuits — Training Team Intake Flow

Direct entry point to the Training Team for knowledge base management.
Accepts a plain-English brief, loads or stubs a project context, then
routes directly to the Training Team Orchestrator.

The Training Team manages knowledge bases for all 9 agent teams — running
7 domain curators, monitoring freshness, and sending Pushover alerts for
CRITICAL updates.

Run modes (selected automatically by Training Orchestrator):
    full        Refresh all 7 team knowledge bases
    team        Refresh one team's knowledge base
    on_demand   Targeted refresh triggered by a specific news item or topic
    status      Show knowledge freshness report across all teams
    alerts      Show critical alerts from last 24h

Usage:
    # Refresh all knowledge bases
    python flows/training_intake_flow.py \\
        --brief "Full knowledge refresh — all teams"

    # Targeted refresh for a specific team
    python flows/training_intake_flow.py \\
        --project parallaxedge \\
        --brief "Refresh DS team knowledge base — focus on Bayesian modeling and sports data APIs" \\
        --save

    # Status check
    python flows/training_intake_flow.py \\
        --brief "Show knowledge freshness status for all teams"

Via pp_flow.py:
    python flows/pp_flow.py --team training --mode full \\
        --project parallaxedge --task "Full knowledge refresh" --save
"""

import argparse
import logging
import re
import sys
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "teams" / "training-team"))

from core.context_loader import load_context, save_output  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

TEAM = "training"


# ── Notifications ─────────────────────────────────────────────────────────────

def _notify(title: str, message: str):
    try:
        from core.notifications import send_pushover
        send_pushover(title=title, message=message)
    except Exception as e:
        logger.warning(f"Pushover notification failed: {e}")


# ── Orchestrator import ───────────────────────────────────────────────────────

def _import_orchestrator():
    """
    Import the Training Team Orchestrator run functions.
    The training orchestrator exposes run_curator() and run_full_refresh()
    rather than a single run_training_orchestrator() — this flow dispatches
    to run_full_refresh() by default, or run_curator() for targeted requests.
    """
    try:
        from agents.orchestrator.orchestrator import run_full_refresh, run_curator
        return run_full_refresh, run_curator
    except ImportError as e:
        sys.exit(
            f"[training_intake_flow] ERROR: Cannot import Training Team Orchestrator.\n"
            f"  Ensure agents/orchestrator/orchestrator.py is on sys.path.\n"
            f"  sys.path includes teams/training-team — verify team is installed.\n"
            f"  Note: Training orchestrator requires teams/training-team/knowledge/ module.\n"
            f"  Original error: {e}"
        )


# ── Context helpers ───────────────────────────────────────────────────────────

def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:40].strip("-")


def _build_stub_context(project_name: str, brief: str) -> dict:
    return {
        "project": project_name,
        "source": "training_intake",
        "team": TEAM,
        "brief": brief,
        "raw": (
            f"Project: {project_name}\n"
            f"Source: training_intake\n"
            f"Brief: {brief}"
        ),
    }


# ── Mode detection ────────────────────────────────────────────────────────────

_TARGETED_KEYWORDS = [
    "ds team", "dev team", "marketing team", "legal team", "design team",
    "qa team", "strategy team", "hr team", "video team", "finance team",
    "one team", "specific team", "targeted", "on demand", "on-demand",
    "only", "just", "single",
]


def _is_targeted(brief: str) -> bool:
    """Return True if the brief suggests a targeted single-team refresh."""
    brief_lower = brief.lower()
    return any(kw in brief_lower for kw in _TARGETED_KEYWORDS)


# ── Main runner ───────────────────────────────────────────────────────────────

def run(brief: str, context: dict, save: bool = False) -> str:
    run_full_refresh, run_curator = _import_orchestrator()

    project = context.get("project") or "ad-hoc"
    logger.info(f"Training intake — project: {project}")
    _notify("PP Training — intake", f"Project: {project} | Brief: {brief[:80]}")

    # Route to targeted curator or full refresh based on brief content
    if _is_targeted(brief):
        logger.info("Routing to run_curator() — targeted refresh detected in brief")
        result = run_curator(brief=brief, context=context)
    else:
        logger.info("Routing to run_full_refresh() — full refresh")
        result = run_full_refresh(brief=brief, context=context)

    output_str = str(result)

    print("\n" + "=" * 60)
    print("TRAINING TEAM OUTPUT")
    print("=" * 60)
    print(output_str)
    print("=" * 60 + "\n")

    if save and context.get("project"):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = save_output(
            content=output_str,
            project=context["project"],
            team=TEAM,
            filename=f"intake_{ts}.md",
        )
        if path:
            logger.info(f"Saved to {path}")

    _notify("PP Training — intake complete", f"Project: {project}")
    return output_str


# ── CLI ───────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="training_intake_flow.py",
        description=(
            "Protean Pursuits — Training Team intake flow.\n\n"
            "Routes a plain-English brief to the Training Team Orchestrator.\n"
            "Dispatches to run_full_refresh() for broad requests or\n"
            "run_curator() when the brief targets a specific team or topic.\n\n"
            "Run modes (auto-detected from brief):\n"
            "  full       — refresh all 7 team knowledge bases\n"
            "  targeted   — refresh one team or topic (detected from brief keywords)\n\n"
            "Knowledge base location: teams/training-team/knowledge/"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--brief", "--task", dest="brief", default=None,
                        help="Plain-English brief describing the knowledge refresh needed.")
    parser.add_argument("--brief-file", dest="brief_file", default=None,
                        help="Path to a file containing the brief.")
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

    # Resolve brief
    if args.brief_file:
        brief = Path(args.brief_file).read_text().strip()
    elif args.brief:
        brief = args.brief
    else:
        parser.error("--brief or --brief-file is required.")

    if args.save and not args.project:
        parser.error("--save requires --project.")

    context = load_context(
        project=args.project,
        context_file=args.context_file,
        context_str=args.context,
    )

    if not context.get("project") and args.project:
        context = _build_stub_context(args.project, brief)
    elif not context.get("project"):
        slug = _slugify(brief)
        context = _build_stub_context(slug, brief)

    run(brief=brief, context=context, save=args.save)


if __name__ == "__main__":
    main()
