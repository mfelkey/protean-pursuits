"""
templates/video-team/flows/video_flow.py

Video Team — orchestrated flow.

Run modes:
    BRIEF_ONLY   Tool Analyst → Script → Visual → Audio (no API calls)
    SHORT_FORM   Full pipeline, <60s social (TikTok, Reels, Shorts)
    LONG_FORM    Full pipeline, 2–10min (YouTube, website)
    AVATAR       Full pipeline, avatar/spokesperson foregrounded
    DEMO         Script → Audio → API Engineer → Compliance (screen recording input)
    EXPLAINER    Full pipeline, animated explainer / motion graphics
    VOICEOVER    Script → Audio → API Engineer → Compliance (no visual generation)
    FULL         All modes sequenced as a campaign package

HITL gates:
    VIDEO_TOOL_SELECTION  — after Tool Analyst, before any creative work
    SCRIPT_REVIEW         — after Script Writer, before API calls
    VIDEO_FINAL           — after Compliance Reviewer, before any publish action

Usage:
    python templates/video-team/flows/video_flow.py \\
        --mode SHORT_FORM \\
        --project parallaxedge \\
        --task "60s TikTok ad for ParallaxEdge sports betting app launch"

Via pp_flow.py:
    python flows/pp_flow.py --team video --mode SHORT_FORM \\
        --project parallaxedge --task "60s TikTok ad" --save
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "teams" / "video-team"))

from core.context_loader import load_context, save_output  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

TEAM = "video"

MODES = [
    "BRIEF_ONLY", "SHORT_FORM", "LONG_FORM",
    "AVATAR", "DEMO", "EXPLAINER", "VOICEOVER", "FULL",
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
    from agents.orchestrator.orchestrator import build_video_orchestrator
    from agents.script.script_writer import build_script_writer
    from agents.visual.visual_director import build_visual_director
    from agents.audio.audio_producer import build_audio_producer
    from agents.avatar.avatar_producer import build_avatar_producer
    from agents.tool_intelligence.tool_analyst import build_tool_analyst
    from agents.compliance.compliance_reviewer import build_compliance_reviewer
    from agents.production.api_engineer import build_api_engineer

    builders = {
        "orchestrator":        build_video_orchestrator,
        "tool_analyst":        build_tool_analyst,
        "script_writer":       build_script_writer,
        "visual_director":     build_visual_director,
        "audio_producer":      build_audio_producer,
        "avatar_producer":     build_avatar_producer,
        "compliance_reviewer": build_compliance_reviewer,
        "api_engineer":        build_api_engineer,
    }
    return {k: builders[k]() for k in keys if k in builders}


# ── HITL gate wrapper ─────────────────────────────────────────────────────────

def _hitl_gate(gate_type: str, artifact_path: str, summary: str) -> bool:
    """
    Delegate to the orchestrator's HITL gate. Returns True if approved.
    Exits the pipeline if rejected.
    """
    try:
        from agents.orchestrator.orchestrator import request_human_approval
        approved = request_human_approval(
            gate_type=gate_type,
            artifact_path=artifact_path,
            summary=summary,
        )
    except Exception as e:
        logger.error(f"HITL gate error: {e}")
        approved = False

    if not approved:
        logger.error(f"[{gate_type}] Rejected or timed out. Pipeline halted.")
        sys.exit(1)

    return True


# ── Core runner ───────────────────────────────────────────────────────────────

def _run_mode(mode: str, agent_keys: list, task: str, context: dict,
              save: bool, gate_after: dict = None) -> str:
    """
    gate_after: {agent_key: gate_type} — fire a HITL gate after this agent's task.
    """
    from crewai import Crew, Task

    agents = _load_agents(agent_keys)
    context_block = context.get("raw", "") or "No context provided."
    gate_after = gate_after or {}

    tasks = []
    last_artifact_path = None

    for i, (key, agent) in enumerate(agents.items()):
        prefix = "" if i == 0 else "Use the output of the previous task as input context.\n\n"
        tasks.append(Task(
            description=(
                f"{prefix}Mode: {mode}\n\n"
                f"Task: {task}\n\n"
                f"Project context:\n{context_block}"
            ),
            expected_output=(
                f"Complete, handoff-ready deliverable from {key.replace('_', ' ')}. "
                f"No placeholders. Ends with numbered OPEN QUESTIONS section."
            ),
            agent=agent,
        ))

    _notify(f"PP Video — {mode}", f"Starting: {task[:80]}")

    # Run agents in sequence, inserting HITL gates where defined
    output_str = ""
    gate_keys = list(gate_after.keys())

    if gate_keys:
        # Run in segments, pausing at each gate
        agent_list = list(agents.items())
        gate_positions = {k: gate_after[k] for k in gate_keys if k in agents}

        segment_start = 0
        for gate_key, gate_type in gate_positions.items():
            gate_idx = list(agents.keys()).index(gate_key)
            segment_agents = [a for _, a in agent_list[segment_start:gate_idx + 1]]
            segment_tasks = tasks[segment_start:gate_idx + 1]

            if segment_agents:
                crew = Crew(agents=segment_agents, tasks=segment_tasks, verbose=True)
                result = crew.kickoff()
                output_str += str(result) + "\n\n"

                # Save segment artifact
                if save and context.get("project"):
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    last_artifact_path = save_output(
                        output_str, context.get("project"), TEAM,
                        f"{mode}_{gate_key}_{ts}.md"
                    )

            _hitl_gate(
                gate_type=gate_type,
                artifact_path=last_artifact_path or "output not yet saved",
                summary=f"{mode} — {gate_key} complete. Review before proceeding.",
            )
            segment_start = gate_idx + 1

        # Run remaining agents after last gate
        if segment_start < len(agent_list):
            remaining_agents = [a for _, a in agent_list[segment_start:]]
            remaining_tasks = tasks[segment_start:]
            if remaining_agents:
                crew = Crew(agents=remaining_agents, tasks=remaining_tasks, verbose=True)
                result = crew.kickoff()
                output_str += str(result)
    else:
        # No gates — run all at once
        crew = Crew(agents=list(agents.values()), tasks=tasks, verbose=True)
        result = crew.kickoff()
        output_str = str(result)

    print("\n" + "=" * 60)
    print(f"VIDEO TEAM OUTPUT — {mode}")
    print("=" * 60)
    print(output_str)
    print("=" * 60 + "\n")

    if save and context.get("project"):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = save_output(output_str, context.get("project"), TEAM,
                           f"{mode}_{ts}.md")
        if path:
            logger.info(f"Saved to {path}")

    _notify(f"PP Video — {mode} complete",
            f"Project: {context.get('project') or 'ad-hoc'}")
    return output_str


# ── Mode runners ──────────────────────────────────────────────────────────────

def run_BRIEF_ONLY(context: dict, task: str, save: bool = False) -> str:
    """Tool Analyst → Script → Visual → Audio. No API calls, no HITL gates."""
    return _run_mode(
        mode="BRIEF_ONLY",
        agent_keys=["tool_analyst", "script_writer", "visual_director", "audio_producer"],
        task=task,
        context=context,
        save=save,
        gate_after={
            "tool_analyst": "VIDEO_TOOL_SELECTION",
            "script_writer": "SCRIPT_REVIEW",
        },
    )


def run_SHORT_FORM(context: dict, task: str, save: bool = False) -> str:
    """Full pipeline for <60s social content. Gates: TOOL_SELECTION, SCRIPT_REVIEW, VIDEO_FINAL."""
    return _run_mode(
        mode="SHORT_FORM",
        agent_keys=[
            "tool_analyst", "script_writer", "visual_director",
            "audio_producer", "compliance_reviewer", "api_engineer",
        ],
        task=task,
        context=context,
        save=save,
        gate_after={
            "tool_analyst":        "VIDEO_TOOL_SELECTION",
            "script_writer":       "SCRIPT_REVIEW",
            "compliance_reviewer": "VIDEO_FINAL",
        },
    )


def run_LONG_FORM(context: dict, task: str, save: bool = False) -> str:
    """Full pipeline for 2–10min content (YouTube, website)."""
    return _run_mode(
        mode="LONG_FORM",
        agent_keys=[
            "tool_analyst", "script_writer", "visual_director",
            "audio_producer", "compliance_reviewer", "api_engineer",
        ],
        task=task,
        context=context,
        save=save,
        gate_after={
            "tool_analyst":        "VIDEO_TOOL_SELECTION",
            "script_writer":       "SCRIPT_REVIEW",
            "compliance_reviewer": "VIDEO_FINAL",
        },
    )


def run_AVATAR(context: dict, task: str, save: bool = False) -> str:
    """Avatar/spokesperson pipeline. Replaces Visual Director with Avatar Producer."""
    return _run_mode(
        mode="AVATAR",
        agent_keys=[
            "tool_analyst", "script_writer", "avatar_producer",
            "audio_producer", "compliance_reviewer", "api_engineer",
        ],
        task=task,
        context=context,
        save=save,
        gate_after={
            "tool_analyst":        "VIDEO_TOOL_SELECTION",
            "script_writer":       "SCRIPT_REVIEW",
            "compliance_reviewer": "VIDEO_FINAL",
        },
    )


def run_DEMO(context: dict, task: str, save: bool = False) -> str:
    """Screen recording input. Script + Audio + API Engineer + Compliance. No visual generation."""
    return _run_mode(
        mode="DEMO",
        agent_keys=[
            "script_writer", "audio_producer",
            "api_engineer", "compliance_reviewer",
        ],
        task=task,
        context=context,
        save=save,
        gate_after={
            "script_writer":       "SCRIPT_REVIEW",
            "compliance_reviewer": "VIDEO_FINAL",
        },
    )


def run_EXPLAINER(context: dict, task: str, save: bool = False) -> str:
    """Animated explainer / motion graphics. Same pipeline as LONG_FORM."""
    return _run_mode(
        mode="EXPLAINER",
        agent_keys=[
            "tool_analyst", "script_writer", "visual_director",
            "audio_producer", "compliance_reviewer", "api_engineer",
        ],
        task=task,
        context=context,
        save=save,
        gate_after={
            "tool_analyst":        "VIDEO_TOOL_SELECTION",
            "script_writer":       "SCRIPT_REVIEW",
            "compliance_reviewer": "VIDEO_FINAL",
        },
    )


def run_VOICEOVER(context: dict, task: str, save: bool = False) -> str:
    """Voiceover-only. Script + Audio + API Engineer + Compliance. No visual generation."""
    return _run_mode(
        mode="VOICEOVER",
        agent_keys=[
            "script_writer", "audio_producer",
            "api_engineer", "compliance_reviewer",
        ],
        task=task,
        context=context,
        save=save,
        gate_after={
            "script_writer":       "SCRIPT_REVIEW",
            "compliance_reviewer": "VIDEO_FINAL",
        },
    )


def run_FULL(context: dict, task: str, save: bool = False) -> str:
    """
    Full campaign package — all modes sequenced.
    Runs BRIEF_ONLY first for planning, then SHORT_FORM, LONG_FORM, AVATAR in sequence.
    Each sub-run fires its own HITL gates.
    """
    logger.info("Video FULL run: BRIEF_ONLY → SHORT_FORM → LONG_FORM → AVATAR")
    _notify("PP Video — FULL", f"Starting full campaign: {task[:80]}")

    results = []
    for mode_fn, label in [
        (run_BRIEF_ONLY, "BRIEF_ONLY"),
        (run_SHORT_FORM,  "SHORT_FORM"),
        (run_LONG_FORM,   "LONG_FORM"),
        (run_AVATAR,      "AVATAR"),
    ]:
        logger.info(f"FULL sub-run: {label}")
        result = mode_fn(context=context, task=task, save=save)
        results.append(f"=== {label} ===\n{result}")

    combined = "\n\n".join(results)

    if save and context.get("project"):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = save_output(combined, context.get("project"), TEAM,
                           f"FULL_{ts}.md")
        if path:
            logger.info(f"Full campaign saved to {path}")

    _notify("PP Video — FULL complete",
            f"Campaign package ready. Project: {context.get('project') or 'ad-hoc'}")
    return combined


# ── CLI ───────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="video_flow.py",
        description=(
            "Video Team flow.\n\n"
            "HITL gates fire automatically:\n"
            "  VIDEO_TOOL_SELECTION — after Tool Analyst (modes with tool evaluation)\n"
            "  SCRIPT_REVIEW        — after Script Writer (all modes with script)\n"
            "  VIDEO_FINAL          — after Compliance Reviewer (all full-pipeline modes)"
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

    mode_fn = globals()[f"run_{args.mode}"]
    mode_fn(context=context, task=args.task, save=args.save)


if __name__ == "__main__":
    main()
