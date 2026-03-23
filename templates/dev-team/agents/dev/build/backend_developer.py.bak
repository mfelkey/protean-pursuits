import sys
sys.path.insert(0, "/home/mfelkey/dev-team")

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from agents.orchestrator.orchestrator import log_event, save_context

load_dotenv("config/.env")

def build_backend_developer() -> Agent:
    llm = LLM(
        model=os.getenv("TIER2_MODEL", "ollama/qwen3-coder:30b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    return Agent(
        role="Backend Developer",
        goal=(
            "Implement the complete server-side codebase — APIs, business logic, "
            "data access layer, and authentication — according to the Technical "
            "Implementation Plan, producing production-ready code with full test coverage."
        ),
        backstory=(
            "You are a Senior Backend Engineer with 12 years of experience building "
            "high-performance, secure server-side systems for government and healthcare "
            "clients. You are deeply fluent in Python and SQL, with strong working "
            "knowledge of C and Rust for performance-critical components. You have "
            "extensive experience with Node.js/Express for API development and know "
            "when to reach for each tool. "
            "You specialize in: REST API design and implementation; relational database "
            "design and query optimization in PostgreSQL; authentication and authorization "
            "systems including JWT, OAuth2, and RBAC; data pipeline integration; and "
            "secure coding practices that satisfy HIPAA and FISMA requirements. "
            "You write clean, well-documented, testable code. You never ship untested "
            "code. You understand that backend code is the foundation everything else "
            "depends on — if you get it wrong, everyone suffers. "
            "You work directly from the Technical Implementation Plan produced by the "
            "Senior Developer. You do not make architectural decisions — you execute "
            "the plan with precision and flag any implementation blockers immediately. "
            "You produce two deliverables: working, documented code and a Backend "
            "Implementation Report (BIR) that documents every endpoint, database table, "
            "and integration point you implemented, so the Frontend Developer and "
            "DevOps Engineer know exactly what exists and how to use it."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_backend_implementation(context: dict, tip_path: str, tad_path: str) -> dict:
    """
    Reads TIP and TAD and produces a Backend Implementation Report (BIR) with code.
    Returns updated context.
    """

    with open(tip_path) as f:
        tip_content = f.read()[:3000]

    with open(tad_path) as f:
        tad_content = f.read()[:2000]

    bd = build_backend_developer()

    bir_task = Task(
        description=f"""
You are the Backend Developer for the following project. Using the Technical
Implementation Plan and Technical Architecture Document below, produce a complete
Backend Implementation Report (BIR) with working code samples for all key components.

--- Technical Implementation Plan (excerpt) ---
{tip_content}

--- Technical Architecture Document (excerpt) ---
{tad_content}

Produce a complete Backend Implementation Report (BIR) with ALL of the following sections:

1. DATABASE SCHEMA
   - Complete SQL DDL for all tables (CREATE TABLE statements)
   - All indexes, constraints, and foreign keys
   - Prisma schema file content
   - Seed data structure for development/testing

2. API ENDPOINTS (IMPLEMENTED)
   - Complete implementation for every endpoint defined in the TIP
   - Each endpoint: route, method, controller code, validation schema,
     middleware applied, response format, error cases
   - Include actual working code, not pseudocode

3. AUTHENTICATION & AUTHORIZATION
   - Complete JWT middleware implementation
   - RBAC implementation (roles, permissions, enforcement)
   - Auth0 integration code
   - Session management

4. DATA ACCESS LAYER
   - Prisma client setup and configuration
   - Repository pattern implementations for each entity
   - Transaction examples for multi-step operations
   - Connection pooling configuration

5. BUSINESS LOGIC SERVICES
   - Trip classification service
   - Export service (CSV and PDF generation)
   - Data validation service
   - Audit logging service

6. ERROR HANDLING
   - Global error handler implementation
   - Custom error classes
   - Error response formatting
   - Unhandled rejection/exception handlers

7. LOGGING IMPLEMENTATION
   - Winston logger configuration
   - Log levels and when to use each
   - Request/response logging middleware
   - Audit log implementation (PHI-safe)

8. UNIT TESTS
   - Complete unit tests for all services
   - Test setup and teardown
   - Mocking strategy for database and external services
   - Coverage report target per module

9. INTEGRATION TESTS
   - API endpoint integration tests
   - Database integration tests
   - Auth flow integration tests

10. ENVIRONMENT CONFIGURATION
    - Complete .env.example file
    - Configuration validation on startup
    - Secrets management integration with Azure Key Vault

Output the complete BIR as well-formatted markdown with working code blocks.
All code must be production-ready, properly typed, and commented.
""",
        expected_output="A complete Backend Implementation Report with working code in markdown format.",
        agent=bd
    )

    crew = Crew(
        agents=[bd],
        tasks=[bir_task],
        process=Process.sequential,
        verbose=True
    )

    print(f"\n⚙️  Backend Developer implementing server-side codebase...\n")
    result = crew.kickoff()

    os.makedirs("dev/build", exist_ok=True)
    bir_path = f"dev/build/{context['project_id']}_BIR.md"
    with open(bir_path, "w") as f:
        f.write(str(result))

    print(f"\n💾 Backend Implementation Report saved: {bir_path}")

    context["artifacts"].append({
        "name": "Backend Implementation Report",
        "type": "BIR",
        "path": bir_path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "Backend Developer"
    })
    context["status"] = "BACKEND_COMPLETE"
    log_event(context, "BACKEND_COMPLETE", bir_path)
    save_context(context)

    return context, bir_path


if __name__ == "__main__":
    import glob

    logs = sorted(glob.glob("logs/PROJ-*.json"), key=os.path.getmtime, reverse=True)
    if not logs:
        print("No project context found.")
        exit(1)

    with open(logs[0]) as f:
        context = json.load(f)

    tip_path = tad_path = None
    for artifact in context.get("artifacts", []):
        if artifact.get("type") == "TIP":
            tip_path = artifact["path"]
        if artifact.get("type") == "TAD":
            tad_path = artifact["path"]

    if not all([tip_path, tad_path]):
        print("Missing TIP or TAD.")
        exit(1)

    print(f"📂 Loaded context: {logs[0]}")
    context, bir_path = run_backend_implementation(context, tip_path, tad_path)

    print(f"\n✅ Backend implementation complete.")
    print(f"📄 BIR: {bir_path}")
    print(f"\nFirst 500 chars:")
    with open(bir_path) as f:
        print(f.read(500))
