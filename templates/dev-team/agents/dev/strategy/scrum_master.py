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

def build_scrum_master() -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/gpt-oss:120b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    return Agent(
        role="Scrum Master",
        goal=(
            "Transform requirements into a prioritized, executable sprint plan "
            "that the development team can deliver predictably and transparently."
        ),
        backstory=(
            "You are a certified Scrum Master with 10 years of experience running "
            "agile delivery in federal IT and healthcare environments. You have deep "
            "knowledge of VA program management requirements including earned value "
            "management, ATO processes, and Section 508 compliance timelines. "
            "You think in epics, stories, and sprints — you never let vague "
            "requirements reach a developer's hands. You run lean ceremonies: "
            "tight standups, focused retrospectives, and sprint reviews that "
            "actually drive decisions. You are the team's shield against scope "
            "creep and the delivery team's advocate with leadership. "
            "You produce three things: a prioritized product backlog, a realistic "
            "sprint plan, and a definition of done that everyone agrees on before "
            "the first line of code is written."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_sprint_planning(context: dict, prd_path: str, bad_path: str) -> dict:
    """
    Reads PRD and BAD and produces a Sprint Plan document.
    Returns updated context.
    """
    # ── Smart extraction: load relevant sections for scrum_master ──
    ctx = load_agent_context(
        context=context,
        consumer="scrum_master",
        artifact_types=["PRD", "BAD"],
        max_chars_per_artifact=6000
    )
    prompt_context = format_context_for_prompt(ctx)


    sm = build_scrum_master()

    sprint_task = Task(
        description=f"""
You have received the following project documents:

--- PRD (excerpt) ---

--- Business Analysis Document (excerpt) ---
{bad_content}

Produce a complete Sprint Planning Document with ALL of the following sections:

1. DEFINITION OF DONE
   - Project-level DoD: what must be true before the project is considered complete
   - Sprint-level DoD: what must be true before any story is considered done
   - Code-level DoD: what every code change must satisfy

2. PRODUCT BACKLOG
   - Full prioritized list of epics and user stories
   - Each epic contains 3-5 stories
   - Each story has: Story ID, title, description, story points (1/2/3/5/8),
     priority (P1/P2/P3), dependencies, acceptance criteria
   - Stories ordered by priority within each epic

3. SPRINT PLAN
   - 2-week sprints
   - Each sprint has: Sprint number, goal, stories included, total points,
     team capacity assumption, risks
   - Sprints ordered chronologically
   - Include a sprint 0 for environment setup

4. VELOCITY & CAPACITY ASSUMPTIONS
   - Assumed team composition
   - Assumed velocity per sprint
   - Buffer for VA compliance activities (ATO, Section 508, PIA)
   - Risk buffer

5. DEPENDENCIES & CRITICAL PATH
   - Which stories block others
   - External dependencies (VA infrastructure, data access, approvals)
   - Critical path to go-live

6. RISKS & MITIGATIONS
   - Top 5 delivery risks
   - Likelihood, impact, and mitigation for each

7. CEREMONIES SCHEDULE
   - Sprint cadence
   - Standup, planning, review, retrospective schedule
   - Stakeholder demo schedule

Output the complete Sprint Planning Document as well-formatted markdown.
""",
        expected_output="A complete Sprint Planning Document in markdown format.",
        agent=sm
    )

    crew = Crew(
        agents=[sm],
        tasks=[sprint_task],
        process=Process.sequential,
        verbose=True
    )

    print(f"\n📅 Scrum Master generating sprint plan...\n")
    result = crew.kickoff()

    # Save sprint plan
    os.makedirs("dev/planning", exist_ok=True)
    sprint_path = f"dev/planning/{context['project_id']}_SPRINT_PLAN.md"
    with open(sprint_path, "w") as f:
        f.write(str(result))

    print(f"\n💾 Sprint plan saved: {sprint_path}")

    context["artifacts"].append({
        "name": "Sprint Planning Document",
        "type": "SPRINT_PLAN",
        "path": sprint_path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "Scrum Master"
    })
    on_artifact_saved(context, "SPRINT_PLAN", sprint_path)
    context["status"] = "SPRINT_PLAN_COMPLETE"
    log_event(context, "SPRINT_PLAN_COMPLETE", sprint_path)
    save_context(context)

    return context, sprint_path


if __name__ == "__main__":
    import glob

    logs = sorted(glob.glob("logs/PROJ-*.json"), key=os.path.getmtime, reverse=True)
    if not logs:
        print("No project context found. Run classify.py first.")
        exit(1)

    with open(logs[0]) as f:
        context = json.load(f)

    prd_path = None
    bad_path = None
    for artifact in context.get("artifacts", []):
        if artifact.get("type") == "PRD":
            prd_path = artifact["path"]
        if artifact.get("type") == "BAD":
            bad_path = artifact["path"]

    if not prd_path or not bad_path:
        print("Missing PRD or BAD. Run product_manager.py and business_analyst.py first.")
        exit(1)

    print(f"📂 Loaded context: {logs[0]}")
    context, sprint_path = run_sprint_planning(context, prd_path, bad_path)

    print(f"\n✅ Sprint planning complete.")
    print(f"📄 Sprint Plan: {sprint_path}")
    print(f"\nFirst 500 chars:")
    with open(sprint_path) as f:
        print(f.read(500))
