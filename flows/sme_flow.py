"""
flows/sme_flow.py

Protean Pursuits — SME Group Flow

Project-agnostic domain specialists callable from any PP project.
All calls use caller="sme_flow" which must be in AUTHORISED_CALLERS
in agents/sme/sme_orchestrator.py.

Run modes:
    consult   Single SME direct — one domain expert answers the question
    crew      Multi-SME synthesized — named experts collaborate, HITL gate fires
    auto      Auto-detect SMEs from question — pp_orchestrator selects experts

Usage:
    python flows/sme_flow.py --mode consult \\
        --sme pga \\
        --question "What are the key betting markets for the Masters?" \\
        --project parallaxedge

    python flows/sme_flow.py --mode crew \\
        --sme pga lpga \\
        --question "Compare majors betting liquidity between PGA and LPGA tours" \\
        --project parallaxedge

    python flows/sme_flow.py --mode auto \\
        --question "How do Asian handicap markets work for soccer and rugby?" \\
        --project parallaxedge

Via pp_flow.py:
    python flows/pp_flow.py --team sme --mode consult \\
        --agent pga \\
        --task "What are the key betting markets for the Masters?" \\
        --project parallaxedge

    python flows/pp_flow.py --team sme --mode auto \\
        --task "How do Asian handicap markets work for soccer and rugby?" \\
        --project parallaxedge
"""

import argparse
import logging
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from core.context_loader import load_context, save_output  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

TEAM = "sme"
CALLER = "sme_flow"

# ── SME registry (mirrors sme_orchestrator.py) ────────────────────────────────

SME_REGISTRY = {
    "sports_betting":           "Cross-sport industry authority — all regulated markets worldwide",
    "world_football":           "All global leagues, confederations, Asian handicap",
    "nba_ncaa_basketball":      "NBA + March Madness",
    "nfl_ncaa_football":        "NFL + CFP, college football",
    "mlb":                      "MLB + NPB + KBO + CPBL",
    "nhl_ncaa_hockey":          "NHL + NCAA + KHL + Euro leagues",
    "mma":                      "UFC + Bellator + ONE + Rizin",
    "tennis":                   "ATP + WTA + Challengers + ITF",
    "world_rugby":              "Union + League — Six Nations, NRL, State of Origin",
    "cricket":                  "Test + ODI + T20 + IPL — all formats, all nations",
    "wnba_ncaa_womens_basketball": "WNBA + NCAA women's",
    "thoroughbred_horse_racing":"US + UK/IRE + AUS + HK + JPN + FR + DXB",
    "harness_racing":           "Standardbred worldwide — Hambletonian, V75, PMU",
    "mens_boxing":              "All four sanctioning bodies, all 17 weight classes",
    "pga":                      "PGA Tour + DP World Tour + LIV + all majors + Ryder Cup",
    "lpga":                     "LPGA + JLPGA + KLPGA + women's majors + Solheim Cup",
}


# ── Notifications ─────────────────────────────────────────────────────────────

def _notify(title: str, message: str):
    try:
        from core.notifications import send_pushover
        send_pushover(title=title, message=message)
    except Exception as e:
        logger.warning(f"Pushover notification failed: {e}")


# ── SME import helper ─────────────────────────────────────────────────────────

def _import_sme():
    """Import SME orchestrator functions. Raises ImportError with clear message."""
    try:
        from agents.sme.sme_orchestrator import run_sme_consult, run_sme_crew
        return run_sme_consult, run_sme_crew
    except ImportError as e:
        sys.exit(
            f"[sme_flow] ERROR: Cannot import SME orchestrator.\n"
            f"  Ensure agents/sme/sme_orchestrator.py is on sys.path.\n"
            f"  Add 'sme_flow' to AUTHORISED_CALLERS in sme_orchestrator.py.\n"
            f"  Original error: {e}"
        )


def _save(content: str, context: dict, mode: str):
    if not context.get("project"):
        return
    from datetime import datetime
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = save_output(
        content=content,
        project=context["project"],
        team=TEAM,
        filename=f"{mode}_{ts}.md",
    )
    if path:
        logger.info(f"Saved to {path}")


# ── Mode runners ──────────────────────────────────────────────────────────────

def run_consult(question: str, sme_keys: list, context: dict,
                save: bool = False) -> str:
    """
    Single SME consult.
    If multiple sme_keys are given, runs each independently (not synthesized).
    For synthesized multi-SME output use run_crew().
    """
    if not sme_keys:
        sys.exit("[sme_flow] consult mode requires --sme <key>. "
                 "Use --mode auto for auto-detection.")

    run_sme_consult, _ = _import_sme()
    ctx_data = context.get("data", {})
    if not ctx_data:
        ctx_data = {"project": context.get("project"), "raw": context.get("raw", "")}

    results = []
    for key in sme_keys:
        if key not in SME_REGISTRY:
            logger.warning(f"Unknown SME key '{key}' — skipping. "
                           f"Valid keys: {list(SME_REGISTRY.keys())}")
            continue

        logger.info(f"SME consult: {key} — {SME_REGISTRY[key]}")
        _notify(f"PP SME — {key}", f"Consulting {key}: {question[:80]}")

        try:
            result = run_sme_consult(
                context=ctx_data,
                sme_key=key,
                question=question,
                caller=CALLER,
            )
            output_str = str(result)
        except PermissionError as e:
            sys.exit(
                f"[sme_flow] PermissionError: {e}\n"
                f"  Add 'sme_flow' to AUTHORISED_CALLERS in "
                f"agents/sme/sme_orchestrator.py."
            )

        print("\n" + "=" * 60)
        print(f"SME CONSULT — {key.upper()}")
        print("=" * 60)
        print(output_str)
        print("=" * 60 + "\n")

        results.append(output_str)
        _notify(f"PP SME — {key} complete",
                f"Project: {context.get('project') or 'ad-hoc'}")

    combined = "\n\n---\n\n".join(results)
    if save:
        _save(combined, context, f"consult_{'_'.join(sme_keys)}")
    return combined


