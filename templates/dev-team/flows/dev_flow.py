"""
templates/dev-team/flows/dev_flow.py

Dev Team — orchestrated flow.

Run modes:
    plan        Full planning phase: PM → BA → Scrum Master → Tech Arch →
                Security Reviewer → UX Designer → UX Content Guide
    build       Build phase: Senior Dev → Backend → Frontend → DBA → DevOps
                ⚠️  Requires TAD in context (loads from project or fails fast)
    quality     QA phase: QA Lead → Test Automation Engineer
    finance     Finance Group sub-crew (full FSP)
    mobile      Mobile pipeline: Mobile UX → iOS → Android → RN Arch →
                RN Dev → Mobile DevOps → Mobile QA
                ⚠️  Requires UXD in context
    full        All phases in sequence (plan → finance → build → quality)

HITL gates: Security RED block (plan), CP-4.5 (finance), standard checkpoints

Usage:
    python templates/dev-team/flows/dev_flow.py \\
        --mode plan --project parallaxedge \\
        --task "Sports betting web app with user accounts and live odds feed"

    python templates/dev-team/flows/dev_flow.py \\
        --mode build --project parallaxedge
        # Loads TAD from output/parallaxedge/context.json automatically
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))

from core.context_loader import load_context, require_artifact, save_output  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

TEAM = "dev"


def _notify(title, message):
    try:
        from core.notifications import send_pushover
        send_pushover(title=title, message=message)
    except Exception as e:
        logger.warning(f"Pushover notification failed: {e}")


def _load_agents(keys):
    # Planning agents
    from agents.dev.strategy.product_manager import build_product_manager
    from agents.dev.strategy.business_analyst import build_business_analyst
    from agents.dev.strategy.scrum_master import build_scrum_master
    from agents.dev.strategy.technical_architect import build_technical_architect
    from agents.dev.strategy.security_reviewer import build_security_reviewer
    from agents.dev.strategy.ux_designer import build_ux_designer
    from agents.dev.strategy.ux_content_guide import build_ux_content_guide

    # Build agents
    from agents.dev.build.senior_developer import build_senior_developer
    from agents.dev.build.backend_developer import build_backend_developer
    from agents.dev.build.frontend_developer import build_frontend_developer
    from agents.dev.build.database_administrator import build_database_administrator
    from agents.dev.build.devops_engineer import build_devops_engineer

    # Quality agents
    from agents.dev.quality.qa_lead import build_qa_lead
    from agents.dev.quality.test_automation_engineer import build_test_automation_engineer

    # Docs agents
    from agents.dev.docs.devex_writer import build_devex_writer
    from agents.dev.docs.technical_writer import build_technical_writer

    # Mobile agents
    from agents.mobile.ux.mobile_ux_designer import build_mobile_ux_designer
    from agents.mobile.ios.ios_developer import build_ios_developer
    from agents.mobile.android.android_developer import build_android_developer
    from agents.mobile.rn.rn_architect import build_rn_architect
    from agents.mobile.rn.rn_developer import build_rn_developer
    from agents.mobile.devops.mobile_devops import build_mobile_devops
    from agents.mobile.qa.mobile_qa_specialist import build_mobile_qa_specialist

    builders = {
        # Planning
        "product_manager":          build_product_manager,
        "business_analyst":         build_business_analyst,
        "scrum_master":             build_scrum_master,
        "technical_architect":      build_technical_architect,
        "security_reviewer":        build_security_reviewer,
        "ux_designer":              build_ux_designer,
        "ux_content_guide":         build_ux_content_guide,
        # Build
        "senior_developer":         build_senior_developer,
        "backend_developer":        build_backend_developer,
        "frontend_developer":       build_frontend_developer,
        "dba":                      build_database_administrator,
        "devops_engineer":          build_devops_engineer,
        # Quality
        "qa_lead":                  build_qa_lead,
        "test_automation_engineer": build_test_automation_engineer,
        # Docs
        "devex_writer":             build_devex_writer,
        "technical_writer":         build_technical_writer,
        # Mobile
        "mobile_ux_designer":       build_mobile_ux_designer,
        "ios_developer":            build_ios_developer,
        "android_developer":        build_android_developer,
        "rn_architect":             build_rn_architect,
        "rn_developer":             build_rn_developer,
        "mobile_devops":            build_mobile_devops,
        "mobile_qa_specialist":     build_mobile_qa_specialist,
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
                f"Complete dev team deliverable from {key.replace('_', ' ')}. "
                f"No placeholder code. Every function complete. "
                f"TypeScript for frontend; Python type hints on all signatures."
            ),
            agent=agent,
        ))

    crew = Crew(agents=agent_list, tasks=tasks, verbose=True)
    _notify(f"PP Dev — {mode}", f"Starting: {task[:80]}")

    result = crew.kickoff()
    output_str = str(result)

    print("\n" + "="*60)
    print(f"DEV TEAM OUTPUT — {mode.upper()}")
    print("="*60)
    print(output_str)
    print("="*60 + "\n")

    if save:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = save_output(output_str, context.get("project"), TEAM, f"{mode}_{timestamp}.md")
        if path:
            logger.info(f"Saved to {path}")

    _notify(f"PP Dev — {mode} complete", f"Project: {context.get('project') or 'ad-hoc'}")
    return output_str


# ---------------------------------------------------------------------------
# Mode runners
# ---------------------------------------------------------------------------

def run_plan(context, task, save=False):
    return _run_mode("plan", [
        "product_manager", "business_analyst", "scrum_master",
        "technical_architect", "security_reviewer", "ux_designer", "ux_content_guide",
    ], task, context, save)


def run_build(context, task, save=False):
    # TAD is required for build — fail fast with a clear error
    require_artifact(
        context, "TAD",
        "--project <name> (loads output/<project>/context.json) "
        "or --context-file <path> containing TAD key"
    )
    return _run_mode("build", [
        "senior_developer", "backend_developer", "frontend_developer",
        "dba", "devops_engineer",
    ], task, context, save)


def run_quality(context, task, save=False):
    return _run_mode("quality", ["qa_lead", "test_automation_engineer"], task, context, save)


def run_finance(context, task, save=False):
    """Invoke the Finance Group sub-crew via its own orchestrator."""
    try:
        from agents.dev.finance.finance_orchestrator import run_finance_crew
        _notify("PP Dev — finance", f"Starting Finance Group: {task[:80]}")
        result = run_finance_crew(context=context, task=task, save=save)
        _notify("PP Dev — finance complete", f"FSP ready. Project: {context.get('project') or 'ad-hoc'}")
        return result
    except ImportError as e:
        sys.exit(
            f"[dev_flow] ERROR: Cannot import finance_orchestrator.\n"
            f"  Ensure templates/dev-team/agents/finance/ is on sys.path.\n"
            f"  Original error: {e}"
        )


def run_mobile(context, task, save=False):
    # UXD is required for mobile
    require_artifact(
        context, "UXD",
        "--project <name> (loads output/<project>/context.json) "
        "or --context-file <path> containing UXD key"
    )
    return _run_mode("mobile", [
        "mobile_ux_designer", "ios_developer", "android_developer",
        "rn_architect", "rn_developer", "mobile_devops", "mobile_qa_specialist",
    ], task, context, save)


def run_full(context, task, save=False):
    """Run all phases in sequence: plan → finance → build → quality."""
    logger.info("Dev full run: plan → finance → build → quality")
    _notify("PP Dev — full", f"Starting full pipeline: {task[:80]}")

    # Phase 1: Plan
    logger.info("Phase 1/4: plan")
    run_plan(context, task, save)

    # Reload context after plan so TAD/UXD artifacts are available
    from core.context_loader import load_context as _lc
    context = _lc(project=context.get("project"))

    # Phase 2: Finance
    logger.info("Phase 2/4: finance")
    run_finance(context, task, save)

    # Phase 3: Build (TAD now in context from plan phase)
    logger.info("Phase 3/4: build")
    run_build(context, task, save)

    # Phase 4: Quality
    logger.info("Phase 4/4: quality")
    run_quality(context, task, save)

    _notify("PP Dev — full complete", f"All phases done. Project: {context.get('project') or 'ad-hoc'}")


MODES = ["plan", "build", "quality", "finance", "mobile", "full"]


def main():
    parser = argparse.ArgumentParser(
        prog="dev_flow.py",
        description=(
            "Dev Team flow.\n\n"
            "build mode requires TAD in context.\n"
            "mobile mode requires UXD in context.\n"
            "full mode runs all phases in sequence (plan → finance → build → quality)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
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
