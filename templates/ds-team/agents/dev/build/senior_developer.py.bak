import sys
sys.path.insert(0, "/home/mfelkey/dev-team")

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from agents.orchestrator.orchestrator import log_event, save_context

load_dotenv("config/.env")

def build_senior_developer() -> Agent:
    llm = LLM(
        model=os.getenv("TIER2_MODEL", "ollama/qwen3-coder:30b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    return Agent(
        role="Senior Developer",
        goal=(
            "Translate architecture and design documents into a concrete, "
            "implementable technical implementation plan that backend, frontend, "
            "and DevOps developers can execute without ambiguity."
        ),
        backstory=(
            "You are a Senior Full-Stack Software Engineer with 15 years of experience "
            "building enterprise web applications, data pipelines, systems software, and "
            "cloud-native systems. You have led development teams in federal healthcare "
            "environments including VA, CMS, and HHS projects. "
            "You are a true full-stack engineer who has worked at every layer of the stack. "
            "You started as a frontend developer — you know React and Next.js deeply, "
            "including SSR, SSG, app router patterns, state management, and component "
            "architecture. You moved through the stack and became equally fluent in "
            "backend systems, systems programming, and data engineering. "
            "Your core languages are: C and C++ for systems-level and performance-critical "
            "work; Python for data pipelines, scripting, and AI/ML integration; Rust for "
            "high-performance, memory-safe systems code; React and Next.js for frontend "
            "and full-stack web applications; and SQL for relational data modeling, "
            "query optimization, and database design. "
            "You understand when to use each language — you don't use Python where Rust "
            "belongs, and you don't write C where Python is sufficient. "
            "You have deep experience with REST API design, microservices, event-driven "
            "architecture, and CI/CD pipelines. You take architecture documents and turn "
            "them into reality — you define the project structure, coding standards, "
            "technology stack confirmations, module boundaries, and implementation "
            "sequencing that the rest of the build team follows. "
            "You are opinionated about quality: you enforce code review standards, test "
            "coverage requirements, and security practices. You never write vague "
            "implementation notes — every decision you document is specific enough that "
            "a mid-level developer can execute it without asking clarifying questions. "
            "You are the primary code reviewer for the team — nothing merges without "
            "your sign-off. You understand that the Backend Developer, Frontend Developer, "
            "and DevOps Engineer are your executors, and your Technical Implementation "
            "Plan (TIP) is their bible. "
            "You are aware of AI/ML integration patterns and know how to structure "
            "codebases that consume model inference APIs, manage embeddings, and "
            "integrate with orchestration frameworks like CrewAI and LangChain."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_technical_implementation_plan(context: dict, prd_path: str, tad_path: str, uxd_path: str) -> dict:
    """
    Reads PRD, TAD, and UXD and produces a Technical Implementation Plan (TIP).
    Returns updated context.
    """

    with open(prd_path) as f:
        prd_content = f.read()[:1500]

    with open(tad_path) as f:
        tad_content = f.read()[:2000]

    with open(uxd_path) as f:
        uxd_content = f.read()[:1500]

    sd = build_senior_developer()

    tip_task = Task(
        description=f"""
You are the Senior Developer for the following project. Review the documents below
and produce a complete Technical Implementation Plan (TIP).

--- PRD (excerpt) ---
{prd_content}

--- Technical Architecture Document (excerpt) ---
{tad_content}

--- User Experience Document (excerpt) ---
{uxd_content}

Produce a complete Technical Implementation Plan (TIP) with ALL of the following sections:

1. PROJECT STRUCTURE
   - Complete directory/file tree for the codebase
   - Purpose of each directory
   - Naming conventions

2. TECHNOLOGY STACK CONFIRMATION
   - Final confirmed stack for each layer (frontend, backend, data, infra)
   - Version numbers for all dependencies
   - Justification for any deviations from the TAD

3. CODING STANDARDS
   - Language-specific style guides to follow
   - Linting and formatting tools and configuration
   - Import organization rules
   - Documentation requirements (docstrings, comments)
   - Naming conventions (variables, functions, classes, files)

4. MODULE BOUNDARIES & INTERFACES
   - How the codebase is divided into modules
   - What each module owns and does not own
   - How modules communicate (function calls, events, APIs)
   - Dependency rules (which modules can import which)

5. DATA ACCESS LAYER
   - ORM or query strategy
   - Connection management
   - Transaction handling
   - Error handling for data operations
   - Migration strategy

6. API IMPLEMENTATION GUIDE
   - Route structure and naming
   - Request validation approach
   - Response envelope format
   - Error response format
   - Authentication middleware implementation
   - Logging requirements per endpoint

7. TESTING STRATEGY
   - Unit test requirements (coverage minimum, what to test)
   - Integration test requirements
   - Test file naming and organization
   - Mocking strategy for external dependencies
   - How to run the full test suite

8. CODE REVIEW STANDARDS
   - What the Senior Developer checks in every PR
   - Automatic blockers (what will always be rejected)
   - PR size guidelines
   - Branch naming conventions
   - Commit message format

9. IMPLEMENTATION SEQUENCE
   - Order in which modules should be built
   - Dependencies between implementation tasks
   - What must be done before the Backend Developer starts
   - What must be done before the Frontend Developer starts
   - What must be done before DevOps starts

10. SECURITY IMPLEMENTATION REQUIREMENTS
    - How authentication is implemented in code
    - How authorization is enforced at the code level
    - Input validation requirements
    - Secrets management in code
    - Logging requirements (what to log, what never to log)

Output the complete TIP as well-formatted markdown.
Every section must have specific, actionable content — no placeholders.
""",
        expected_output="A complete Technical Implementation Plan in markdown format.",
        agent=sd
    )

    crew = Crew(
        agents=[sd],
        tasks=[tip_task],
        process=Process.sequential,
        verbose=True
    )

    print(f"\n👨‍💻 Senior Developer creating Technical Implementation Plan...\n")
    result = crew.kickoff()

    os.makedirs("dev/build", exist_ok=True)
    tip_path = f"dev/build/{context['project_id']}_TIP.md"
    with open(tip_path, "w") as f:
        f.write(str(result))

    print(f"\n💾 Technical Implementation Plan saved: {tip_path}")

    context["artifacts"].append({
        "name": "Technical Implementation Plan",
        "type": "TIP",
        "path": tip_path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "Senior Developer"
    })
    context["status"] = "TIP_COMPLETE"
    log_event(context, "TIP_COMPLETE", tip_path)
    save_context(context)

    return context, tip_path


if __name__ == "__main__":
    import glob

    logs = sorted(glob.glob("logs/PROJ-*.json"), key=os.path.getmtime, reverse=True)
    if not logs:
        print("No project context found.")
        exit(1)

    with open(logs[0]) as f:
        context = json.load(f)

    prd_path = tad_path = uxd_path = None
    for artifact in context.get("artifacts", []):
        if artifact.get("type") == "PRD":
            prd_path = artifact["path"]
        if artifact.get("type") == "TAD":
            tad_path = artifact["path"]
        if artifact.get("type") == "UXD":
            uxd_path = artifact["path"]

    if not all([prd_path, tad_path, uxd_path]):
        print("Missing PRD, TAD, or UXD.")
        exit(1)

    print(f"📂 Loaded context: {logs[0]}")
    context, tip_path = run_technical_implementation_plan(context, prd_path, tad_path, uxd_path)

    print(f"\n✅ Technical Implementation Plan complete.")
    print(f"📄 TIP: {tip_path}")
    print(f"\nFirst 500 chars:")
    with open(tip_path) as f:
        print(f.read(500))
