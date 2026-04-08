"""
templates/marketing-team/flows/marketing_agent_flow.py

Marketing Team — single-agent direct flow.
Bypasses the Marketing Orchestrator; targets one agent by registry key.

Usage:
    python templates/marketing-team/flows/marketing_agent_flow.py \\
        --agent copywriter \\
        --task "Write App Store listing for ParallaxEdge — sports betting, iOS" \\
        --project parallaxedge [--save]

Via pp_flow.py:
    python flows/pp_flow.py --team marketing --agent copywriter \\
        --task "Write App Store listing" --project parallaxedge
"""

import argparse
import importlib
import logging
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))

from core.context_loader import load_context, save_agent_direct_output  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Agent registry
# ---------------------------------------------------------------------------
AGENT_REGISTRY = {
    "marketing_analyst": {
        "module":    "agents.analyst.analyst_agent",
        "build_fn":  "build_marketing_analyst",
        "description": "Marketing Analyst — channel performance, KPI dashboards",
    },
    "copywriter": {
        "module":    "agents.copywriter.copywriter_agent",
        "build_fn":  "build_copywriter",
        "description": "Copywriter — landing pages, ads, app store listings, push copy, campaign messaging",
    },
    "email_specialist": {
        "module":    "agents.email.email_agent",
        "build_fn":  "build_email_specialist",
        "description": "Email Specialist — sequences, drip campaigns, transactional templates",
    },
    "social_media_specialist": {
        "module":    "agents.social.social_agent",
        "build_fn":  "build_social_media_specialist",
        "description": "Social Media Specialist — post drafts, visual briefs (X, Instagram, TikTok, Discord)",
    },
    "video_producer": {
        "module":    "agents.video.video_agent",
        "build_fn":  "build_video_producer",
        "description": "Video Producer — scripts, visual direction briefs, music briefs",
    },
}


def run_agent(agent_key: str, task: str, context: dict, save: bool = False):
    if agent_key not in AGENT_REGISTRY:
        _print_registry()
        sys.exit(f"[marketing_agent_flow] ERROR: Unknown agent key '{agent_key}'.")

    entry = AGENT_REGISTRY[agent_key]
    logger.info(f"Marketing agent direct: {agent_key} — {entry['description']}")

    try:
        mod = importlib.import_module(entry["module"])
    except ModuleNotFoundError as e:
        sys.exit(
            f"[marketing_agent_flow] ERROR: Cannot import '{entry['module']}'.\n"
            f"  VERIFY the module path in AGENT_REGISTRY for key '{agent_key}'.\n"
            f"  Original error: {e}"
        )

    build_fn = getattr(mod, entry["build_fn"], None)
    if build_fn is None:
        sys.exit(
            f"[marketing_agent_flow] ERROR: '{entry['build_fn']}' not found in '{entry['module']}'.\n"
            f"  VERIFY the build_fn in AGENT_REGISTRY for key '{agent_key}'."
        )

    from crewai import Crew, Task

    agent = build_fn()
    task_obj = Task(
        description=(
            f"{task}\n\n"
            f"Context:\n{context.get('raw', '') or 'No context provided.'}"
        ),
        expected_output=(
            f"Complete, structured output from the {entry['description']}. "
            f"No placeholders. All sections fully populated."
        ),
        agent=agent,
    )

    crew = Crew(agents=[agent], tasks=[task_obj], verbose=True)
    result = crew.kickoff()
    output_str = str(result)

    print("\n" + "="*60)
    print(f"MARKETING AGENT DIRECT OUTPUT — {agent_key.upper()}")
    print("="*60)
    print(output_str)
    print("="*60 + "\n")

    if save:
        path = save_agent_direct_output(output_str, context.get("project"), agent_key)
        if path:
            logger.info(f"Saved to {path}")
        else:
            logger.warning("--save specified but no --project set. Output not saved.")

    return output_str


def _print_registry():
    print("\nAvailable Marketing agents:")
    for key, entry in AGENT_REGISTRY.items():
        print(f"  {key:<30} {entry['description']}")
    print()


def build_parser():
    parser = argparse.ArgumentParser(
        prog="marketing_agent_flow.py",
        description="Marketing Team — run a single agent directly.",
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

    context = load_context(project=args.project, context_file=args.context_file, context_str=args.context)
    run_agent(agent_key=args.agent, task=args.task, context=context, save=args.save)


if __name__ == "__main__":
    main()
