"""
flows/design_intake_flow.py

Protean Pursuits — Design Team Intake Flow

Direct entry point to the Design Team for post-initiation requests.
Accepts a plain-English brief, loads or stubs a project context,
prompts for any critical missing information, then routes directly to the
Design Team Orchestrator. The orchestrator selects the appropriate run
mode and sequences agents based on the brief.

HITL gate: DESIGN_REVIEW fires on all modes before handoff to dev.

Run modes (selected automatically by Design Team Orchestrator):
    research        User research report, journey maps
    wireframe       Research report + wireframes
    visual          UI designs, brand guide, design system
    motion          Motion spec, animation briefs
    accessibility   Accessibility audit, usability report
    full            Complete design package

Usage:
    # Cold start — no existing project
    python flows/design_intake_flow.py \
        --brief "Full design package for ParallaxEdge — sports betting app, iOS + Android, dark-mode first"

    # With existing project context
    python flows/design_intake_flow.py \
        --project parallaxedge \
        --brief "Wireframe the bet slip flow and user onboarding screens"

    # Brief from file
    python flows/design_intake_flow.py \
        --project parallaxedge \
        --brief-file briefs/design_brief.txt \
        --save

Via pp_flow.py:
    python flows/pp_flow.py --team design --mode full \
        --project parallaxedge --task "Full design package for ParallaxEdge — sports betting app, iOS + Android, dark-mode first" --save
"""

import argparse
import logging
import re
import sys
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, "/home/mfelkey/design-team")

from core.context_loader import load_context, save_output  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

TEAM = "design"
BRIEF_MIN_WORDS = 20  # briefs shorter than this trigger a clarification prompt


# ── Notifications ─────────────────────────────────────────────────────────────

def _notify(title: str, message: str):
    try:
        from core.notifications import send_pushover
        send_pushover(title=title, message=message)
    except Exception as e:
        logger.warning(f"Pushover notification failed: {e}")


# ── Orchestrator import ───────────────────────────────────────────────────────

def _import_orchestrator():
    """Import the Design Team Orchestrator run function. Exits with clear message on failure."""
    try:
        from agents.design.orchestrator.orchestrator import run_design_orchestrator
        return run_design_orchestrator
    except ImportError as e:
        sys.exit(
            f"[design_intake_flow] ERROR: Cannot import Design Team Orchestrator.\n"
            f"  Ensure agents/design/orchestrator/orchestrator.py is on sys.path.\n"
            f"  sys.path includes /home/mfelkey/design-team — verify team is installed.\n"
            f"  Original error: {e}"
        )


# ── Context helpers ───────────────────────────────────────────────────────────

