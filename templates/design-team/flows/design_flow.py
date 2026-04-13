"""
templates/design-team/flows/design_flow.py

Design Team — orchestrated flow.

Run modes:
    research        UX Researcher
    wireframe       UX Researcher → Wireframing Specialist
    visual          UI Designer → Brand Identity Specialist → Design System Architect
    motion          Motion & Animation Designer
    accessibility   Accessibility Specialist → Usability Analyst
    full            All agents in sequence

HITL gate: DESIGN_REVIEW on every mode.
Note: visual mode expects wireframes in context if run standalone.
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))
_TEAM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_TEAM_ROOT))

from core.context_loader import load_context, save_output  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

TEAM = "design"


def _notify(title, message):
    try:
        from core.notifications import send_pushover
        send_pushover(title=title, message=message)
    except Exception as e:
        logger.warning(f"Pushover notification failed: {e}")


def _load_agents(keys):
    from agents.orchestrator.orchestrator import build_design_orchestrator
    from agents.ux_research.ux_research_agent import build_ux_researcher
    from agents.wireframing.wireframing_agent import build_wireframing_specialist
    from agents.ui_design.ui_design_agent import build_ui_designer
    from agents.brand_identity.brand_identity_agent import build_brand_identity_specialist
    from agents.design_system.design_system_agent import build_design_system_architect
    from agents.motion_animation.motion_agent import build_motion_animation_designer
    from agents.accessibility.accessibility_agent import build_accessibility_specialist
    from agents.usability.usability_agent import build_usability_analyst

    builders = {
        "orchestrator":               build_design_orchestrator,
        "ux_researcher":              build_ux_researcher,
        "wireframing_specialist":     build_wireframing_specialist,
        "ui_designer":                build_ui_designer,
        "brand_identity_specialist":  build_brand_identity_specialist,
        "design_system_architect":    build_design_system_architect,
        "motion_designer":            build_motion_animation_designer,
        "accessibility_specialist":   build_accessibility_specialist,
        "usability_analyst":          build_usability_analyst,
    }
    return {k: builders[k]() for k in keys if k in builders}


def _run_mode(mode, agent_keys, task, context, save):
    from crewai import Crew, Task

    agents = _load_agents(agent_keys)
    agent_list = list(agents.values())
    context_block = context.get("raw", "") or "No context provided."

    tasks = []
    for i, (key, agent) in enumerate(agents.items()):
        prefix = "" if i == 0 else "Use the output of the previous task as input context.\n\n"
        tasks.append(Task(
            description=f"{prefix}{task}\n\nProject context:\n{context_block}",
            expected_output=(
                f"Complete design deliverable from {key.replace('_', ' ')}. "
                f"No placeholders. Ends with DESIGN_REVIEW gate summary."
            ),
            agent=agent,
        ))

    crew = Crew(agents=agent_list, tasks=tasks, verbose=True)
    _notify(f"PP Design — {mode}", f"Starting: {task[:80]}")

    result = crew.kickoff()
    output_str = str(result)

    print("\n" + "="*60)
    print(f"DESIGN TEAM OUTPUT — {mode.upper()}")
    print("="*60)
    print(output_str)
    print("="*60 + "\n")

    if save:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = save_output(output_str, context.get("project"), TEAM, f"{mode}_{timestamp}.md")
        if path:
            logger.info(f"Saved to {path}")

    _notify(f"PP Design — {mode} complete", f"Project: {context.get('project') or 'ad-hoc'}")
    return output_str


def run_research(context, task, save=False):
    return _run_mode("research", ["ux_researcher"], task, context, save)

def run_wireframe(context, task, save=False):
    return _run_mode("wireframe", ["ux_researcher", "wireframing_specialist"], task, context, save)

def run_visual(context, task, save=False):
    return _run_mode("visual", ["ui_designer", "brand_identity_specialist", "design_system_architect"], task, context, save)

def run_motion(context, task, save=False):
    return _run_mode("motion", ["motion_designer"], task, context, save)

def run_accessibility(context, task, save=False):
    return _run_mode("accessibility", ["accessibility_specialist", "usability_analyst"], task, context, save)

def run_full(context, task, save=False):
    return _run_mode("full", [
        "orchestrator", "ux_researcher", "wireframing_specialist",
        "ui_designer", "brand_identity_specialist", "design_system_architect",
        "motion_designer", "accessibility_specialist", "usability_analyst",
    ], task, context, save)


MODES = ["research", "wireframe", "visual", "motion", "accessibility", "full"]


def main():
    parser = argparse.ArgumentParser(prog="design_flow.py", description="Design Team flow.")
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
