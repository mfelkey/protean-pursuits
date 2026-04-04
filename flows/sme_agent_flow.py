"""
flows/sme_agent_flow.py

SME Group — single-agent direct flow.
Targets one domain specialist by registry key via run_sme_consult().

HITL behavior:
  - Single consult: no HITL gate (consult mode)
  - This flow always uses consult mode (single agent)
  - For multi-SME synthesis with HITL, use sme_flow.py --mode crew

Usage:
    python flows/sme_agent_flow.py \\
        --agent pga \\
        --task "What are the key value betting angles for LIV Golf?" \\
        --project parallaxedge [--save]

Via pp_flow.py:
    python flows/pp_flow.py --team sme --agent pga \\
        --task "Key value betting angles for LIV Golf" \\
        --project parallaxedge
"""

import argparse
import logging
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from core.context_loader import load_context, save_agent_direct_output  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

CALLER = "sme_flow"

# ── Agent registry — mirrors sme_orchestrator.py ──────────────────────────────
# Each key maps directly to the SME registry in sme_orchestrator.py.
# Description format: "DOMAIN_ASSESSMENT: HIGH/MEDIUM/LOW ... CROSS-TEAM FLAGS ... OPEN QUESTIONS"

AGENT_REGISTRY = {
    "sports_betting": {
        "description": "Sports Betting Expert — cross-sport industry authority, all regulated markets worldwide",
        "domain":      "Sports betting industry",
    },
    "world_football": {
        "description": "World Football & Soccer Betting Expert — all global leagues, confederations, Asian handicap",
        "domain":      "Soccer / football betting",
    },
    "nba_ncaa_basketball": {
        "description": "NBA & NCAA Men's Basketball Betting Expert — NBA + March Madness",
        "domain":      "Basketball betting",
    },
    "nfl_ncaa_football": {
        "description": "NFL & NCAA Football Betting Expert — NFL + CFP, college football",
        "domain":      "American football betting",
    },
    "mlb": {
        "description": "MLB Betting Expert — MLB + NPB + KBO + CPBL",
        "domain":      "Baseball betting",
    },
    "nhl_ncaa_hockey": {
        "description": "NHL & NCAA Men's Hockey Betting Expert — NHL + NCAA + KHL + Euro leagues",
        "domain":      "Hockey betting",
    },
    "mma": {
        "description": "MMA Betting Expert — UFC + Bellator + ONE + Rizin",
        "domain":      "MMA betting",
    },
    "tennis": {
        "description": "Tennis Betting Expert — ATP + WTA + Challengers + ITF",
        "domain":      "Tennis betting",
    },
    "world_rugby": {
        "description": "World Rugby Betting Expert — Union + League, Six Nations, NRL, State of Origin",
        "domain":      "Rugby betting",
    },
    "cricket": {
        "description": "Cricket Betting Expert — Test + ODI + T20 + IPL, all formats and nations",
        "domain":      "Cricket betting",
    },
    "wnba_ncaa_womens_basketball": {
        "description": "WNBA & NCAA Women's Basketball Betting Expert",
        "domain":      "Women's basketball betting",
    },
    "thoroughbred_horse_racing": {
        "description": "Thoroughbred Horse Racing Betting Expert — US + UK/IRE + AUS + HK + JPN + FR + DXB",
        "domain":      "Thoroughbred racing betting",
    },
    "harness_racing": {
        "description": "Harness Racing Betting Expert — Standardbred worldwide, Hambletonian, V75, PMU",
        "domain":      "Harness racing betting",
    },
    "mens_boxing": {
        "description": "Men's Professional Boxing Betting Expert — all four sanctioning bodies, all 17 weight classes",
        "domain":      "Boxing betting",
    },
    "pga": {
        "description": "PGA Tour Betting Expert — PGA Tour + DP World Tour + LIV + all majors + Ryder Cup",
        "domain":      "Men's professional golf betting",
    },
    "lpga": {
        "description": "LPGA Tour Betting Expert — LPGA + JLPGA + KLPGA + women's majors + Solheim Cup",
        "domain":      "Women's professional golf betting",
    },
}


def run_agent(agent_key: str, task: str, context: dict,
              save: bool = False) -> str:
    """
    Invoke a single SME via run_sme_consult().
    caller="sme_flow" — must be in AUTHORISED_CALLERS.
    """
    if agent_key not in AGENT_REGISTRY:
        _print_registry()
        sys.exit(f"[sme_agent_flow] ERROR: Unknown agent key '{agent_key}'.\n"
                 f"  Use --list-agents to see valid keys.")

    entry = AGENT_REGISTRY[agent_key]
    logger.info(f"SME agent direct: {agent_key} — {entry['domain']}")

    # Import SME orchestrator
    try:
        from agents.sme.sme_orchestrator import run_sme_consult
    except ImportError as e:
        sys.exit(
            f"[sme_agent_flow] ERROR: Cannot import SME orchestrator.\n"
            f"  Add 'sme_flow' to AUTHORISED_CALLERS in "
            f"agents/sme/sme_orchestrator.py.\n"
            f"  Original error: {e}"
        )

    # Build context dict for SME
    ctx_data = context.get("data", {})
    if not ctx_data:
        ctx_data = {
            "project": context.get("project"),
            "raw": context.get("raw", ""),
        }

    try:
        result = run_sme_consult(
            context=ctx_data,
            sme_key=agent_key,
            question=task,
            caller=CALLER,
        )
        output_str = str(result)
    except PermissionError as e:
        sys.exit(
            f"[sme_agent_flow] PermissionError: {e}\n"
            f"  Add 'sme_flow' to AUTHORISED_CALLERS in "
            f"agents/sme/sme_orchestrator.py."
        )

    print("\n" + "=" * 60)
    print(f"SME AGENT DIRECT — {agent_key.upper()}")
    print("=" * 60)
    print(output_str)
    print("=" * 60 + "\n")

    if save:
        path = save_agent_direct_output(
            content=output_str,
            project=context.get("project"),
            agent_key=f"sme_{agent_key}",
        )
        if path:
            logger.info(f"Saved to {path}")
        else:
            logger.warning("--save specified but no --project set. Output not saved.")

    return output_str


def _print_registry():
    print("\nAvailable SME agents:")
    for key, entry in AGENT_REGISTRY.items():
        print(f"  {key:<35} {entry['domain']}")
    print()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sme_agent_flow.py",
        description=(
            "SME Group — single domain specialist direct.\n\n"
            "All calls use caller='sme_flow'. Ensure 'sme_flow' is in\n"
            "AUTHORISED_CALLERS in agents/sme/sme_orchestrator.py.\n\n"
            "Every SME output opens with DOMAIN ASSESSMENT: HIGH/MEDIUM/LOW\n"
            "and ends with CROSS-TEAM FLAGS and OPEN QUESTIONS."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--agent", required=True,
                        help="SME registry key.")
    parser.add_argument("--task", required=True,
                        help="Domain question or task description.")
    parser.add_argument("--project", default=None,
                        help="Project name — loads output/<project>/context.json.")
    parser.add_argument("--context-file", dest="context_file", default=None,
                        help="Path to context file.")
    parser.add_argument("--context", default=None,
                        help="Inline context string.")
    parser.add_argument("--save", action="store_true", default=False,
                        help="Save output to disk (requires --project).")
    parser.add_argument("--list-agents", action="store_true", default=False,
                        help="List available SME agents and exit.")
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