def _slugify(text: str) -> str:
    """Convert a string to a lowercase slug suitable for use as a project name."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:40].strip("-")


def _build_stub_context(project_name: str, brief: str) -> dict:
    """
    Build a minimal project context for cold-start runs.
    The Design Team Orchestrator fills in objectives and details from the brief.
    """
    return {
        "project": project_name,
        "source": "design_intake",
        "team": TEAM,
        "brief": brief,
        "objectives": [],
        "raw": (
            f"Project: {project_name}\n"
            f"Source: design_intake\n"
            f"Brief: {brief}"
        ),
    }


def _resolve_brief(args: argparse.Namespace) -> str:
    """Return brief text from --brief or --brief-file. Exits if neither provided."""
    if args.brief_file:
        path = Path(args.brief_file)
        if not path.exists():
            sys.exit(f"[design_intake_flow] ERROR: Brief file not found: {path}")
        return path.read_text(encoding="utf-8").strip()
    if args.brief:
        return args.brief.strip()
    sys.exit(
        "[design_intake_flow] ERROR: A brief is required.\n"
        "  Use --brief \"<text>\" or --brief-file <path>."
    )


# ── Interactive prompts ───────────────────────────────────────────────────────

def _prompt_project_name(suggested: str) -> str:
    """Prompt for a project name when --project is not supplied."""
    try:
        response = input(
            f"\nProject name (used for output folder) [{suggested}]: "
        ).strip()
    except (EOFError, KeyboardInterrupt):
        return suggested
    return response if response else suggested


def _prompt_additional_context(brief: str) -> str:
    """Prompt for additional context when the brief is very short."""
    word_count = len(brief.split())
    if word_count >= BRIEF_MIN_WORDS:
        return brief
    try:
        extra = input(
            f"\nYour brief is brief \U0001f604 ({word_count} words) — "
            f"any additional context to share? (Enter to skip): "
        ).strip()
    except (EOFError, KeyboardInterrupt):
        return brief
    if extra:
        return f"{brief}\n\nAdditional context: {extra}"
    return brief


# ── Core runner ───────────────────────────────────────────────────────────────

def run_design_intake(
    brief: str,
    context: dict,
    save: bool = False,
    non_interactive: bool = False,
) -> str:
    """
    Route a plain-English brief to the Design Team Orchestrator.

    The orchestrator selects the appropriate run mode based on the brief
    and sequences agents accordingly. HITL gates fire as normal.

    Args:
        brief:           Plain-English description of the request.
        context:         Project context dict (from load_context or stub).
        save:            Write output to disk under output/<project>/design/.
        non_interactive: Skip all interactive prompts (for scripted use).

    Returns:
        Design Team Orchestrator output as a string.
    """
    # ── Brief enrichment ──────────────────────────────────────────────────────
    if not non_interactive:
        brief = _prompt_additional_context(brief)

    # ── Inject brief into context ─────────────────────────────────────────────
    context["brief"] = brief
    if "raw" not in context or not context["raw"]:
        context["raw"] = brief
    else:
        context["raw"] = f"{context['raw']}\n\nDesign Team brief:\n{brief}"

    project = context.get("project") or "ad-hoc"
    logger.info(f"Design Team intake — project: {project}")
    logger.info(f"Brief ({len(brief.split())} words): {brief[:120]}{'...' if len(brief) > 120 else ''}")

    _notify(
        "PP Design Team — intake",
        f"Project: {project} | Brief: {brief[:80]}"
    )

    # ── Route to Design Team Orchestrator ─────────────────────────────────────
    run_orchestrator = _import_orchestrator()

    try:
        result = run_orchestrator(
            context=context,
            brief=brief,
        )
        output_str = str(result)
    except TypeError:
        # Fallback: orchestrator may use a different signature — try context only
        logger.warning(
            "Design Team Orchestrator did not accept 'brief' kwarg — "
            "passing brief via context['brief'] only."
        )
        result = run_orchestrator(context=context)
        output_str = str(result)

    print("\n" + "=" * 60)
    print(f"DESIGN TEAM ORCHESTRATOR OUTPUT — {project.upper()}")
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
    elif save and not context.get("project"):
        logger.warning("--save specified but no project name resolved. Output not saved.")

    _notify(
        "PP Design Team — intake complete",
        f"Project: {project}"
    )
    return output_str


# ── CLI ───────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="design_intake_flow.py",
        description=(
            "Protean Pursuits — Design Team Intake Flow\n\n"
            "Direct entry point for post-initiation design requests.\n"
            "Accepts a plain-English brief and routes to the Design Team\n"
            "Orchestrator, which selects the appropriate run mode.\n\n"
            "HITL gate: DESIGN_REVIEW fires on all modes before handoff to dev.\n\n"
            "Examples:\n"
            "  # Cold start\n"
            "  python flows/design_intake_flow.py \\\n"
            "      --brief \"Full design package for ParallaxEdge — sports betting app, iOS + Android, dark-mode first\"\n\n"
            "  # Existing project\n"
            "  python flows/design_intake_flow.py \\\n"
            "      --project parallaxedge \\\n"
            "      --brief \"Wireframe the bet slip flow and user onboarding screens\" --save\n\n"
            "  # Brief from file\n"
            "  python flows/design_intake_flow.py \\\n"
            "      --project parallaxedge \\\n"
            "      --brief-file briefs/design_brief.txt --save"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    brief_group = parser.add_mutually_exclusive_group(required=True)
    brief_group.add_argument(
        "--brief",
        metavar="TEXT",
        help="Plain-English brief.",
    )
    brief_group.add_argument(
        "--brief-file",
        dest="brief_file",
        metavar="PATH",
        help="Path to a text file containing the brief.",
    )

    parser.add_argument(
        "--project",
        default=None,
        help="Project name — loads output/<project>/context.json if it exists.",
    )
    parser.add_argument(
        "--context-file",
        dest="context_file",
        default=None,
        help="Explicit path to a context JSON file.",
    )
    parser.add_argument(
        "--context",
        default=None,
        help="Inline context string (appended to brief context).",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        default=False,
        help=(
            "Save output to output/<project>/design/intake_<timestamp>.md. "
            "Requires --project (or a project name entered at the prompt)."
        ),
    )
    parser.add_argument(
        "--non-interactive",
        dest="non_interactive",
        action="store_true",
        default=False,
        help=(
            "Suppress all interactive prompts. "
            "Requires --project to be set explicitly."
        ),
    )

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.non_interactive and not args.project:
        parser.error("--non-interactive requires --project.")

    if args.save and args.non_interactive and not args.project:
        parser.error("--save with --non-interactive requires --project.")

    brief = _resolve_brief(args)

    if args.project or args.context_file or args.context:
        context = load_context(
            project=args.project,
            context_file=args.context_file,
            context_str=args.context,
        )
        if not context.get("project") and args.project:
            context["project"] = args.project
    else:
        suggested_slug = _slugify(brief[:60])
        if args.non_interactive:
            project_name = suggested_slug
        else:
            project_name = _prompt_project_name(suggested_slug)
        context = _build_stub_context(project_name, brief)

    run_design_intake(
        brief=brief,
        context=context,
        save=args.save,
        non_interactive=args.non_interactive,
    )


if __name__ == "__main__":
    main()
