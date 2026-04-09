"""
PATCH for templates/video-team/agents/orchestrator/orchestrator.py

TWO CHANGES REQUIRED:

1. BUG FIX — NameError at import time:
   The current file has:
       import sys
       sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))
   ...before `from pathlib import Path` — Path is not yet defined.

   Replace those two lines at the top of the file with the block marked
   REPLACE_TOP below.

2. ADD run_video_orchestrator() — append the block marked ADD_BOTTOM
   to the end of the file (after build_video_orchestrator).

────────────────────────────────────────────────────────────────────────────────
REPLACE_TOP  (swap the first 3 lines of the file with these)
────────────────────────────────────────────────────────────────────────────────

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))

────────────────────────────────────────────────────────────────────────────────
ADD_BOTTOM  (append after build_video_orchestrator)
────────────────────────────────────────────────────────────────────────────────
"""

# ── ADD_BOTTOM ────────────────────────────────────────────────────────────────

import os
from crewai import Crew, Task


def run_video_orchestrator(context: dict, brief: str = "") -> str:
    """
    Entry point called by video_intake_flow.py.

    Builds the Video Team Orchestrator agent, issues a Task derived from
    the project context and brief, runs a single-agent Crew, saves output
    to output/<project>/video/, and returns the result string.

    Three HITL gates fire inside the pipeline:
      VIDEO_TOOL_SELECTION → SCRIPT_REVIEW → VIDEO_FINAL
    Nothing publishes without all three gates passing.

    Args:
        context: Project context dict (from load_context or stub).
        brief:   Plain-English video brief (may also live in context["brief"]).

    Returns:
        String output from the Video Team Orchestrator agent.
    """
    # ── Resolve brief ──────────────────────────────────────────────────────────
    resolved_brief = brief or context.get("brief", "")
    if not resolved_brief:
        raise ValueError(
            "run_video_orchestrator: no brief provided. "
            "Pass via 'brief' argument or context['brief']."
        )

    project = context.get("project", "ad-hoc")

    # ── Build agent ────────────────────────────────────────────────────────────
    agent = build_video_orchestrator()

    # ── Build task ─────────────────────────────────────────────────────────────
    task_description = f"""
You are the Video Team Orchestrator for the Protean Pursuits system.

PROJECT: {project}

BRIEF:
{resolved_brief}

CONTEXT:
{context.get("raw", "")}

{VIDEO_STANDARDS}

Based on the brief above, select the appropriate run mode (BRIEF_ONLY,
SHORT_FORM, LONG_FORM, AVATAR, DEMO, EXPLAINER, VOICEOVER, or FULL),
engage the relevant specialist agents, and produce the complete video
production package.

MANDATORY GATE SEQUENCE — nothing proceeds without each approval:
  1. VIDEO_TOOL_SELECTION gate — tool evaluation report, human must approve
     before any creative work or API calls begin
  2. SCRIPT_REVIEW gate — script approved before production work begins
  3. VIDEO_FINAL gate — compliance review approved before any publish action

MANDATORY OUTPUT STRUCTURE:
1. Tool Selection Brief (platform, tools, rationale)
2. Script / Narrative
3. Visual Direction Brief
4. Audio & Music Brief
5. Avatar/Spokesperson notes (if applicable)
6. Production API call spec (if applicable)
7. Compliance & Brand Review
8. Video Package (VP) cover document indexing all artifacts
9. OPEN ITEMS — decisions or assets still required from the human

Do not invoke any external API without explicit human approval at
VIDEO_TOOL_SELECTION and SCRIPT_REVIEW gates.
"""

    task = Task(
        description=task_description,
        expected_output=(
            "A complete video production package appropriate to the selected run mode "
            "(BRIEF_ONLY through FULL). Must include tool selection brief, script, "
            "visual direction, audio brief, compliance review, and a VP cover document "
            "indexing all artifacts. Must end with OPEN ITEMS section."
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
        output_dir = f"output/{project}/video"
        os.makedirs(output_dir, exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        out_path = f"{output_dir}/orchestrator_{ts}.md"
        with open(out_path, "w") as f:
            f.write(output_str)
        print(f"💾 Video Orchestrator output saved: {out_path}")

    return output_str
