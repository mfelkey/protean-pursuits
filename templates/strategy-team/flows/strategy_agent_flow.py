"""
templates/strategy-team/flows/strategy_agent_flow.py

Strategy Team — single-agent direct flow.
"""

import argparse
import importlib
import logging
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, "/home/mfelkey/strategy-team")

from core.context_loader import load_context, save_agent_direct_output  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

AGENT_REGISTRY = {
    "brand_positioning_strategist": {
        "module":   "agents.brand_positioning.brand_agent",
        "build_fn": "build_brand_positioning_strategist",
        "description": "Brand Positioning Strategist — positioning framework",
    },
    "business_model_designer": {
        "module":   "agents.business_model.business_model_agent",
        "build_fn": "build_business_model_designer",
        "description": "Business Model Designer — business model canvas + narrative",
    },
    "competitive_intel_analyst": {
        "module":   "agents.competitive_intel.competitive_intel_agent",
        "build_fn": "build_competitive_intelligence_analyst",
        "description": "Competitive Intelligence Analyst — landscape, positioning gaps",
    },
    "financial_strategist": {
        "module":   "agents.financial_strategy.financial_strategy_agent",
        "build_fn": "build_financial_strategist",
        "description": "Financial Strategist — financial strategy, funding roadmap",
    },
    "gtm_strategist": {
        "module":   "agents.gtm.gtm_agent",
        "build_fn": "build_gtm_strategist",
        "description": "GTM Strategist — GTM plan, channel strategy, launch sequencing",
    },
    "okr_planner": {
        "module":   "agents.okr_planning.okr_agent",
        "build_fn": "build_okr_planner",
        "description": "OKR Planner — OKR framework, measurement plan",
    },
    "partnership_strategist": {
        "module":   "agents.partnership.partnership_agent",
        "build_fn": "build_partnership_strategist",
        "description": "Partnership Strategist — partnership framework, target list",
    },
    "product_strategist": {
        "module":   "agents.product_strategy.product_strategy_agent",
        "build_fn": "build_product_strategist",
        "description": "Product Strategist — product strategy, roadmap",
    },
    "risk_scenario_planner": {
        "module":   "agents.risk_scenario.risk_agent",
        "build_fn": "build_risk_scenario_planner",
        "description": "Risk & Scenario Planner — risk register, scenario analysis",
    },
    "talent_org_designer": {
        "module":   "agents.talent_org.talent_agent",
        "build_fn": "build_talent_org_designer",
        "description": "Talent & Org Designer — org design, hiring plan",
    },
    "technology_strategist": {
        "module":   "agents.technology_strategy.tech_strategy_agent",
        "build_fn": "build_technology_strategist",
        "description": "Technology Strategist — technology strategy, build/buy/partner rec",
    },
}


def run_agent(agent_key: str, task: str, context: dict, save: bool = False):
    if agent_key not in AGENT_REGISTRY:
        _print_registry()
        sys.exit(f"[strategy_agent_flow] ERROR: Unknown agent key '{agent_key}'.")

    entry = AGENT_REGISTRY[agent_key]
    logger.info(f"Strategy agent direct: {agent_key}")

    try:
        mod = importlib.import_module(entry["module"])
    except ModuleNotFoundError as e:
        sys.exit(f"[strategy_agent_flow] ERROR: Cannot import '{entry['module']}'.\n  Original error: {e}")

    build_fn = getattr(mod, entry["build_fn"], None)
    if build_fn is None:
        sys.exit(f"[strategy_agent_flow] ERROR: '{entry['build_fn']}' not found in '{entry['module']}'.")

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
    print(f"STRATEGY AGENT DIRECT OUTPUT — {agent_key.upper()}")
    print("="*60)
    print(output_str)
    print("="*60 + "\n")

    if save:
        path = save_agent_direct_output(output_str, context.get("project"), agent_key)
        if path:
            logger.info(f"Saved to {path}")

    return output_str


def _print_registry():
    print("\nAvailable Strategy agents:")
    for key, entry in AGENT_REGISTRY.items():
        print(f"  {key:<35} {entry['description']}")
    print()


def main():
    parser = argparse.ArgumentParser(prog="strategy_agent_flow.py", description="Strategy Team — single agent direct.")
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
