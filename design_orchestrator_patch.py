"""
PATCH: Add run_design_orchestrator() to
  templates/design-team/agents/orchestrator/orchestrator.py

Append this block to the bottom of that file (after build_design_orchestrator).
"""

import os
from crewai import Crew, Task


def run_design_orchestrator(context: dict, brief: str = "") -> str:
    """
    Entry point called by design_intake_flow.py.

    Builds the Design Team Orchestrator agent, issues a Task derived from
    the project context and brief, runs a single-agent Crew, saves output
    to output/<project>/design/, and returns the result string.

    All outputs require human review (DESIGN_REVIEW gate) before handoff
    to implementation teams.

    Args:
        context: Project context dict (from load_context or stub).
        brief:   Plain-English design brief (may also live in context["brief"]).

    Returns:
        String output from the Design Team Orchestrator agent.
    """
    # ── Resolve brief ──────────────────────────────────────────────────────────
    resolved_brief = brief or context.get("brief", "")
    if not resolved_brief:
        raise ValueError(
            "run_design_orchestrator: no brief provided. "
            "Pass via 'brief' argument or context['brief']."
        )

    project = context.get("project", "ad-hoc")

    # ── Build agent ────────────────────────────────────────────────────────────
    agent = build_design_orchestrator()

    # ── Build task ─────────────────────────────────────────────────────────────
    task_description = f"""
You are the Design Team Orchestrator for the Protean Pursuits system.

PROJECT: {project}

BRIEF:
{resolved_brief}

CONTEXT:
{context.get("raw", "")}

{DESIGN_INSTRUCTION}

Based on the brief above, select the appropriate run mode (research, wireframe,
visual, motion, accessibility, or full), engage the relevant specialist agents,
and produce the complete design deliverable.

MANDATORY OUTPUT STANDARDS (enforced on all outputs):
- Tool-agnostic specs with precise values (hex colors, px/rem, named tokens)
- Accessibility-first: flag any WCAG 2.1 AA concerns
- Full state annotations: default, hover, focus, disabled, error
- Responsive behaviour defined for all breakpoints
- Handoff-ready: a developer can implement without follow-up questions

End every output with OPEN QUESTIONS listing design decisions that require
human input before implementation begins.
"""

    task = Task(
        description=task_description,
        expected_output=(
            "A complete design deliverable (research report, wireframes, UI component "
            "specs, brand system, motion spec, accessibility audit, or full design "
            "package) appropriate to the requested mode. Must be tool-agnostic, "
            "fully annotated, and end with an OPEN QUESTIONS section."
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
        output_dir = f"output/{project}/design"
        os.makedirs(output_dir, exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        out_path = f"{output_dir}/orchestrator_{ts}.md"
        with open(out_path, "w") as f:
            f.write(output_str)
        print(f"💾 Design Orchestrator output saved: {out_path}")

    return output_str
