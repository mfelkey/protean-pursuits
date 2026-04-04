"""
templates/video-team/flows/video_agent_flow.py

Video Team — single-agent direct flow.

⚠️  STUB — pending video team template build.
    Registry keys and descriptions are locked in. Wire module paths and
    build_fn names once templates/video-team/agents/ is committed.
"""

import argparse
import importlib
import logging
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, "/home/mfelkey/video-team")

from core.context_loader import load_context, save_agent_direct_output  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Agent registry
# TODO: Fill in module paths and build_fn names once agent files are committed.
# ---------------------------------------------------------------------------
AGENT_REGISTRY = {
    "script_writer": {
        "module":   "agents.script.script_writer",          # TODO: VERIFY path
        "build_fn": "build_script_writer",                  # TODO: VERIFY fn name
        "description": "Script Writer — video scripts",
    },
    "visual_director": {
        "module":   "agents.visual.visual_director",        # TODO: VERIFY path
        "build_fn": "build_visual_director",                # TODO: VERIFY fn name
        "description": "Visual Director — shot lists, visual direction briefs",
    },
    "audio_producer": {
        "module":   "agents.audio.audio_producer",          # TODO: VERIFY path
        "build_fn": "build_audio_producer",                 # TODO: VERIFY fn name
        "description": "Audio Producer — music briefs, SFX notes",
    },
    "avatar_producer": {
        "module":   "agents.avatar.avatar_producer",        # TODO: VERIFY path
        "build_fn": "build_avatar_producer",                # TODO: VERIFY fn name
        "description": "Avatar Producer — avatar direction briefs",
    },
    "tool_intelligence_analyst": {
        "module":   "agents.tool_intelligence.tool_analyst",  # TODO: VERIFY path
        "build_fn": "build_tool_intelligence_analyst",        # TODO: VERIFY fn name
        "description": "Tool Intelligence Analyst — production tooling recommendations",
    },
    "api_engineer": {
        "module":   "agents.production.api_engineer",       # TODO: VERIFY path
        "build_fn": "build_api_engineer",                   # TODO: VERIFY fn name
        "description": "API Engineer — production pipeline config",
    },
    "compliance_reviewer": {
        "module":   "agents.compliance.compliance_reviewer",  # TODO: VERIFY path
        "build_fn": "build_compliance_reviewer",              # TODO: VERIFY fn name
        "description": "Compliance Reviewer — compliance clearance",
    },
}


def run_agent(agent_key: str, task: str, context: dict, save: bool = False):
    if agent_key not in AGENT_REGISTRY:
        _print_registry()
        sys.exit(f"[video_agent_flow] ERROR: Unknown agent key '{agent_key}'.")

    entry = AGENT_REGISTRY[agent_key]
    logger.info(f"Video agent direct: {agent_key}")

    try:
        mod = importlib.import_module(entry["module"])
    except ModuleNotFoundError as e:
        sys.exit(
            f"[video_agent_flow] ERROR: Cannot import '{entry['module']}'.\n"
            f"  This is a stub — verify the module path once agent files are committed.\n"
            f"  Original error: {e}"
        )

    build_fn = getattr(mod, entry["build_fn"], None)
    if build_fn is None:
        sys.exit(
            f"[video_agent_flow] ERROR: '{entry['build_fn']}' not found in '{entry['module']}'.\n"
            f"  TODO: Verify build_fn name once agent files are committed."
        )

    from crewai import Crew, Task

    agent = build_fn()
    task_obj = Task(
        description=f"{task}\n\nContext:\n{context.get('raw', '') or 'No context provided.'}",
        expected_output=f"Complete deliverable from {entry['description']}. No placeholders.",
        agent=agent,
    )

    crew = Crew(agents=[agent], tasks=[task_obj], verbose=True)
    result = crew.kickoff()
    output_str = str(result)

    print("\n" + "="*60)
    print(f"VIDEO AGENT DIRECT OUTPUT — {agent_key.upper()}")
    print("="*60)
    print(output_str)
    print("="*60 + "\n")

    if save:
        path = save_agent_direct_output(output_str, context.get("project"), agent_key)
        if path:
            logger.info(f"Saved to {path}")

    return output_str


def _print_registry():
    print("\nAvailable Video agents (⚠️ STUB — module paths not yet verified):")
    for key, entry in AGENT_REGISTRY.items():
        print(f"  {key:<30} {entry['description']}")
    print()


def main():
    parser = argparse.ArgumentParser(prog="video_agent_flow.py", description="Video Team — single agent direct. ⚠️ STUB.")
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
