"""
templates/video-team/flows/video_flow.py

Video Team — orchestrated flow.

⚠️  STUB — pending video team template build.
    Mode names and structure are locked in. Wire agent imports once
    templates/video-team/agents/ is committed.

Run modes:
    script          Script Writer
    visual          Visual Director
    audio           Audio Producer
    avatar          Avatar Producer
    production      API Engineer
    compliance      Compliance Reviewer
    full            All agents in sequence

HITL gate: VIDEO
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, "/home/mfelkey/video-team")

from core.context_loader import load_context, save_output  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

TEAM = "video"

MODES = ["script", "visual", "audio", "avatar", "production", "compliance", "full"]

# ---------------------------------------------------------------------------
# TODO: Wire agent imports once templates/video-team/agents/ is committed.
# Follow the pattern in marketing_flow.py — one import per agent, lazy-loaded
# inside _load_agents().
# ---------------------------------------------------------------------------


def _notify(title, message):
    try:
        from core.notifications import send_pushover
        send_pushover(title=title, message=message)
    except Exception as e:
        logger.warning(f"Pushover notification failed: {e}")


def _load_agents(keys):  # TODO: implement when agent files are committed
    raise NotImplementedError(
        "[video_flow] Agent imports not yet wired. "
        "Build templates/video-team/agents/ first, then update _load_agents()."
    )


def _run_mode(mode, agent_keys, task, context, save):
    from crewai import Crew, Task  # TODO: remove stub guard when wired

    agents = _load_agents(agent_keys)  # will raise NotImplementedError until wired
    agent_list = list(agents.values())
    context_block = context.get("raw", "") or "No context provided."

    tasks = []
    for i, (key, agent) in enumerate(agents.items()):
        prefix = "" if i == 0 else "Use the output of the previous task as input context.\n\n"
        tasks.append(Task(
            description=f"{prefix}{task}\n\nProject context:\n{context_block}",
            expected_output=(
                f"Complete video deliverable from {key.replace('_', ' ')}. "
                f"No placeholders. Ends with VIDEO gate summary."
            ),
            agent=agent,
        ))

    crew = Crew(agents=agent_list, tasks=tasks, verbose=True)
    _notify(f"PP Video — {mode}", f"Starting: {task[:80]}")

    result = crew.kickoff()
    output_str = str(result)

    print("\n" + "="*60)
    print(f"VIDEO TEAM OUTPUT — {mode.upper()}")
    print("="*60)
    print(output_str)
    print("="*60 + "\n")

    if save:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = save_output(output_str, context.get("project"), TEAM, f"{mode}_{timestamp}.md")
        if path:
            logger.info(f"Saved to {path}")

    _notify(f"PP Video — {mode} complete", f"Project: {context.get('project') or 'ad-hoc'}")
    return output_str


# Mode stubs — names locked in, bodies delegate to _run_mode when wired

def run_script(context, task, save=False):
    return _run_mode("script", ["script_writer"], task, context, save)

def run_visual(context, task, save=False):
    return _run_mode("visual", ["visual_director"], task, context, save)

def run_audio(context, task, save=False):
    return _run_mode("audio", ["audio_producer"], task, context, save)

def run_avatar(context, task, save=False):
    return _run_mode("avatar", ["avatar_producer"], task, context, save)

def run_production(context, task, save=False):
    return _run_mode("production", ["api_engineer"], task, context, save)

def run_compliance(context, task, save=False):
    return _run_mode("compliance", ["compliance_reviewer"], task, context, save)

def run_full(context, task, save=False):
    return _run_mode("full", [
        "orchestrator", "script_writer", "visual_director", "audio_producer",
        "avatar_producer", "api_engineer", "compliance_reviewer",
    ], task, context, save)


def main():
    parser = argparse.ArgumentParser(prog="video_flow.py", description="Video Team flow. ⚠️ STUB.")
    parser.add_argument("--mode", required=True, choices=MODES)
    parser.add_argument("--task", required=True)
    parser.add_argument("--project", default=None)
    parser.add_argument("--context-file", dest="context_file", default=None)
    parser.add_argument("--context", default=None)
    parser.add_argument("--save", action="store_true", default=False)
    args = parser.parse_args()

    if args.save and not args.project:
        parser.error("--save requires --project.")

    context = load_context(project=args.project, context_file=args.context_file, context_str=args.context)
    globals()[f"run_{args.mode}"](context=context, task=args.task, save=args.save)


if __name__ == "__main__":
    main()
