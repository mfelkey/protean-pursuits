"""
PATCH: Add run_legal_orchestrator() to
  templates/legal-team/agents/orchestrator/orchestrator.py

Append this block to the bottom of that file (after build_legal_orchestrator).
"""

import os
from crewai import Crew, Task


def run_legal_orchestrator(context: dict, brief: str = "") -> str:
    """
    Entry point called by legal_intake_flow.py.

    Builds the Legal Team Orchestrator agent, issues a Task derived from
    the project context and brief, runs a single-agent Crew, saves output
    to output/<project>/legal/, and returns the result string.

    Risk level and jurisdiction tags are enforced via the RISK_INSTRUCTION
    and JURISDICTION_INSTRUCTION constants already defined in this module.

    Args:
        context: Project context dict (from load_context or stub).
        brief:   Plain-English legal brief (may also live in context["brief"]).

    Returns:
        String output from the Legal Team Orchestrator agent.
    """
    # ── Resolve brief ──────────────────────────────────────────────────────────
    resolved_brief = brief or context.get("brief", "")
    if not resolved_brief:
        raise ValueError(
            "run_legal_orchestrator: no brief provided. "
            "Pass via 'brief' argument or context['brief']."
        )

    project = context.get("project", "ad-hoc")

    # ── Build agent ────────────────────────────────────────────────────────────
    agent = build_legal_orchestrator()

    # ── Build task ─────────────────────────────────────────────────────────────
    task_description = f"""
You are the Legal Team Orchestrator for the Protean Pursuits system.

PROJECT: {project}

BRIEF:
{resolved_brief}

CONTEXT:
{context.get("raw", "")}

{RISK_INSTRUCTION}

{JURISDICTION_INSTRUCTION}

Based on the brief above, select the appropriate run mode (contract, review,
ip, privacy, regulatory, employment, corporate, dispute, or full), engage the
relevant specialist agents, and produce the complete legal deliverable.

MANDATORY OUTPUT STRUCTURE:
1. Risk assessment block (RISK LEVEL / JURISDICTION / EXTERNAL COUNSEL /
   DISCLAIMER) — at the very top
2. Complete legal deliverable appropriate to the requested mode
3. OPEN QUESTIONS section listing any items requiring human or external
   counsel input before the document is used or executed

HIGH and CRITICAL risk outputs trigger immediate human notification via
escalate_risk() before this document is released.
"""

    task = Task(
        description=task_description,
        expected_output=(
            "A complete legal deliverable (contract draft, review memo, IP analysis, "
            "privacy assessment, compliance report, employment agreement, corporate "
            "recommendation, dispute memo, or full legal package) appropriate to the "
            "requested mode. Must open with the mandatory risk assessment block and "
            "end with an OPEN QUESTIONS section."
        ),
        agent=agent,
    )

    # ── Run crew ───────────────────────────────────────────────────────────────
    crew = Crew(agents=[agent], tasks=[task], verbose=True)
    result = crew.kickoff()
    output_str = str(result)

    # ── Persist output ─────────────────────────────────────────────────────────
    if project and project != "ad-hoc":
        from datetime import datetime
        output_dir = f"output/{project}/legal"
        os.makedirs(output_dir, exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        out_path = f"{output_dir}/orchestrator_{ts}.md"
        with open(out_path, "w") as f:
            f.write(output_str)
        print(f"💾 Legal Orchestrator output saved: {out_path}")

    return output_str
