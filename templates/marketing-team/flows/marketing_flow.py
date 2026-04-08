"""
templates/marketing-team/flows/marketing_flow.py

Marketing Team — orchestrated flow.

Run modes:
    brief       Marketing Orchestrator → campaign brief, channel plan
    copy        Copywriter → copy package
    email       Email Specialist → email sequences, drip campaigns
    social      Social Media Specialist → post drafts, visual briefs
    video       Video Producer → scripts, visual direction briefs, music briefs
    analytics   Marketing Analyst → channel performance report, KPI dashboard
    campaign    Full campaign — Orchestrator → all specialists in sequence

HITL gates: POST, EMAIL, VIDEO
No deliverable publishes autonomously.

Usage:
    python templates/marketing-team/flows/marketing_flow.py \\
        --mode campaign --project parallaxedge \\
        --task "Q2 launch campaign for ParallaxEdge sports betting app"

Via pp_flow.py:
    python flows/pp_flow.py --team marketing --mode campaign \\
        --project parallaxedge --task "Q2 launch campaign"
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))

from core.context_loader import load_context, save_output  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

TEAM = "marketing"

# ---------------------------------------------------------------------------
# Pushover notification (mirrors ds_flow.py pattern)
# ---------------------------------------------------------------------------

def _notify(title: str, message: str):
    try:
        from core.notifications import send_pushover
        send_pushover(title=title, message=message)
    except Exception as e:
        logger.warning(f"Pushover notification failed: {e}")


# ---------------------------------------------------------------------------
# Agent imports (lazy — only the agents needed per mode are imported)
# ---------------------------------------------------------------------------

def _load_agents(keys: list):
    """Import and build agents by registry key. Returns dict of key → agent."""
    from agents.orchestrator.orchestrator import build_marketing_orchestrator
    from agents.analyst.analyst_agent import build_marketing_analyst
    from agents.copywriter.copywriter_agent import build_copywriter
    from agents.email.email_agent import build_email_specialist
    from agents.social.social_agent import build_social_media_specialist
    from agents.video.video_agent import build_video_producer

    builders = {
        "orchestrator":       build_marketing_orchestrator,
        "marketing_analyst":  build_marketing_analyst,
        "copywriter":         build_copywriter,
        "email_specialist":   build_email_specialist,
        "social_specialist":  build_social_media_specialist,
        "video_producer":     build_video_producer,
    }
    return {k: builders[k]() for k in keys if k in builders}


# ---------------------------------------------------------------------------
# Mode runners
# ---------------------------------------------------------------------------

def _run_mode(mode: str, agents_keys: list, task: str, context: dict, save: bool):
    """Shared runner for all single/multi-agent modes."""
    from crewai import Crew, Task

    agents = _load_agents(agents_keys)
    agent_list = list(agents.values())

    context_block = context.get("raw", "") or "No context provided."

    tasks = []
    for i, (key, agent) in enumerate(agents.items()):
        input_note = "" if i == 0 else f"Use the output of the previous task as input context.\n\n"
        tasks.append(Task(
            description=f"{input_note}{task}\n\nProject context:\n{context_block}",
            expected_output=(
                f"Complete, structured {key.replace('_', ' ')} deliverable. "
                f"No placeholders. All sections fully populated."
            ),
            agent=agent,
        ))

    crew = Crew(agents=agent_list, tasks=tasks, verbose=True)
    _notify(f"PP Marketing — {mode}", f"Starting {mode} run: {task[:80]}")

    result = crew.kickoff()
    output_str = str(result)

    print("\n" + "="*60)
    print(f"MARKETING TEAM OUTPUT — {mode.upper()}")
    print("="*60)
    print(output_str)
    print("="*60 + "\n")

    if save:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = save_output(output_str, context.get("project"), TEAM, f"{mode}_{timestamp}.md")
        if path:
            logger.info(f"Saved to {path}")

    _notify(f"PP Marketing — {mode} complete", f"Output ready. Project: {context.get('project') or 'ad-hoc'}")
    return output_str


def run_brief(context: dict, task: str, save: bool = False):
    return _run_mode("brief", ["orchestrator"], task, context, save)


def run_copy(context: dict, task: str, save: bool = False):
    return _run_mode("copy", ["copywriter"], task, context, save)


def run_email(context: dict, task: str, save: bool = False):
    return _run_mode("email", ["email_specialist"], task, context, save)


def run_social(context: dict, task: str, save: bool = False):
    return _run_mode("social", ["social_specialist"], task, context, save)


def run_video(context: dict, task: str, save: bool = False):
    return _run_mode("video", ["video_producer"], task, context, save)


def run_analytics(context: dict, task: str, save: bool = False):
    return _run_mode("analytics", ["marketing_analyst"], task, context, save)


def run_campaign(context: dict, task: str, save: bool = False):
    return _run_mode(
        "campaign",
        ["orchestrator", "marketing_analyst", "copywriter", "email_specialist",
         "social_specialist", "video_producer"],
        task, context, save,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

MODES = ["brief", "copy", "email", "social", "video", "analytics", "campaign"]


def build_parser():
    parser = argparse.ArgumentParser(
        prog="marketing_flow.py",
        description="Marketing Team flow. Routes to the orchestrator or specialist agents.",
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

    context = load_context(project=args.project, context_file=args.context_file, context_str=args.context)
    globals()[f"run_{args.mode}"](context=context, task=args.task, save=args.save)


if __name__ == "__main__":
    main()
