"""
flows/pp_flow.py

Top-level Protean Pursuits dispatcher.

Routes any request to a team orchestrator (--mode) or directly to a named
agent (--agent) without going through intake_flow.py.

Usage examples:
    # Team orchestrator via mode
    python flows/pp_flow.py --team marketing --mode campaign --project parallaxedge

    # Named agent direct
    python flows/pp_flow.py --team marketing --agent copywriter \\
        --task "Write App Store listing for ParallaxEdge" --project parallaxedge

    # Inline context, no project
    python flows/pp_flow.py --team legal --agent contract_drafter \\
        --task "Draft NDA for contractor" --context "Two-party NDA, Michigan law, 2yr term"

    # Context from file
    python flows/pp_flow.py --team strategy --mode competitive \\
        --project parallaxedge --context-file ~/briefs/competitive_brief.txt

    # Save output to disk
    python flows/pp_flow.py --team design --mode research \\
        --project parallaxedge --task "Research user onboarding patterns" --save
"""

import argparse
import importlib
import logging
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup — repo root on sys.path
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from core.context_loader import load_context  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Team → flow module mapping
# ---------------------------------------------------------------------------
# Maps CLI team name to (flow_module_path, agent_flow_module_path)
# Module paths are relative to repo root, using dot notation.
TEAM_FLOW_MAP = {
    "dev":       ("templates.dev-team.flows.dev_flow",       "templates.dev-team.flows.dev_agent_flow"),
    "ds":        ("templates.ds-team.flows.ds_flow",         "templates.ds-team.flows.ds_agent_flow"),
    "design":    ("templates.design-team.flows.design_flow", "templates.design-team.flows.design_agent_flow"),
    "legal":     ("templates.legal-team.flows.legal_flow",   "templates.legal-team.flows.legal_agent_flow"),
    "marketing": ("templates.marketing-team.flows.marketing_flow", "templates.marketing-team.flows.marketing_agent_flow"),
    "strategy":  ("templates.strategy-team.flows.strategy_flow",   "templates.strategy-team.flows.strategy_agent_flow"),
    "qa":        ("templates.qa-team.flows.qa_flow",         "templates.qa-team.flows.qa_agent_flow"),
    "hr":        ("templates.hr-team.flows.hr_flow",         "templates.hr-team.flows.hr_agent_flow"),
    "video":     ("templates.video-team.flows.video_flow",   "templates.video-team.flows.video_agent_flow"),
}

VALID_TEAMS = sorted(TEAM_FLOW_MAP.keys())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _import_module(dotted_path: str):
    """Import a module by dotted path, with a friendly error on failure."""
    # Convert hyphens in package names to underscores for Python import
    safe_path = dotted_path.replace("-", "_")
    try:
        return importlib.import_module(safe_path)
    except ModuleNotFoundError as e:
        logger.error(f"Could not import module '{safe_path}': {e}")
        sys.exit(
            f"[pp_flow] ERROR: Flow module not found — '{safe_path}'\n"
            f"  This may be a stub (e.g. video team) or not yet built.\n"
            f"  Original error: {e}"
        )


def _run_team_flow(team: str, mode: str, task: str, context: dict, save: bool):
    """Load the team flow module and call run_<mode>(context, task, save)."""
    flow_module_path, _ = TEAM_FLOW_MAP[team]
    module = _import_module(flow_module_path)

    run_fn_name = f"run_{mode}"
    run_fn = getattr(module, run_fn_name, None)
    if run_fn is None:
        # List available modes from the module to help the user
        available = [
            name[4:] for name in dir(module)
            if name.startswith("run_") and callable(getattr(module, name))
        ]
        sys.exit(
            f"[pp_flow] ERROR: Mode '{mode}' not found in {team} flow.\n"
            f"  Available modes: {', '.join(sorted(available)) or 'none'}"
        )

    logger.info(f"Dispatching to {team} team — mode: {mode}")
    run_fn(context=context, task=task, save=save)


