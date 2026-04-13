"""
templates/video-team/flows/video_agent_flow.py

Video Team — single-agent direct flow.
Bypasses the Video Orchestrator; targets one agent by registry key.

Usage:
    python templates/video-team/flows/video_agent_flow.py \\
        --agent script_writer \\
        --task "60s TikTok script for ParallaxEdge sports betting app launch" \\
        --project parallaxedge [--save]

Via pp_flow.py:
    python flows/pp_flow.py --team video --agent script_writer \\
        --task "60s TikTok script" --project parallaxedge
"""

import argparse
import logging
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))
_TEAM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_TEAM_ROOT))

from core.context_loader import load_context, save_agent_direct_output  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# ── Agent registry ────────────────────────────────────────────────────────────

AGENT_REGISTRY = {
    "script_writer": {
        "module":      "agents.script.script_writer",
        "build_fn":    "build_script_writer",
        "description": "Script & Narrative Writer — scripts, voiceovers, on-screen copy, compliance checklist",
        "tier":        "TIER1",
    },
    "visual_director": {
        "module":      "agents.visual.visual_director",
        "build_fn":    "build_visual_director",
        "description": "Visual Director — Visual Direction Briefs, shot types, motion direction, AI prompt strings",
        "tier":        "TIER1",
    },
    "audio_producer": {
        "module":      "agents.audio.audio_producer",
        "build_fn":    "build_audio_producer",
        "description": "Audio & Music Producer — Audio Production Briefs, music prompts, TTS direction, SFX cue sheet",
        "tier":        "TIER1",
    },
    "avatar_producer": {
        "module":      "agents.avatar.avatar_producer",
        "build_fn":    "build_avatar_producer",
        "description": "Avatar & Spokesperson Producer — Avatar Production Briefs, HeyGen/Synthesia execution params",
        "tier":        "TIER1",
    },
    "tool_analyst": {
        "module":      "agents.tool_intelligence.tool_analyst",
        "build_fn":    "build_tool_analyst",
        "description": "Tool Intelligence Analyst — Tool Recommendation Report, scored tool rankings, API signatures",
        "tier":        "TIER1",
    },
    "compliance_reviewer": {
        "module":      "agents.compliance.compliance_reviewer",
        "build_fn":    "build_compliance_reviewer",
        "description": "Compliance & Brand Reviewer — Compliance Report (PASS/CONDITIONAL/FAIL), brand + platform + legal review",
        "tier":        "TIER1",
    },
    "api_engineer": {
        "module":      "agents.production.api_engineer",
        "build_fn":    "build_api_engineer",
        "description": "API Production Engineer — executes approved video/audio APIs, saves assets, produces assembly manifest",
        "tier":        "TIER2",
    },
}


# ── Runner ────────────────────────────────────────────────────────────────────

def run_agent(agent_key: str, task: str, context: dict, save: bool = False) -> str:
    if agent_key not in AGENT_REGISTRY:
        _print_registry()
        sys.exit(f"[video_agent_flow] ERROR: Unknown agent key '{agent_key}'.")

    entry = AGENT_REGISTRY[agent_key]
    logger.info(f"Video agent direct: {agent_key} — {entry['description']}")

    # ── Avatar producer check — requires avatar_config ────────────────────────
    if agent_key == "avatar_producer":
        avatar_config = context.get("data", {}).get("avatar_config", {})
        if not avatar_config:
            logger.warning(
                "avatar_producer requires 'avatar_config' in context. "
                "Proceeding — agent will flag this as a blocking open question."
            )

    import importlib
    try:
        mod = importlib.import_module(entry["module"])
    except ModuleNotFoundError as e:
        sys.exit(
            f"[video_agent_flow] ERROR: Cannot import '{entry['module']}'.\n"
            f"  Original error: {e}"
        )

    build_fn = getattr(mod, entry["build_fn"], None)
    if build_fn is None:
        sys.exit(
            f"[video_agent_flow] ERROR: '{entry['build_fn']}' not found "
            f"in '{entry['module']}'."
        )

    from crewai import Crew, Task

    agent = build_fn()

    task_obj = Task(
        description=(
            f"{task}\n\n"
            f"Context:\n{context.get('raw', '') or 'No context provided.'}"
        ),
        expected_output=(
            f"Complete, handoff-ready deliverable from {entry['description']}. "
            f"No placeholders. Ends with numbered OPEN QUESTIONS section."
        ),
        agent=agent,
    )

    crew = Crew(agents=[agent], tasks=[task_obj], verbose=True)
    result = crew.kickoff()
    output_str = str(result)

    print("\n" + "=" * 60)
    print(f"VIDEO AGENT DIRECT OUTPUT — {agent_key.upper()}")
    print("=" * 60)
    print(output_str)
    print("=" * 60 + "\n")

    if save:
        path = save_agent_direct_output(
            content=output_str,
            project=context.get("project"),
            agent_key=agent_key,
        )
        if path:
            logger.info(f"Saved to {path}")
        else:
            logger.warning("--save specified but no --project set. Output not saved.")

    return output_str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _print_registry():
    print("\nAvailable Video agents:")
    for key, entry in AGENT_REGISTRY.items():
        tier_label = f"[{entry['tier']}]"
        print(f"  {key:<25} {tier_label:<8} {entry['description']}")
    print()


# ── CLI ───────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="video_agent_flow.py",
        description=(
            "Video Team — run a single agent directly, bypassing the orchestrator.\n\n"
            "Note: API Engineer (api_engineer) makes live external API calls.\n"
            "      Tool Analyst (tool_analyst) performs web search at runtime.\n"
            "      Avatar Producer (avatar_producer) requires avatar_config in context."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--agent", required=True, help="Agent registry key.")
    parser.add_argument("--task", required=True, help="Plain-English task description.")
    parser.add_argument("--project", default=None,
                        help="Project name — loads output/<project>/context.json.")
    parser.add_argument("--context-file", dest="context_file", default=None,
                        help="Path to context file (JSON or plain text).")
    parser.add_argument("--context", default=None, help="Inline context string.")
    parser.add_argument("--save", action="store_true", default=False,
                        help="Save output to disk (requires --project).")
    parser.add_argument("--list-agents", action="store_true", default=False,
                        help="List available agents and exit.")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.list_agents:
        _print_registry()
        sys.exit(0)

    if args.save and not args.project:
        parser.error("--save requires --project.")

    context = load_context(
        project=args.project,
        context_file=args.context_file,
        context_str=args.context,
    )

    run_agent(
        agent_key=args.agent,
        task=args.task,
        context=context,
        save=args.save,
    )


if __name__ == "__main__":
    main()
