"""
PATCH: Add run_qa_orchestrator() to
  templates/qa-team/agents/orchestrator/orchestrator.py

Append this block to the bottom of that file (after build_qa_orchestrator).
"""

import os
from crewai import Crew, Task


def run_qa_orchestrator(context: dict, brief: str = "") -> str:
    """
    Entry point called by qa_intake_flow.py.

    Builds the QA Team Orchestrator agent, issues a Task derived from
    the project context and brief, runs a single-agent Crew, saves output
    to output/<project>/qa/, and returns the result string.

    FAIL and CRITICAL verdicts trigger immediate human notification via
    escalate_qa_failure() before the report is released.

    Args:
        context: Project context dict (from load_context or stub).
        brief:   Plain-English QA brief (may also live in context["brief"]).

    Returns:
        String output from the QA Team Orchestrator agent.
    """
    # ── Resolve brief ──────────────────────────────────────────────────────────
    resolved_brief = brief or context.get("brief", "")
    if not resolved_brief:
        raise ValueError(
            "run_qa_orchestrator: no brief provided. "
            "Pass via 'brief' argument or context['brief']."
        )

    project = context.get("project", "ad-hoc")

    # ── Build agent ────────────────────────────────────────────────────────────
    agent = build_qa_orchestrator()

    # ── Build task ─────────────────────────────────────────────────────────────
    task_description = f"""
You are the QA Team Orchestrator for the Protean Pursuits system.

PROJECT: {project}

BRIEF:
{resolved_brief}

CONTEXT:
{context.get("raw", "")}

{QA_INSTRUCTION}

Based on the brief above, select the appropriate run mode (functional,
performance, security, accessibility, data_quality, legal_review,
marketing_review, test_cases, or full), engage the relevant specialist
agents, and produce the complete QA deliverable.

MANDATORY OUTPUT STRUCTURE:
1. QA VERDICT block (PASS / CONDITIONAL / FAIL / CRITICAL) — at the very top
2. BLOCKING ISSUES list (each with ID, severity, category, description,
   expected vs actual, remediation, and blocking: YES/NO)
3. NON-BLOCKING ISSUES list (same format)
4. SIGN-OFF STATUS: APPROVED TO SHIP / CONDITIONAL / DO NOT SHIP
5. RETEST REQUIREMENTS (if verdict is FAIL or CRITICAL)

FAIL and CRITICAL verdicts must be escalated to the human immediately.
No vague findings — every issue must be precise and reproducible.
"""

    task = Task(
        description=task_description,
        expected_output=(
            "A complete QA report (functional test results, performance benchmarks, "
            "security report, accessibility audit, data quality scorecard, legal "
            "completeness review, marketing compliance review, test case library, "
            "or full QA package) appropriate to the requested mode. Must open with "
            "the mandatory QA VERDICT block and include a SIGN-OFF STATUS decision."
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
        output_dir = f"output/{project}/qa"
        os.makedirs(output_dir, exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        out_path = f"{output_dir}/orchestrator_{ts}.md"
        with open(out_path, "w") as f:
            f.write(output_str)
        print(f"💾 QA Orchestrator output saved: {out_path}")

    return output_str