def run_crew(question: str, sme_keys: list, context: dict,
             save: bool = False) -> str:
    """
    Multi-SME synthesized crew.
    SME Orchestrator routes to named experts, synthesizes output,
    and fires a HITL review gate on the Domain Intelligence Brief.
    """
    _, run_sme_crew = _import_sme()
    ctx_data = context.get("data", {})
    if not ctx_data:
        ctx_data = {"project": context.get("project"), "raw": context.get("raw", "")}

    logger.info(f"SME crew: {sme_keys or 'auto-detect'}")
    _notify(
        f"PP SME — crew ({len(sme_keys) if sme_keys else 'auto'})",
        f"Question: {question[:80]}"
    )

    try:
        result = run_sme_crew(
            context=ctx_data,
            sme_keys=sme_keys,
            question=question,
            caller=CALLER,
        )
        output_str = str(result)
    except PermissionError as e:
        sys.exit(
            f"[sme_flow] PermissionError: {e}\n"
            f"  Add 'sme_flow' to AUTHORISED_CALLERS in "
            f"agents/sme/sme_orchestrator.py."
        )

    print("\n" + "=" * 60)
    print(f"SME CREW OUTPUT — {', '.join(sme_keys) if sme_keys else 'AUTO'}")
    print("=" * 60)
    print(output_str)
    print("=" * 60 + "\n")

    if save:
        label = "_".join(sme_keys) if sme_keys else "auto"
        _save(output_str, context, f"crew_{label}")

    _notify(f"PP SME — crew complete",
            f"Project: {context.get('project') or 'ad-hoc'}")
    return output_str


def run_auto(question: str, context: dict, save: bool = False) -> str:
    """
    Auto-detect SMEs from question keywords.
    Delegates to run_crew() with empty sme_keys list.
    """
    logger.info("SME auto-detect mode — SME Orchestrator will select experts.")
    return run_crew(question=question, sme_keys=[], context=context, save=save)


# ── CLI ───────────────────────────────────────────────────────────────────────

MODES = ["consult", "crew", "auto"]


def _print_registry():
    print("\nAvailable SME registry keys:")
    for key, desc in SME_REGISTRY.items():
        print(f"  {key:<35} {desc}")
    print()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sme_flow.py",
        description=(
            "Protean Pursuits — SME Group Flow\n\n"
            "Modes:\n"
            "  consult  Single SME — one domain expert\n"
            "  crew     Multi-SME synthesized — HITL gate fires on output\n"
            "  auto     Auto-detect experts from question keywords\n\n"
            "All calls use caller='sme_flow'. Ensure 'sme_flow' is in\n"
            "AUTHORISED_CALLERS in agents/sme/sme_orchestrator.py."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--mode", required=True, choices=MODES,
                        help="Run mode.")
    parser.add_argument("--question", "--task", dest="question", required=False,
                        default="",
                        help="The domain question or task description.")
    parser.add_argument("--sme", nargs="+", default=[],
                        metavar="KEY",
                        help="One or more SME registry keys (consult/crew modes). "
                             "Leave blank for auto-detect.")
    parser.add_argument("--project", default=None,
                        help="Project name — loads output/<project>/context.json.")
    parser.add_argument("--context-file", dest="context_file", default=None,
                        help="Path to context file.")
    parser.add_argument("--context", default=None,
                        help="Inline context string.")
    parser.add_argument("--save", action="store_true", default=False,
                        help="Save output to disk (requires --project).")
    parser.add_argument("--list-smes", action="store_true", default=False,
                        help="List available SME registry keys and exit.")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.list_smes:
        _print_registry()
        sys.exit(0)

    if not args.question:
        parser.error("--question / --task is required.")

    if args.save and not args.project:
        parser.error("--save requires --project.")

    if args.mode == "consult" and not args.sme:
        parser.error("--mode consult requires at least one --sme <key>. "
                     "Use --list-smes to see available keys.")

    context = load_context(
        project=args.project,
        context_file=args.context_file,
        context_str=args.context,
    )

    if args.mode == "consult":
        run_consult(question=args.question, sme_keys=args.sme,
                    context=context, save=args.save)
    elif args.mode == "crew":
        run_crew(question=args.question, sme_keys=args.sme,
                 context=context, save=args.save)
    elif args.mode == "auto":
        run_auto(question=args.question, context=context, save=args.save)


if __name__ == "__main__":
    main()
