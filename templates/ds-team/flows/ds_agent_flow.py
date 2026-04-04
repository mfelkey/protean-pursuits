"""
templates/ds-team/flows/ds_agent_flow.py

DS Team — single-agent direct flow.
Bypasses the DS orchestrator; targets one agent by registry key.

Usage:
    python templates/ds-team/flows/ds_agent_flow.py \\
        --agent eda_analyst \\
        --task "Run EDA on Q1 churn dataset" \\
        --project parallaxedge \\
        [--save]

Via pp_flow.py:
    python flows/pp_flow.py --team ds --agent eda_analyst \\
        --task "Run EDA on Q1 churn dataset" --project parallaxedge
"""

# NOTE: Registry keys below are logical names derived from the design doc.
# VERIFY each key against the actual build_* function name in the agent file
# before running. Format: build_<registry_key> should exist in the agent module.

import argparse
import logging
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, "/home/mfelkey/ds-team")

from core.context_loader import load_context, save_agent_direct_output  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Agent registry
# REGISTRY KEY — verify each key against the actual build_* function name
# in the corresponding agent file under templates/ds-team/agents/
# ---------------------------------------------------------------------------
AGENT_REGISTRY = {
    "data_framer": {
        "module": "agents.data_framing.data_framing_agent",  # VERIFY path
        "build_fn": "build_data_framer",                     # VERIFY fn name
        "description": "Data Framing Specialist — scoping, complexity classification",
    },
    "data_evaluator": {
        "module": "agents.data_evaluation.data_evaluation_agent",  # VERIFY path
        "build_fn": "build_data_evaluator",                        # VERIFY fn name
        "description": "Data Evaluation Specialist — quality assessment, gap analysis",
    },
    "eda_analyst": {
        "module": "agents.eda.eda_agent",          # VERIFY path
        "build_fn": "build_eda_analyst",           # VERIFY fn name
        "description": "EDA Analyst — exploratory data analysis, distribution analysis",
    },
    "statistical_analyst": {
        "module": "agents.statistical_analysis.statistical_agent",  # VERIFY path
        "build_fn": "build_statistical_analyst",                    # VERIFY fn name
        "description": "Statistical Analyst — hypothesis testing, inferential statistics",
    },
    "ml_engineer": {
        "module": "agents.ml.ml_agent",      # VERIFY path
        "build_fn": "build_ml_engineer",     # VERIFY fn name
        "description": "ML Engineer — model selection, training, evaluation",
    },
    "reporting_analyst": {
        "module": "agents.reporting.reporting_agent",  # VERIFY path
        "build_fn": "build_reporting_analyst",         # VERIFY fn name
        "description": "Reporting Analyst — final reports, handoff packages",
    },
}


# ---------------------------------------------------------------------------
# Core runner
# ---------------------------------------------------------------------------

def run_agent(agent_key: str, task: str, context: dict, save: bool = False):
    """
    Instantiate a single DS agent and run it against the given task.
    Called directly or via pp_flow.py.
    """
    if agent_key not in AGENT_REGISTRY:
        _print_registry()
        sys.exit(f"[ds_agent_flow] ERROR: Unknown agent key '{agent_key}'.")

    entry = AGENT_REGISTRY[agent_key]
    logger.info(f"DS agent direct: {agent_key} — {entry['description']}")

    # Import agent module and build agent
    import importlib
    try:
        mod = importlib.import_module(entry["module"])
    except ModuleNotFoundError as e:
        sys.exit(
            f"[ds_agent_flow] ERROR: Cannot import agent module '{entry['module']}'.\n"
            f"  VERIFY the module path in AGENT_REGISTRY for key '{agent_key}'.\n"
            f"  Original error: {e}"
        )

    build_fn = getattr(mod, entry["build_fn"], None)
    if build_fn is None:
        sys.exit(
            f"[ds_agent_flow] ERROR: Build function '{entry['build_fn']}' not found "
            f"in module '{entry['module']}'.\n"
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
    print(f"DS AGENT DIRECT OUTPUT — {agent_key.upper()}")
    print("="*60)
    print(output_str)
    print("="*60 + "\n")

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


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def _print_registry():
    print("\nAvailable DS agents:")
    for key, entry in AGENT_REGISTRY.items():
        print(f"  {key:<25} {entry['description']}")
    print()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ds_agent_flow.py",
        description="DS Team — run a single agent directly, bypassing the orchestrator.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--agent", required=True, help="Agent registry key.")
    parser.add_argument("--task", required=True, help="Plain-English task description.")
    parser.add_argument("--project", default=None, help="Project name — loads output/<project>/context.json.")
    parser.add_argument("--context-file", dest="context_file", default=None, help="Path to context file.")
    parser.add_argument("--context", default=None, help="Inline context string.")
    parser.add_argument("--save", action="store_true", default=False, help="Save output to disk (requires --project).")
    parser.add_argument("--list-agents", action="store_true", default=False, help="List available agents and exit.")
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
