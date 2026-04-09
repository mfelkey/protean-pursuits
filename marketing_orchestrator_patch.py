"""
PATCH: Add run_marketing_orchestrator() to
  templates/marketing-team/agents/orchestrator/orchestrator.py

Append this block to the bottom of that file (after build_marketing_orchestrator).
"""

import os
from crewai import Crew, Task


def run_marketing_orchestrator(context: dict, brief: str = "") -> str:
    """
    Entry point called by marketing_intake_flow.py.

    Builds the Marketing Orchestrator agent, issues a Task derived from
    the project context and brief, runs a single-agent Crew, saves output
    to output/<project>/marketing/, and returns the result string.

    Args:
        context: Project context dict (from load_context or stub).
        brief:   Plain-English marketing brief (may also live in context["brief"]).

    Returns:
        String output from the Marketing Orchestrator agent.
    """
    # ── Resolve brief ──────────────────────────────────────────────────────────
    resolved_brief = brief or context.get("brief", "")
    if not resolved_brief:
        raise ValueError(
            "run_marketing_orchestrator: no brief provided. "
            "Pass via 'brief' argument or context['brief']."
        )

    project = context.get("project", "ad-hoc")

    # ── Build agent ────────────────────────────────────────────────────────────
    agent = build_marketing_orchestrator()

    # ── Build task ─────────────────────────────────────────────────────────────
    task_description = f"""
You are the Marketing Orchestrator for the Protean Pursuits system.

PROJECT: {project}

BRIEF:
{resolved_brief}

CONTEXT:
{context.get("raw", "")}

Based on the brief above, select the appropriate run mode (brief, copy, email,
social, video, analytics, or campaign), sequence the relevant marketing agents,
and produce the complete requested marketing deliverable.

Enforce brand voice throughout: data-forward, quietly confident, never hypey,
never tipster-adjacent. Every deliverable must go through the appropriate HITL
gate (POST / EMAIL / VIDEO) before it is considered final.

Output a complete, structured marketing deliverable appropriate for the
requested mode. End with a numbered list of any open items requiring human
input before execution.
"""

    task = Task(
        description=task_description,
        expected_output=(
            "A complete marketing deliverable (campaign brief, copy package, "
            "email sequence, social drafts, video script, analytics report, or "
            "full campaign package) appropriate to the requested run mode. "
            "Must end with OPEN ITEMS section listing any decisions still needed."
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
        output_dir = f"output/{project}/marketing"
        os.makedirs(output_dir, exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        out_path = f"{output_dir}/orchestrator_{ts}.md"
        with open(out_path, "w") as f:
            f.write(output_str)
        print(f"💾 Marketing Orchestrator output saved: {out_path}")

    return output_str
