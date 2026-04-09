"""
flows/dev_intake_flow.py

Protean Pursuits — Dev Team Intake Flow

Direct entry point to the Dev Team for post-initiation software development
requests. Accepts a plain-English brief, loads or stubs a project context,
then routes directly to the Dev Team Orchestrator. The orchestrator
sequences the full planning → build → quality pipeline based on the brief.

Checkpoints (CP-1 through CP-6) fire as normal inside the dev pipeline.
Nothing ships without human approval at each gate.

Run modes (selected automatically by Dev Team Orchestrator):
    plan        Planning phase only (PRD → TAD → SRR → UX)
    build       Build phase (Senior Dev → Backend → Frontend → DBA → DevOps)
    quality     Quality phase (QA Lead → Test Automation)
    mobile      Mobile add-on (UX → iOS → Android → RN → DevOps → QA)
    retrofit    Retrofit run (deployment-agnostic cleanup)
    full        Full pipeline — plan → finance → build → quality

Usage:
    # Cold start — no existing project
    python flows/dev_intake_flow.py \\
        --brief "Build a sports betting data dashboard with real-time odds feeds"

    # With existing project context
    python flows/dev_intake_flow.py \\
        --project parallaxedge \\
        --brief "Add subscription billing to the existing ParallaxEdge platform" \\
        --save

    # Brief from file
    python flows/dev_intake_flow.py \\
        --project parallaxedge \\
        --brief-file briefs/feature_brief.txt \\
        --save

Via pp_flow.py:
    python flows/pp_flow.py --team dev --mode full \\
        --project parallaxedge --task "Full dev pipeline" --save
"""

import argparse
import logging
import re
import sys
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "teams" / "dev-team"))

from core.context_loader import load_context, save_output  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

TEAM = "dev"
BRIEF_MIN_WORDS = 20


# ── Notifications ─────────────────────────────────────────────────────────────

def _notify(title: str, message: str):
    try:
        from core.notifications import send_pushover
        send_pushover(title=title, message=message)
    except Exception as e:
        logger.warning(f"Pushover notification failed: {e}")


# ── Orchestrator import ───────────────────────────────────────────────────────

def _import_orchestrator():
    """Import the Dev Team Orchestrator run function. Exits with clear message on failure."""
    try:
        from agents.orchestrator.orchestrator import run_dev_orchestrator
        return run_dev_orchestrator
    except ImportError as e:
        sys.exit(
            f"[dev_intake_flow] ERROR: Cannot import Dev Team Orchestrator.\n"
            f"  Ensure agents/orchestrator/orchestrator.py is on sys.path.\n"
            f"  sys.path includes teams/dev-team — verify team is installed.\n"
            f"  Original error: {e}"
        )


# ── Context helpers ───────────────────────────────────────────────────────────

def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:40].strip("-")


def _build_stub_context(project_name: str, brief: str) -> dict:
    """
    Build a minimal project context for cold-start runs.
    The Dev Team Orchestrator fills in tech stack, scope, and requirements from the brief.
    """
    return {
        "project": project_name,
        "source": "dev_intake",
        "team": TEAM,
        "brief": brief,
        "classification": "DEV",
        "structured_spec": {},
        "raw": (
            f"Project: {project_name}\n"
            f"Source: dev_intake\n"
            f"Brief: {brief}"
        ),
    }


# ── Brief clarification ───────────────────────────────────────────────────────

def _maybe_clarify(brief: str) -> str:
    """Prompt for more detail if the brief is too short to act on."""
    words = brief.split()
    if len(words) < BRIEF_MIN_WORDS:
        print(f"\n⚠️  Brief is short ({len(words)} words). A detailed brief produces better results.")
        print("   Add detail (or press Enter to continue as-is):")
        addition = input("   > ").strip()
        if addition:
            brief = f"{brief} {addition}"
    return brief


# ── Main runner ───────────────────────────────────────────────────────────────

def run(brief: str, context: dict, save: bool = False) -> str:
    run_dev_orchestrator = _import_orchestrator()

    project = context.get("project") or "ad-hoc"
    logger.info(f"Dev intake — project: {project}")
    _notify("PP Dev — intake", f"Project: {project} | Brief: {brief[:80]}")

    result = run_dev_orchestrator(brief=brief, context=context)
    output_str = str(result)

    print("\n" + "=" * 60)
    print("DEV TEAM OUTPUT")
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

    _notify("PP Dev — intake complete", f"Project: {project}")
    return output_str


# ── CLI ───────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dev_intake_flow.py",
        description=(
            "Protean Pursuits — Dev Team intake flow.\n\n"
            "Routes a plain-English brief directly to the Dev Team Orchestrator.\n"
            "Checkpoints CP-1 through CP-6 fire automatically inside the pipeline."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--brief", "--task", dest="brief", default=None,
                        help="Plain-English project brief.")
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
    parser.add_argument("--no-clarify", action="store_true", default=False,
                        help="Skip the brief clarification prompt.")
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

    if not args.no_clarify:
        brief = _maybe_clarify(brief)

    context = load_context(
        project=args.project,
        context_file=args.context_file,
        context_str=args.context,
    )

    # Cold start — no existing context
    if not context.get("project") and args.project:
        context = _build_stub_context(args.project, brief)
    elif not context.get("project"):
        slug = _slugify(brief)
        context = _build_stub_context(slug, brief)

    run(brief=brief, context=context, save=args.save)


if __name__ == "__main__":
    main()
