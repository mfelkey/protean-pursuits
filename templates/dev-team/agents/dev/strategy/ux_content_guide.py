import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from agents.orchestrator.orchestrator import log_event, save_context
from agents.orchestrator.context_manager import load_agent_context, format_context_for_prompt, on_artifact_saved


load_dotenv("config/.env")

def run_content_guide(context: dict, uxd_path: str) -> dict:
    """
    Reads UXD and produces a standalone UI Content Guide.
    """
    # ── Smart extraction: load relevant sections for ux_content ──
    ctx = load_agent_context(
        context=context,
        consumer="ux_content",
        artifact_types=["PRD", "UXD"],
        max_chars_per_artifact=6000
    )
    prompt_context = format_context_for_prompt(ctx)


    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/gpt-oss:120b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    ux = Agent(
        role="UX/UI Designer",
        goal="Produce a complete UI Content Guide for the the project dashboard.",
        backstory=(
            "You are a Senior UX/UI Designer responsible for all interface content — "
            "every label, button, tooltip, error message, and notification that a user "
            "sees. You know that developers should never write UI copy. You write with "
            "clarity, brevity, and plain language appropriate for non-technical VA users. "
            "You follow VA plain language guidelines and Section 508 requirements. "
            "Every string you write is intentional — no placeholder text, no 'Click here', "
            "no 'Error occurred'. Your content guide is the single source of truth for "
            "all UI text in the application."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

    content_task = Task(
        description=f"""
Using the following User Experience Document as context, produce a complete and exhaustive
UI Content Guide for the the project dashboard.

--- UXD (excerpt) ---

Produce a UI Content Guide with ALL of the following sections:

1. FIELD LABELS
   - Every data field displayed in the UI
   - Format: Field Name | Label Text | Notes

2. BUTTON & ACTION TEXT
   - Every button, link, and action in the application
   - Format: Component/Location | Button Text | Tooltip on Hover | Notes

3. NAVIGATION & PAGE TITLES
   - All page titles, tab labels, breadcrumb text, section headers

4. TOOLTIPS
   - Every tooltip in the application
   - Format: Element | Trigger | Tooltip Text (max 2 sentences, plain language)

5. ERROR MESSAGES
   - Every error state
   - Format: Error Condition | Headline | Body Text | Recovery Action shown to user
   - Be specific: no generic "An error occurred"

6. EMPTY STATE MESSAGES
   - No data, no results, first-time use, loading
   - Format: State | Headline | Body Text | Call to Action

7. CONFIRMATION DIALOGS
   - Every action requiring confirmation
   - Format: Action | Dialog Title | Body Text | Confirm Button | Cancel Button

8. SUCCESS & NOTIFICATION MESSAGES
   - Toast notifications, banners, inline confirmations
   - Format: Trigger | Message Text | Duration shown

9. HELP & INSTRUCTIONAL TEXT
   - Onboarding text, help panel content, field-level instructions
   - Format: Location | Text

10. LOADING STATES
    - Every loading state in the application
    - Format: Component | Loading Message | Accessible aria-label

11. SECURITY & COMPLIANCE NOTICES
    - PHI masking notices, audit log notices, session timeout warnings,
      export restrictions visible to users
    - Format: Location | Notice Text

12. CONTENT STYLE RULES
    - Capitalization rules
    - Number and date formatting
    - Abbreviations allowed/not allowed
    - Voice and tone guidelines (3-4 principles)
    - Plain language rules specific to this application

Output the complete UI Content Guide as well-formatted markdown.
Every entry must have actual content — no placeholders, no TBDs.
""",
        expected_output="A complete UI Content Guide in markdown format.",
        agent=ux
    )

    crew = Crew(
        agents=[ux],
        tasks=[content_task],
        process=Process.sequential,
        verbose=True
    )

    print(f"\n✍️  UX Designer generating UI Content Guide...\n")
    result = crew.kickoff()

    content_path = f"dev/design/{context['project_id']}_UI_CONTENT.md"
    with open(content_path, "w") as f:
        f.write(str(result))

    print(f"\n💾 UI Content Guide saved: {content_path}")

    context["artifacts"].append({
        "name": "UI Content Guide",
        "type": "UI_CONTENT",
        "path": content_path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "UX/UI Designer"
    })
    on_artifact_saved(context, "CONTENT_GUIDE", content_path)
    log_event(context, "UI_CONTENT_COMPLETE", content_path)
    save_context(context)

    return context, content_path


if __name__ == "__main__":
    import glob

    logs = sorted(glob.glob("logs/PROJ-*.json"), key=os.path.getmtime, reverse=True)
    if not logs:
        print("No project context found.")
        exit(1)

    with open(logs[0]) as f:
        context = json.load(f)

    uxd_path = None
    for artifact in context.get("artifacts", []):
        if artifact.get("type") == "UXD":
            uxd_path = artifact["path"]

    if not uxd_path:
        print("Missing UXD. Run ux_designer.py first.")
        exit(1)

    print(f"📂 Loaded context: {logs[0]}")
    context, content_path = run_content_guide(context, uxd_path)

    print(f"\n✅ UI Content Guide complete.")
    print(f"📄 Content Guide: {content_path}")
    print(f"\nFirst 500 chars:")
    with open(content_path) as f:
        print(f.read(500))
