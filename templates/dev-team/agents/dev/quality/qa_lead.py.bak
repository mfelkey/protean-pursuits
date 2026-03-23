import sys
sys.path.insert(0, "/home/mfelkey/dev-team")

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from agents.orchestrator.orchestrator import log_event, save_context

load_dotenv("config/.env")

def build_qa_lead() -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/gpt-oss:120b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    return Agent(
        role="QA Lead",
        goal=(
            "Own the complete quality assurance strategy for the project — "
            "define what 'done' means from a quality perspective, design the "
            "test plan, coordinate all testing activities, and be the final "
            "gate before any release reaches production."
        ),
        backstory=(
            "You are a Senior QA Lead with 15 years of experience in software "
            "quality assurance for government and healthcare systems. You have "
            "led QA programs for HIPAA-regulated applications, FISMA-compliant "
            "federal systems, and Section 508-accessible web applications. "
            "You think about quality at every level — unit, integration, "
            "end-to-end, performance, security, accessibility, and user "
            "acceptance. You know that testing is not a phase at the end of "
            "development — it is a discipline woven through the entire SDLC. "
            "You have deep experience with both manual and automated testing. "
            "You know when to automate and when human judgment is irreplaceable. "
            "You are fluent in test planning, test case design, defect management, "
            "risk-based testing, and release criteria definition. "
            "You review every artifact the development team produces — PRD, "
            "TAD, BIR, FIR, DBAR — and you find the gaps, ambiguities, and "
            "untestable requirements before they become production defects. "
            "You are the voice of the end user in the development process. "
            "You work from all available project artifacts and produce a Master "
            "Test Plan (MTP) that the test automation engineer, performance "
            "tester, and security tester execute against. Nothing ships without "
            "your sign-off."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_master_test_plan(context: dict, prd_path: str, tip_path: str,
                          bir_path: str, fir_path: str, uxd_path: str) -> dict:

    with open(prd_path) as f:
        prd_content = f.read()[:1500]

    with open(tip_path) as f:
        tip_content = f.read()[:1000]

    with open(bir_path) as f:
        bir_content = f.read()[:1000]

    with open(fir_path) as f:
        fir_content = f.read()[:1000]

    with open(uxd_path) as f:
        uxd_content = f.read()[:1000]

    qa = build_qa_lead()

    mtp_task = Task(
        description=f"""
You are the QA Lead for the following project. Review the documents below
and produce a complete Master Test Plan (MTP).

--- PRD (excerpt) ---
{prd_content}

--- Technical Implementation Plan (excerpt) ---
{tip_content}

--- Backend Implementation Report (excerpt) ---
{bir_content}

--- Frontend Implementation Report (excerpt) ---
{fir_content}

--- User Experience Document (excerpt) ---
{uxd_content}

Produce a complete Master Test Plan (MTP) with ALL of the following sections:

1. TEST STRATEGY OVERVIEW
   - Testing philosophy and approach
   - Test levels (unit, integration, E2E, performance, security, accessibility)
   - Testing tools and frameworks for each level
   - Entry and exit criteria for each test level
   - Risk-based testing approach

2. TEST ENVIRONMENT REQUIREMENTS
   - Environment specifications (dev, staging, production-mirror)
   - Test data requirements (PHI-safe synthetic data)
   - Access requirements per tester role
   - Environment setup and teardown procedures
   - Dependency mocking strategy

3. TEST CASES — FUNCTIONAL
   - Complete test cases for every major feature:
     * User authentication and authorization (all roles)
     * Filter functionality (all filter combinations)
     * Trip classification (happy path, edge cases, error cases)
     * Data table (sort, search, pagination)
     * Trip detail modal
     * Export (CSV, PDF — including PHI masking verification)
     * Dashboard KPI cards
     * Session management and timeout
   - Format: Test ID | Description | Preconditions | Steps | Expected Result | Priority

4. TEST CASES — NEGATIVE & EDGE CASES
   - Invalid inputs for all forms and filters
   - Boundary conditions (date ranges, row limits, confidence scores)
   - Concurrent user scenarios
   - Network failure handling
   - Empty state handling
   - Large dataset handling (10,000+ rows)

5. TEST CASES — ACCESSIBILITY (Section 508 / WCAG 2.1 AA)
   - Keyboard navigation test cases for every interactive element
   - Screen reader test cases (NVDA, JAWS, VoiceOver)
   - Color contrast verification
   - Focus management after async operations
   - ARIA label verification
   - Form error announcement verification

6. API TEST CASES
   - Test cases for every endpoint in the BIR
   - Authentication tests (valid token, expired token, missing token, wrong role)
   - Input validation tests (missing fields, invalid types, injection attempts)
   - Response format verification
   - Error response verification

7. DATABASE TEST CASES
   - Schema integrity tests
   - Constraint violation tests
   - RLS policy verification
   - PHI masking verification
   - Migration rollback tests

8. DEFECT MANAGEMENT PROCESS
   - Defect severity definitions (Critical, High, Medium, Low)
   - Defect lifecycle
   - Defect report template
   - SLA for defect resolution by severity
   - Regression testing requirements after fixes

9. RELEASE CRITERIA
   - Definition of Ready for UAT
   - Definition of Ready for Production
   - Mandatory passing criteria
   - Acceptable risk criteria
   - Sign-off matrix

10. TEST METRICS & REPORTING
    - Metrics to track
    - Daily test status report format
    - Weekly quality dashboard
    - Go/No-Go meeting agenda template

Output the complete MTP as well-formatted markdown.
Every test case must have actual steps — no vague descriptions.
""",
        expected_output="A complete Master Test Plan in markdown format.",
        agent=qa
    )

    crew = Crew(
        agents=[qa],
        tasks=[mtp_task],
        process=Process.sequential,
        verbose=True
    )

    print(f"\n🧪 QA Lead creating Master Test Plan...\n")
    result = crew.kickoff()

    os.makedirs("dev/quality", exist_ok=True)
    mtp_path = f"dev/quality/{context['project_id']}_MTP.md"
    with open(mtp_path, "w") as f:
        f.write(str(result))

    print(f"\n💾 Master Test Plan saved: {mtp_path}")

    context["artifacts"].append({
        "name": "Master Test Plan",
        "type": "MTP",
        "path": mtp_path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "QA Lead"
    })
    context["status"] = "MTP_COMPLETE"
    log_event(context, "MTP_COMPLETE", mtp_path)
    save_context(context)

    return context, mtp_path


if __name__ == "__main__":
    import glob

    logs = sorted(glob.glob("logs/PROJ-*.json"), key=os.path.getmtime, reverse=True)
    if not logs:
        print("No project context found.")
        exit(1)

    with open(logs[0]) as f:
        context = json.load(f)

    prd_path = tip_path = bir_path = fir_path = uxd_path = None
    for artifact in context.get("artifacts", []):
        if artifact.get("type") == "PRD":
            prd_path = artifact["path"]
        if artifact.get("type") == "TIP":
            tip_path = artifact["path"]
        if artifact.get("type") == "BIR":
            bir_path = artifact["path"]
        if artifact.get("type") == "FIR":
            fir_path = artifact["path"]
        if artifact.get("type") == "UXD":
            uxd_path = artifact["path"]

    if not all([prd_path, tip_path, bir_path, fir_path, uxd_path]):
        print("Missing one or more required artifacts.")
        exit(1)

    print(f"📂 Loaded context: {logs[0]}")
    context, mtp_path = run_master_test_plan(
        context, prd_path, tip_path, bir_path, fir_path, uxd_path
    )

    print(f"\n✅ Master Test Plan complete.")
    print(f"📄 MTP: {mtp_path}")
    print(f"\nFirst 500 chars:")
    with open(mtp_path) as f:
        print(f.read(500))