def _run_agent_flow(team: str, agent: str, task: str, context: dict, save: bool):
    """Load the agent flow module and call run_agent(agent_key, task, context, save)."""
    _, agent_flow_module_path = TEAM_FLOW_MAP[team]
    module = _import_module(agent_flow_module_path)

    run_fn = getattr(module, "run_agent", None)
    if run_fn is None:
        sys.exit(
            f"[pp_flow] ERROR: run_agent() not found in {team} agent flow module.\n"
            f"  Module: {agent_flow_module_path}"
        )

    logger.info(f"Dispatching to {team} team — agent: {agent}")
    run_fn(agent_key=agent, task=task, context=context, save=save)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pp_flow.py",
        description=(
            "Protean Pursuits top-level dispatcher.\n"
            "Routes to a team orchestrator (--mode) or a named agent (--agent).\n\n"
            "Context resolution order: --project → --context-file → --context → none"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--team",
        required=True,
        choices=VALID_TEAMS,
        help="Target team.",
    )

    # Mode or agent — one required
    dispatch = parser.add_mutually_exclusive_group(required=True)
    dispatch.add_argument(
        "--mode",
        help="Run mode — routes to the team orchestrator. Use --list-modes to see options.",
    )
    dispatch.add_argument(
        "--agent",
        help="Registry key of a specific agent — bypasses the orchestrator.",
    )

    parser.add_argument(
        "--task",
        required=True,
        help="Plain-English task description.",
    )

    # Context sources (all optional, resolved in order)
    ctx = parser.add_argument_group("context (optional — first match wins)")
    ctx.add_argument(
        "--project",
        default=None,
        help="Project name. Loads output/<project>/context.json.",
    )
    ctx.add_argument(
        "--context-file",
        dest="context_file",
        default=None,
        help="Path to a context file (JSON or plain text).",
    )
    ctx.add_argument(
        "--context",
        default=None,
        help="Inline context string (JSON or plain text).",
    )

    parser.add_argument(
        "--save",
        action="store_true",
        default=False,
        help=(
            "Save output to disk. "
            "Team flows → output/<project>/<team>/. "
            "Agent direct → output/<project>/agent_direct/. "
            "Requires --project."
        ),
    )

    parser.add_argument(
        "--list-modes",
        action="store_true",
        default=False,
        help="List available modes for --team and exit.",
    )

    return parser


def _list_modes(team: str):
    """Print available run_* functions from the team flow module."""
    flow_module_path, agent_flow_module_path = TEAM_FLOW_MAP[team]
    try:
        flow_mod = _import_module(flow_module_path)
        modes = sorted(
            name[4:] for name in dir(flow_mod)
            if name.startswith("run_") and callable(getattr(flow_mod, name))
        )
    except SystemExit:
        modes = []

    try:
        agent_mod = _import_module(agent_flow_module_path)
        agents = sorted(getattr(agent_mod, "AGENT_REGISTRY", {}).keys())
    except SystemExit:
        agents = []

    print(f"\n{'='*50}")
    print(f"Team: {team}")
    print(f"{'='*50}")
    print(f"Modes (--mode):   {', '.join(modes) if modes else 'none / module not yet built'}")
    print(f"Agents (--agent): {', '.join(agents) if agents else 'none / module not yet built'}")
    print()


def main():
    parser = build_parser()
    args = parser.parse_args()

    # --list-modes shortcut
    if args.list_modes:
        _list_modes(args.team)
        sys.exit(0)

    # Validate --save requires --project
    if args.save and not args.project:
        parser.error("--save requires --project to determine output path.")

    # Load context
    context = load_context(
        project=args.project,
        context_file=args.context_file,
        context_str=args.context,
    )

    # Dispatch
    if args.agent:
        _run_agent_flow(
            team=args.team,
            agent=args.agent,
            task=args.task,
            context=context,
            save=args.save,
        )
    else:
        _run_team_flow(
            team=args.team,
            mode=args.mode,
            task=args.task,
            context=context,
            save=args.save,
        )


if __name__ == "__main__":
    main()
