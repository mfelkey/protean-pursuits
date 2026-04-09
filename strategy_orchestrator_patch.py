"""
PATCH: Add run_strategy_orchestrator() to
  templates/strategy-team/agents/orchestrator/orchestrator.py

Append this block to the bottom of that file (after build_strategy_orchestrator).
"""

import os
from crewai import Crew, Task


def run_strategy_orchestrator(context: dict, brief: str = "") -> str:
    """
    Entry point called by strategy_intake_flow.py.

    Builds the Strategy Team Orchestrator agent, issues a Task derived from
    the project context and brief, runs a single-agent Crew, saves output
    to output/<project>/strategy/, and returns the result string.

    All outputs require human review before forwarding to the Protean
    Pursuits Orchestrator for implementation. Every recommendation must
    carry a confidence level (HIGH / MEDIUM / LOW).

    Args:
        context: Project context dict (from load_context or stub).
        brief:   Plain-English strategy brief (may also live in context["brief"]).

    Returns:
        String output from the Strategy Team Orchestrator agent.
    """
    # ── Resolve brief ──────────────────────────────────────────────────────────
    resolved_brief = brief or context.get("brief", "")
    if not resolved_brief:
        raise ValueError(
            "run_strategy_orchestrator: no brief provided. "
            "Pass via 'brief' argument or context['brief']."
        )

    project = context.get("project", "ad-hoc")

    # ── Build agent ────────────────────────────────────────────────────────────
    agent = build_strategy_orchestrator()

    # ── Build task ─────────────────────────────────────────────────────────────
    task_description = f"""
You are the Strategy Team Orchestrator for the Protean Pursuits system.

PROJECT: {project}

BRIEF:
{resolved_brief}

CONTEXT:
{context.get("raw", "")}

{CONFIDENCE_INSTRUCTION}

Based on the brief above, select the appropriate run mode (positioning,
business_model, competitive, gtm, okr, financial, partnership, product,
risk, talent, technology, or full), engage the relevant specialist agents,
and produce the complete strategy deliverable.

SCOPE DETERMINATION:
- If the brief references a specific project, treat this as PROJECT scope
  and align with the company-level baseline strategy.
- If the brief is company-wide, treat this as COMPANY scope and update
  the baseline strategy accordingly.

MANDATORY OUTPUT STANDARDS:
- Every recommendation must carry a confidence level tag:
  [CONFIDENCE: HIGH | MEDIUM | LOW] with supporting evidence or stated assumption
- No recommendation ships without a confidence tag — omission is a defect
- End with OPEN ITEMS listing decisions requiring human approval before
  this strategy is forwarded to the Protean Pursuits Orchestrator
"""

    task = Task(
        description=task_description,
        expected_output=(
            "A complete strategy deliverable (brand positioning framework, business "
            "model canvas, competitive landscape, GTM plan, OKR framework, financial "
            "strategy, partnership framework, product strategy, risk register, org "
            "design, technology strategy, or full strategy package) appropriate to "
            "the requested mode. Every recommendation must carry a [CONFIDENCE: ...] "
            "tag. Must end with OPEN ITEMS section."
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
        output_dir = f"output/{project}/strategy"
        os.makedirs(output_dir, exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        out_path = f"{output_dir}/orchestrator_{ts}.md"
        with open(out_path, "w") as f:
            f.write(output_str)
        print(f"💾 Strategy Orchestrator output saved: {out_path}")

    return output_str
