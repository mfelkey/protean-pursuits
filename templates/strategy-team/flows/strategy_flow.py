"""
templates/strategy-team/flows/strategy_flow.py

Strategy Team — orchestrated flow.

Run modes:
    positioning     Brand Positioning Strategist
    business_model  Business Model Designer
    competitive     Competitive Intelligence Analyst
    gtm             GTM Strategist
    okr             OKR Planner
    financial       Financial Strategist
    partnership     Partnership Strategist
    product         Product Strategist
    risk            Risk & Scenario Planner
    talent          Talent & Org Designer
    technology      Technology Strategist
    full            All agents in sequence

HITL gates: STRATEGY, OKR_CYCLE, COMPETITIVE
Authorized SME caller — may invoke the SME Group.
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

TEAM = "strategy"


def _notify(title, message):
    try:
        from core.notifications import send_pushover
        send_pushover(title=title, message=message)
    except Exception as e:
        logger.warning(f"Pushover notification failed: {e}")


def _load_agents(keys):
    from agents.orchestrator.orchestrator import build_strategy_orchestrator
    from agents.brand_positioning.brand_agent import build_brand_positioning_strategist
    from agents.business_model.business_model_agent import build_business_model_designer
    from agents.competitive_intel.competitive_intel_agent import build_competitive_intelligence_analyst
    from agents.financial_strategy.financial_strategy_agent import build_financial_strategist
    from agents.gtm.gtm_agent import build_gtm_strategist
    from agents.okr_planning.okr_agent import build_okr_planner
    from agents.partnership.partnership_agent import build_partnership_strategist
    from agents.product_strategy.product_strategy_agent import build_product_strategist
    from agents.risk_scenario.risk_agent import build_risk_scenario_planner
    from agents.talent_org.talent_agent import build_talent_org_designer
    from agents.technology_strategy.tech_strategy_agent import build_technology_strategist

    builders = {
        "orchestrator":                    build_strategy_orchestrator,
        "brand_positioning_strategist":    build_brand_positioning_strategist,
        "business_model_designer":         build_business_model_designer,
        "competitive_intel_analyst":       build_competitive_intelligence_analyst,
        "financial_strategist":            build_financial_strategist,
        "gtm_strategist":                  build_gtm_strategist,
        "okr_planner":                     build_okr_planner,
        "partnership_strategist":          build_partnership_strategist,
        "product_strategist":              build_product_strategist,
        "risk_scenario_planner":           build_risk_scenario_planner,
        "talent_org_designer":             build_talent_org_designer,
        "technology_strategist":           build_technology_strategist,
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
                f"Complete strategy deliverable from {key.replace('_', ' ')}. "
                f"No placeholders. All sections fully populated."
            ),
            agent=agent,
        ))

    crew = Crew(agents=agent_list, tasks=tasks, verbose=True)
    _notify(f"PP Strategy — {mode}", f"Starting: {task[:80]}")

    result = crew.kickoff()
    output_str = str(result)

    print("\n" + "="*60)
    print(f"STRATEGY TEAM OUTPUT — {mode.upper()}")
    print("="*60)
    print(output_str)
    print("="*60 + "\n")

    if save:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = save_output(output_str, context.get("project"), TEAM, f"{mode}_{timestamp}.md")
        if path:
            logger.info(f"Saved to {path}")

    _notify(f"PP Strategy — {mode} complete", f"Project: {context.get('project') or 'ad-hoc'}")
    return output_str


def run_positioning(context, task, save=False):
    return _run_mode("positioning", ["brand_positioning_strategist"], task, context, save)

def run_business_model(context, task, save=False):
    return _run_mode("business_model", ["business_model_designer"], task, context, save)

def run_competitive(context, task, save=False):
    return _run_mode("competitive", ["competitive_intel_analyst"], task, context, save)

def run_gtm(context, task, save=False):
    return _run_mode("gtm", ["gtm_strategist"], task, context, save)

def run_okr(context, task, save=False):
    return _run_mode("okr", ["okr_planner"], task, context, save)

def run_financial(context, task, save=False):
    return _run_mode("financial", ["financial_strategist"], task, context, save)

def run_partnership(context, task, save=False):
    return _run_mode("partnership", ["partnership_strategist"], task, context, save)

def run_product(context, task, save=False):
    return _run_mode("product", ["product_strategist"], task, context, save)

def run_risk(context, task, save=False):
    return _run_mode("risk", ["risk_scenario_planner"], task, context, save)

def run_talent(context, task, save=False):
    return _run_mode("talent", ["talent_org_designer"], task, context, save)

def run_technology(context, task, save=False):
    return _run_mode("technology", ["technology_strategist"], task, context, save)

def run_full(context, task, save=False):
    return _run_mode("full", [
        "orchestrator", "brand_positioning_strategist", "business_model_designer",
        "competitive_intel_analyst", "financial_strategist", "gtm_strategist",
        "okr_planner", "partnership_strategist", "product_strategist",
        "risk_scenario_planner", "talent_org_designer", "technology_strategist",
    ], task, context, save)


MODES = [
    "positioning", "business_model", "competitive", "gtm", "okr",
    "financial", "partnership", "product", "risk", "talent", "technology", "full",
]


def main():
    parser = argparse.ArgumentParser(prog="strategy_flow.py", description="Strategy Team flow.")
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
