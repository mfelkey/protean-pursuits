import sys
sys.path.insert(0, "/home/mfelkey/dev-team")

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from agents.orchestrator.orchestrator import log_event, save_context

load_dotenv("config/.env")

def build_ux_designer() -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/gpt-oss:120b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    return Agent(
        role="UX/UI Designer",
        goal=(
            "Translate business requirements and user needs into clear, intuitive, "
            "and accessible interface designs that developers can implement without "
            "ambiguity and that users will actually adopt."
        ),
        backstory=(
            "You are a Senior UX/UI Designer with 12 years of experience designing "
            "enterprise web applications for government and healthcare clients. You "
            "have deep expertise in user-centered design, information architecture, "
            "and accessibility standards including WCAG 2.1 AA and Section 508. "
            "You know that hard-to-use software doesn't get used — adoption failure "
            "is a project failure regardless of technical quality. "
            "You have designed dashboards, data visualization tools, and workflow "
            "applications for VA, DoD, and HHS clients. You understand the specific "
            "constraints of government UI: accessibility requirements are non-negotiable, "
            "users are often non-technical, screens must work on older government hardware, "
            "and the VA design system (USWDS/VA Design System) must be followed. "
            "You think in user journeys, mental models, and cognitive load — not just "
            "pixels. You produce three deliverables: a User Experience Document (UXD) "
            "covering personas, user journeys, and interaction patterns; annotated "
            "wireframes described in enough detail that a UI developer can build from them "
            "without guessing; and a UI Style Guide that enforces consistency. "
            "You work closely with the Security Reviewer to ensure that access controls "
            "and data visibility rules are reflected in the UI design, not bolted on after. "
            "You hand off to UI Developers with zero ambiguity — they execute, you design. "
            "You are also responsible for all UI content: labels, button text, tooltips, "
            "error messages, empty states, confirmation dialogs, help text, and any copy "
            "that appears in the interface. You know that 'Submit' and 'An error occurred' "
            "are not acceptable — every string a user sees is a design decision. You produce "
            "a UI Content Guide alongside your wireframes so developers never write interface "
            "copy themselves."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_ux_design(context: dict, prd_path: str, bad_path: str, srr_path: str) -> dict:
    """
    Reads PRD, BAD, and SRR and produces a User Experience Document (UXD).
    Returns updated context.
    """

    with open(prd_path) as f:
        prd_content = f.read()[:2000]

    with open(bad_path) as f:
        bad_content = f.read()[:1500]

    with open(srr_path) as f:
        srr_content = f.read()[:1500]

    ux = build_ux_designer()

    ux_task = Task(
        description=f"""
You are designing the user experience for the following project:

--- PRD (excerpt) ---
{prd_content}

--- BAD (excerpt) ---
{bad_content}

--- Security Review Report (excerpt) ---
{srr_content}

Produce a complete User Experience Document (UXD) with ALL of the following sections:

1. USER PERSONAS
   - 3-4 personas based on the stakeholder analysis
   - Each persona: name, role, goals, frustrations, tech comfort level,
     typical workflow, what success looks like for them
   - Note which persona is the primary design target

2. USER JOURNEY MAPS
   - Journey map for each primary persona
   - Stages: Trigger → Discovery → First Use → Regular Use → Advanced Use
   - For each stage: user action, thought, emotion, pain point, opportunity

3. INFORMATION ARCHITECTURE
   - Site/app structure (navigation hierarchy)
   - Page inventory with purpose of each page/view
   - Data hierarchy (what information is most important, least important)
   - Filter and search strategy

4. WIREFRAMES (detailed textual descriptions)
   - Main Dashboard view
   - Filtered/drill-down view
   - Trip detail view
   - For each wireframe: layout description, components present,
     interactions, data displayed, accessibility notes
   - Annotate every interactive element with its behavior

5. INTERACTION PATTERNS
   - Filter behavior (how filters work, persist, reset)
   - Drill-down behavior (click paths, breadcrumbs, back navigation)
   - Export behavior (what can be exported, format, PHI handling)
   - Error states (no data, loading, permission denied)
   - Empty states

6. ACCESSIBILITY DESIGN REQUIREMENTS
   - Color contrast requirements (WCAG 2.1 AA minimums)
   - Keyboard navigation map
   - Screen reader annotations for key components
   - Focus management requirements
   - Section 508 checklist for this specific application

7. UI STYLE GUIDE
   - Color palette (primary, secondary, semantic colors)
   - Typography scale
   - Component library references (VA Design System / USWDS components to use)
   - Data visualization standards (chart types, color encoding, labels)
   - Spacing and grid system

8. SECURITY-INFORMED DESIGN DECISIONS
   - How RBAC is reflected in the UI (what each role sees/cannot see)
   - PHI visibility rules in the interface
   - Session timeout behavior
   - Export restrictions visible to users
   - Audit-visible actions (what actions users know are being logged)

9. UI CONTENT GUIDE
   - All labels for every data field displayed in the UI
   - Button and action text (be specific: not "Submit" but "Run Classification")
   - Tooltip text for every non-obvious element
   - Error messages (specific, actionable, non-technical)
   - Empty state messages (no data, no results, first-time use)
   - Confirmation dialog text
   - Help text and instructional copy
   - Loading state messages
   - Success/failure notification text

10. HANDOFF NOTES FOR UI DEVELOPERS
   - Component build priority order
   - Known implementation risks
   - Decisions that require developer input
   - What NOT to change without UX review

Output the complete UXD as well-formatted markdown.
""",
        expected_output="A complete User Experience Document in markdown format.",
        agent=ux
    )

    crew = Crew(
        agents=[ux],
        tasks=[ux_task],
        process=Process.sequential,
        verbose=True
    )

    print(f"\n🎨 UX Designer creating user experience document...\n")
    result = crew.kickoff()

    os.makedirs("dev/design", exist_ok=True)
    uxd_path = f"dev/design/{context['project_id']}_UXD.md"
    with open(uxd_path, "w") as f:
        f.write(str(result))

    print(f"\n💾 User Experience Document saved: {uxd_path}")

    context["artifacts"].append({
        "name": "User Experience Document",
        "type": "UXD",
        "path": uxd_path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "UX/UI Designer"
    })
    context["status"] = "UX_DESIGN_COMPLETE"
    log_event(context, "UX_DESIGN_COMPLETE", uxd_path)
    save_context(context)

    return context, uxd_path


if __name__ == "__main__":
    import glob

    logs = sorted(glob.glob("logs/PROJ-*.json"), key=os.path.getmtime, reverse=True)
    if not logs:
        print("No project context found.")
        exit(1)

    with open(logs[0]) as f:
        context = json.load(f)

    prd_path = bad_path = srr_path = None
    for artifact in context.get("artifacts", []):
        if artifact.get("type") == "PRD":
            prd_path = artifact["path"]
        if artifact.get("type") == "BAD":
            bad_path = artifact["path"]
        if artifact.get("type") == "SRR":
            srr_path = artifact["path"]

    if not all([prd_path, bad_path, srr_path]):
        print("Missing PRD, BAD, or SRR.")
        exit(1)

    print(f"📂 Loaded context: {logs[0]}")
    context, uxd_path = run_ux_design(context, prd_path, bad_path, srr_path)

    print(f"\n✅ UX design complete.")
    print(f"📄 UXD: {uxd_path}")
    print(f"\nFirst 500 chars:")
    with open(uxd_path) as f:
        print(f.read(500))
