"""
core/input_guard.py

Protean Pursuits — Agent Input Guard

Provides two functions used by every Finance agent (and eventually all PP agents):

  check_required_inputs(project_id, prd_text, cli_context)
      Hard stop if critical inputs are missing. On TTY, prompts for project_id
      if that's the only missing item. Prints a structured MISSING INPUTS block
      and exits with code 1 on failure.

  build_assumption_instructions()
      Returns a task-description block that instructs the agent to tag every
      unverified figure with a standard label, and consolidate all tags in
      OPEN QUESTIONS.

Usage in any agent __main__:

    from core.input_guard import check_required_inputs
    project_id = check_required_inputs(project_id, prd_text, args.cli_context)

Usage in any agent run_*() task description:

    from core.input_guard import build_assumption_instructions
    task = Task(
        description=f\"\"\"...existing task...\n\n{build_assumption_instructions()}\"\"\",
        ...
    )

Hard-stop conditions:
  - project_id resolves to "PROJ-UNKNOWN" and stdin is not a TTY
  - prd_text is empty AND cli_context is empty

Ask conditions (TTY only):
  - project_id is "PROJ-UNKNOWN" — prompt once; if blank, hard stop

Flag-and-continue (injected into task description, never stops execution):
  - Competitor prices not in brief or PRD  → [ASSUMPTION — unverified]
  - User volumes / conversion rates without stated basis
                                           → [ASSUMPTION — document before launch]
  - Any numeric figure derived without a cited source
                                           → [MODELED — basis: first principles]
"""

import sys

# ── ANSI helpers (stripped when not a TTY) ────────────────────────────────────

def _tty() -> bool:
    return sys.stdin.isatty()


def _fmt(text: str, code: str) -> str:
    if sys.stdout.isatty():
        return f"\033[{code}m{text}\033[0m"
    return text


def _red(t: str)    -> str: return _fmt(t, "31")
def _yellow(t: str) -> str: return _fmt(t, "33")
def _bold(t: str)   -> str: return _fmt(t, "1")


# ── Hard-stop printer ─────────────────────────────────────────────────────────

def _print_missing_inputs(missing: list[str]) -> None:
    """Print a structured MISSING INPUTS block to stderr and stdout."""
    border = "═" * 66
    lines = [
        "",
        _red(f"╔{border}╗"),
        _red("║") + _bold("  MISSING INPUTS — AGENT CANNOT PROCEED" + " " * 26) + _red("║"),
        _red(f"╚{border}╝"),
        "",
        "The following required inputs are missing:",
        "",
    ]
    for item in missing:
        lines.append(f"  {_red('✗')} {item}")
    lines += [
        "",
        "Agent produced no artifact. Resolve the above and re-run.",
        _red("Exit code: 1"),
        "",
    ]
    output = "\n".join(lines)
    print(output, file=sys.stderr)
    print(output)


# ── Public API ────────────────────────────────────────────────────────────────

def check_required_inputs(
    project_id:  str,
    prd_text:    str,
    cli_context: str,
) -> str:
    """Validate critical inputs before an agent run.

    Args:
        project_id:  The resolved project ID string.
        prd_text:    PRD file contents (may be empty string).
        cli_context: CLI --context brief (may be empty string or None).

    Returns:
        project_id — possibly updated from stdin prompt if on a TTY.

    Raises:
        SystemExit(1) on hard-stop conditions.
    """
    cli_context = cli_context or ""
    prd_text    = prd_text    or ""
    project_id  = project_id  or "PROJ-UNKNOWN"

    missing = []

    # ── Check 1: project_id ───────────────────────────────────────────────────
    if project_id == "PROJ-UNKNOWN":
        if _tty():
            # Interactive — ask once
            print(
                _yellow(
                    "\n⚠️  No project ID resolved from --project-id or logs/PROJ-*.json."
                )
            )
            try:
                entered = input("   Enter project ID (e.g. PROJ-PARALLAXEDGE) or press Enter to abort: ").strip()
            except (EOFError, KeyboardInterrupt):
                entered = ""

            if entered:
                project_id = entered
                print(f"   Using project ID: {project_id}\n")
            else:
                missing.append(
                    "PROJECT ID    — pass --project-id PROJ-XXXXX\n"
                    "                    or ensure logs/PROJ-*.json exists"
                )
        else:
            # Non-interactive — hard stop immediately
            missing.append(
                "PROJECT ID    — pass --project-id PROJ-XXXXX\n"
                "                    or ensure logs/PROJ-*.json exists"
            )

    # ── Check 2: content brief ────────────────────────────────────────────────
    if not prd_text.strip() and not cli_context.strip():
        missing.append(
            "CONTENT BRIEF — pass --prd /path/to/prd.md\n"
            "                    and/or --context \"your brief here\""
        )

    # ── Hard stop if anything missing ─────────────────────────────────────────
    if missing:
        _print_missing_inputs(missing)
        sys.exit(1)

    return project_id


def build_assumption_instructions() -> str:
    """Return the assumption-tagging block to append to every agent task description.

    Paste this at the end of the task description f-string:

        description=f\"\"\"
        ...existing sections...

        {build_assumption_instructions()}
        \"\"\"
    """
    return """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ASSUMPTION TAGGING REQUIREMENTS — NON-NEGOTIABLE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
You MUST tag every unverified or derived figure inline using the
standard labels below. Never omit a tag to make output look cleaner.

TAG DEFINITIONS:

  [ASSUMPTION — unverified]
      Use when: a competitor price, market size, industry benchmark,
      or third-party figure is not explicitly stated in the brief or PRD.
      Example: "OddsJam charges ~$200/mo [ASSUMPTION — unverified]"

  [ASSUMPTION — document before launch]
      Use when: a user volume, conversion rate, churn rate, or growth
      rate has no stated basis in the brief, PRD, or upstream artifacts.
      Example: "5,000 MAU by month 6 [ASSUMPTION — document before launch]"

  [MODELED — basis: first principles]
      Use when: a numeric figure was derived by your own reasoning
      without a cited source, upstream artifact, or brief statement.
      Example: "Infra cost $400/mo at launch [MODELED — basis: first principles]"

CONSOLIDATION REQUIREMENT:
  In your OPEN QUESTIONS section, list every tagged figure grouped by
  tag type, with a one-line remediation step for each:
    - Who should verify it
    - What source or method would resolve it
    - Whether it is launch-blocking or can be refined post-launch

DO NOT produce a section with no tags if you used any estimates.
DO NOT present estimates as facts.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
