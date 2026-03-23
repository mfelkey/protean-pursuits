import sys
sys.path.insert(0, "/home/mfelkey/dev-team")

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from agents.orchestrator.orchestrator import log_event, save_context

load_dotenv("config/.env")

def build_product_manager() -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/gpt-oss:120b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    )

    return Agent(
        role="Product Manager",
        goal=(
            "Transform project specifications into detailed, unambiguous product "
            "requirements that development teams can execute without guessing."
        ),
        backstory=(
            "You are a senior Product Manager with 15 years of experience delivering "
            "software in government and healthcare environments. You have deep expertise "
            "in VA and federal IT systems. You write requirements that are specific, "
            "measurable, and technically actionable. You never leave room for "
            "interpretation — if something is unclear, you flag it explicitly rather "
            "than assume. You structure all requirements using standard PRD format and "
            "always include user stories, acceptance criteria, and out-of-scope items. "
            "You are the last line of defense before engineering begins — your document "
            "is the contract between the business and the technical team."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_requirements_phase(context: dict) -> dict:
    """
    Takes a classified project context and produces a full PRD.
    Returns updated context with PRD artifact added.
    """

    spec = context["structured_spec"]
    pm = build_product_manager()

    prd_task = Task(
        description=f"""
You have received the following project specification from the Master Orchestrator:

{json.dumps(spec, indent=2)}

Produce a complete Product Requirements Document (PRD) for this project.

Your PRD must include ALL of the following sections:

1. EXECUTIVE SUMMARY
   - Project title, requestor, date
   - One paragraph business justification
   - Key stakeholders

2. PROBLEM STATEMENT
   - Current state (what exists today)
   - Desired state (what we're building toward)
   - Gap analysis (what's missing)

3. USER STORIES
   - At least 5 user stories in format: "As a [role], I want [feature] so that [benefit]"
   - Each story must have 3-5 acceptance criteria in Given/When/Then format

4. FUNCTIONAL REQUIREMENTS
   - Numbered list of specific features the system must have
   - Each requirement must be testable

5. NON-FUNCTIONAL REQUIREMENTS
   - Performance targets (load times, throughput)
   - Security requirements
   - Accessibility standards
   - Browser/platform compatibility

6. DATA REQUIREMENTS
   - What data is needed
   - Data sources
   - Data governance considerations (especially PHI/PII for VA context)

7. OUT OF SCOPE
   - Explicit list of what this project will NOT deliver

8. DEPENDENCIES AND ASSUMPTIONS
   - What must be true for this project to succeed
   - External dependencies

9. RISKS
   - At least 3 risks with likelihood (HIGH/MED/LOW) and mitigation strategy

10. SUCCESS METRICS
    - How we measure that this project succeeded post-launch

Project context for VA/healthcare domain:
- This system may handle veteran health data — apply HIPAA and VA privacy standards
- Users include VA clinical and administrative staff
- System must meet Section 508 accessibility requirements
- Prefer existing VA-approved technology stacks where possible

Output the complete PRD as a well-formatted markdown document.
""",
        expected_output="A complete Product Requirements Document in markdown format.",
        agent=pm
    )

    crew = Crew(
        agents=[pm],
        tasks=[prd_task],
        process=Process.sequential,
        verbose=True
    )

    print(f"\n📋 Product Manager generating PRD for: {spec.get('title')}\n")
    result = crew.kickoff()

    # Save PRD to file
    os.makedirs("dev/requirements", exist_ok=True)
    prd_path = f"dev/requirements/{context['project_id']}_PRD.md"
    with open(prd_path, "w") as f:
        f.write(str(result))

    print(f"\n💾 PRD saved: {prd_path}")

    # Update context
    context["artifacts"].append({
        "name": "Product Requirements Document",
        "type": "PRD",
        "path": prd_path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "Product Manager"
    })
    context["status"] = "PRD_COMPLETE"
    log_event(context, "PRD_COMPLETE", prd_path)
    save_context(context)

    return context, prd_path


if __name__ == "__main__":
    import glob

    logs = sorted(glob.glob("logs/PROJ-*.json"), key=os.path.getmtime, reverse=True)
    if not logs:
        print("No project context found. Run classify.py first.")
        exit(1)

    with open(logs[0]) as f:
        context = json.load(f)

    print(f"📂 Loaded context: {logs[0]}")
    context, prd_path = run_requirements_phase(context)

    print(f"\n✅ Requirements phase complete.")
    print(f"📄 PRD: {prd_path}")
    print(f"\nFirst 500 chars of PRD:")
    with open(prd_path) as f:
        print(f.read(500))
