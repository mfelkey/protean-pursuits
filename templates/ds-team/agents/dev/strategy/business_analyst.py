import sys
sys.path.insert(0, "/home/mfelkey/dev-team")

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from agents.orchestrator.orchestrator import log_event, save_context
from agents.shared.knowledge_curator.rag_inject import get_knowledge_context

load_dotenv("config/.env")

def build_business_analyst() -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/gpt-oss:120b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    return Agent(
        role="Business Analyst",
        goal=(
            "Translate business needs into detailed process flows, stakeholder "
            "maps, and data dictionaries that eliminate ambiguity before "
            "technical design begins."
        ),
        backstory=(
            "You are a senior Business Analyst with 12 years of experience in "
            "federal healthcare IT, specializing in VA and DoD systems. You have "
            "deep knowledge of the relevant business domain, processes, "
            "workflows, and the political dynamics of government stakeholder "
            "environments. You think in process flows and data lineage — you never "
            "accept vague requirements and always ask 'what does the data look like "
            "at each step?' You produce three things better than anyone: stakeholder "
            "impact assessments, current-state vs future-state process diagrams, "
            "and data dictionaries that developers can build from directly. "
            "You work from the PRD and go deeper — your job is to answer every "
            "question the PRD leaves open before engineering starts."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_business_analysis(context: dict, prd_path: str) -> dict:
    """
    Reads the PRD and produces a Business Analysis Document (BAD).
    Returns updated context.
    """

    # Load PRD - extract key sections only to stay within context limits
    with open(prd_path) as f:
        full_prd = f.read()
    # Pass first 4000 chars (exec summary through user stories) + requirements
    prd_content = full_prd[:4000]

    # ── RAG: inject current knowledge (VA/CMS policy, domain context) ──
    project_title = context.get("structured_spec", {}).get("title", "project")
    knowledge = get_knowledge_context(
        agent_role="Business Analyst",
        task_summary=f"Business analysis for {project_title}",
    )

    ba = build_business_analyst()

    ba_task = Task(
        description=f"""
You have received the following Product Requirements Document (PRD):

---
{prd_content}
---

CURRENT DOMAIN KNOWLEDGE (from knowledge base — use only if relevant to this project):
{knowledge}

Your job is to produce a Business Analysis Document (BAD) that goes deeper
than the PRD on process, stakeholders, and data.

Produce a complete Business Analysis Document with ALL of the following sections:

1. STAKEHOLDER ANALYSIS
   - Stakeholder register: Name/role, interest level (HIGH/MED/LOW),
     influence level (HIGH/MED/LOW), engagement strategy
   - For each HIGH influence stakeholder: specific concerns they are likely
     to raise and how to address them
   - Communication plan: who gets what updates, how often, in what format

2. CURRENT STATE PROCESS FLOW
   - Step-by-step description of how the core workflow is currently
     authorized, dispatched, recorded, and billed at the VA
   - Identify every point where data is created, modified, or lost
   - Identify pain points and bottlenecks in the current process
   - Note which steps involve PHI and who has access

3. FUTURE STATE PROCESS FLOW
   - How the process changes after this system is deployed
   - Which manual steps are automated
   - How classification results feed into leadership decisions
   - How the dashboard fits into the existing VA reporting workflow

4. GAP ANALYSIS (PROCESS LEVEL)
   - Side-by-side comparison of current vs future state at each step
   - Effort required to close each gap (HIGH/MED/LOW)
   - Who owns closing each gap

5. DATA DICTIONARY
   - Every field in the project dataset with:
     * Field name (technical)
     * Display name (business-friendly)
     * Data type
     * Valid values or range
     * Required (Y/N)
     * PHI (Y/N)
     * Business definition
     * Source system
     * Notes/edge cases

6. BUSINESS RULES CATALOG
   - Every classification rule stated precisely:
     * Rule ID
     * Rule name
     * Condition (IF...)
     * Action (THEN...)
     * Priority (if rules conflict)
     * Owner (who can change this rule)
     * Effective date

7. OPEN QUESTIONS LOG
   - Every assumption in the PRD that needs validation
   - Every question that must be answered before development starts
   - Owner and target resolution date for each

Output the complete Business Analysis Document as well-formatted markdown.
""",
        expected_output="A complete Business Analysis Document in markdown format.",
        agent=ba
    )

    crew = Crew(
        agents=[ba],
        tasks=[ba_task],
        process=Process.sequential,
        verbose=True
    )

    print(f"\n🔍 Business Analyst analyzing PRD...\n")
    result = crew.kickoff()

    # Save BAD
    os.makedirs("dev/requirements", exist_ok=True)
    bad_path = f"dev/requirements/{context['project_id']}_BAD.md"
    with open(bad_path, "w") as f:
        f.write(str(result))

    print(f"\n💾 Business Analysis Document saved: {bad_path}")

    # Update context
    context["artifacts"].append({
        "name": "Business Analysis Document",
        "type": "BAD",
        "path": bad_path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "Business Analyst"
    })
    context["status"] = "BUSINESS_ANALYSIS_COMPLETE"
    log_event(context, "BAD_COMPLETE", bad_path)
    save_context(context)

    return context, bad_path


if __name__ == "__main__":
    import glob

    logs = sorted(glob.glob("logs/PROJ-*.json"), key=os.path.getmtime, reverse=True)
    if not logs:
        print("No project context found. Run classify.py first.")
        exit(1)

    with open(logs[0]) as f:
        context = json.load(f)

    # Find the PRD
    prd_path = None
    for artifact in context.get("artifacts", []):
        if artifact.get("type") == "PRD":
            prd_path = artifact["path"]
            break

    if not prd_path or not os.path.exists(prd_path):
        print("No PRD found in context. Run product_manager.py first.")
        exit(1)

    print(f"📂 Loaded context: {logs[0]}")
    print(f"📄 Using PRD: {prd_path}")

    context, bad_path = run_business_analysis(context, prd_path)

    print(f"\n✅ Business analysis complete.")
    print(f"📄 BAD: {bad_path}")
    print(f"\nFirst 500 chars:")
    with open(bad_path) as f:
        print(f.read(500))
