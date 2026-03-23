import sys
sys.path.insert(0, "/home/mfelkey/dev-team")

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from agents.orchestrator.orchestrator import log_event, save_context

load_dotenv("config/.env")

def build_test_automation_engineer() -> Agent:
    llm = LLM(
        model=os.getenv("TIER2_MODEL", "ollama/qwen3-coder:30b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    return Agent(
        role="Test Automation Engineer",
        goal=(
            "Implement the complete automated test suite from the Master Test Plan — "
            "E2E tests, API tests, unit tests, and accessibility tests — producing "
            "working, runnable test code that is deployment-agnostic and passes "
            "in any environment through configuration alone."
        ),
        backstory=(
            "You are a Senior Test Automation Engineer with 12 years of experience "
            "building automated test suites for government and healthcare applications. "
            "You are expert-level in Playwright (E2E, multi-browser, accessibility), "
            "Jest with React Testing Library (unit and component tests), and Supertest "
            "(API integration tests). You use k6 for performance test scripting and "
            "integrate axe-core into every Playwright test for automatic accessibility "
            "checking. "
            "You have a core principle that defines everything you build: tests are "
            "deployment-agnostic. Your test code never contains hostnames, cloud "
            "provider references, or infrastructure assumptions. Every environment- "
            "specific value — base URLs, credentials, feature flags, database "
            "connection strings — is injected through environment variables. "
            "A test suite you write runs identically whether the application is "
            "deployed on Azure Kubernetes Service, AWS ECS, on-premises bare metal, "
            "or a developer's local Docker Compose stack. The only thing that changes "
            "between environments is the .env.test file. "
            "You use test tags to handle infrastructure-dependent tests: "
            "@smoke, @regression, @cloud-only, @onprem-only, @slow. Tests tagged "
            "@cloud-only are skipped automatically in on-prem environments. Tests "
            "tagged @onprem-only are skipped in cloud environments. The DEPLOY_TARGET "
            "environment variable (values: 'cloud' or 'onprem') controls which tags "
            "are active. "
            "You write tests that are readable, maintainable, and deterministic. "
            "Flaky tests are not acceptable — if a test cannot be made reliable, "
            "you document why and propose an alternative. "
            "You work directly from the Master Test Plan produced by the QA Lead. "
            "You implement every test case in the MTP and produce a Test Automation "
            "Report (TAR) that documents the test suite structure, how to run it, "
            "how to add new tests, and how to configure it for each deployment target."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_test_automation(context: dict, mtp_path: str, bir_path: str,
                         fir_path: str, tip_path: str) -> dict:

    with open(mtp_path) as f:
        mtp_content = f.read()[:2000]

    with open(bir_path) as f:
        bir_content = f.read()[:1000]

    with open(fir_path) as f:
        fir_content = f.read()[:1000]

    with open(tip_path) as f:
        tip_content = f.read()[:500]

    tae = build_test_automation_engineer()

    tar_task = Task(
        description=f"""
You are the Test Automation Engineer. Using the documents below, implement
a complete automated test suite and produce a Test Automation Report (TAR).

--- Master Test Plan (excerpt) ---
{mtp_content}

--- Backend Implementation Report (excerpt) ---
{bir_content}

--- Frontend Implementation Report (excerpt) ---
{fir_content}

--- Technical Implementation Plan (excerpt) ---
{tip_content}

Produce a complete Test Automation Report (TAR) with ALL of the following sections:

1. TEST SUITE STRUCTURE
   - Complete directory tree for the test suite
   - File naming conventions
   - How tests are organized (by feature, by layer, by tag)
   - Shared utilities and fixtures location

2. ENVIRONMENT CONFIGURATION
   - Complete .env.test.example file with ALL variables
   - Variable documentation (what each does, valid values)
   - DEPLOY_TARGET variable (cloud | onprem) and how it affects test execution
   - Per-environment override files (.env.test.cloud, .env.test.onprem)
   - How to switch between environments (single variable change, nothing else)

3. PLAYWRIGHT E2E TESTS
   - playwright.config.ts (deployment-agnostic, reads from env)
   - Complete test implementations for:
     * Authentication (all roles: Admin, Analyst, Viewer)
     * Filter functionality (date range, multi-filter, reset, URL persistence)
     * Trip detail modal (open, close, focus trap, PHI masking)
     * Export (CSV download verification, PHI masking, role restriction)
     * Session timeout
     * Keyboard navigation (Tab order, skip nav link)
   - Shared fixtures: authenticated page per role
   - Page Object Model classes for Dashboard, Login, FilterBar, Modal
   - axe-core accessibility scan integrated into every page test
   - Tests tagged with @smoke, @regression, @cloud-only, @onprem-only as appropriate

4. JEST + SUPERTEST API TESTS
   - jest.config.js
   - Complete API test implementations for:
     * GET /api/trips (filters, pagination, auth)
     * GET /api/trips/:id (found, not found, unauthorized)
     * POST /api/trips (valid, invalid, missing fields)
     * POST /api/trips/:id/classify (happy path, service error)
     * Auth endpoints (valid token, expired token, missing token, wrong role)
     * Input validation (SQL injection attempt, XSS attempt, boundary values)
   - Test setup/teardown with database seeding
   - Mock strategy for external services (classifier, Auth0)

5. JEST + REACT TESTING LIBRARY UNIT TESTS
   - Complete component tests for:
     * KPICard (renders value, tooltip shows on hover, ARIA labels)
     * FilterBar (state updates, Apply fires callback, Reset clears state)
     * DataTable (renders rows, sort on header click, pagination controls)
     * Modal (opens/closes, focus trap, Esc key closes)
     * Toast (appears, auto-dismisses, aria-live region)
     * ErrorBanner (renders message, close button works)
   - Hook tests (useTrips, useTripDetail, useExport)

6. K6 PERFORMANCE SCRIPTS
   - k6 script for dashboard load (100 concurrent users)
   - k6 script for filter query (10k rows)
   - k6 script for export (CSV, 10k rows)
   - Thresholds defined in script (not hardcoded to cloud metrics)
   - DEPLOY_TARGET-aware base URL injection

7. TEST RUNNER CONFIGURATION
   - package.json scripts:
     * test:unit
     * test:api
     * test:e2e
     * test:e2e:smoke
     * test:a11y
     * test:perf
     * test:all
     * test:cloud (runs @cloud-only tagged tests)
     * test:onprem (runs @onprem-only tagged tests)
   - Makefile targets that wrap the npm scripts
   - CI pipeline snippet showing how tests run on PR and on merge

8. TAGGING & SKIP STRATEGY
   - Complete list of all tags used and their meaning
   - How @cloud-only and @onprem-only tests are skipped
   - How DEPLOY_TARGET controls execution
   - Example of adding a new deployment-specific test correctly

9. SYNTHETIC TEST DATA
   - Script to generate PHI-safe synthetic data (faker-based)
   - Data volumes: 1k, 5k, 10k row datasets
   - Seed script that works against any PostgreSQL instance
     (no Azure-specific connection strings hardcoded)

10. REPORTING
    - HTML report configuration for Playwright
    - Jest coverage report configuration (target: 90% statement coverage)
    - How reports are published in CI
    - Failure notification strategy (deployment-agnostic)

Output the complete TAR as well-formatted markdown with working code.
All code must be deployment-agnostic — no Azure, AWS, or on-prem assumptions.
Every environment-specific value must come from environment variables.
""",
        expected_output="A complete Test Automation Report with working test code.",
        agent=tae
    )

    crew = Crew(
        agents=[tae],
        tasks=[tar_task],
        process=Process.sequential,
        verbose=True
    )

    print(f"\n⚗️  Test Automation Engineer implementing test suite...\n")
    result = crew.kickoff()

    os.makedirs("dev/quality", exist_ok=True)
    tar_path = f"dev/quality/{context['project_id']}_TAR.md"
    with open(tar_path, "w") as f:
        f.write(str(result))

    print(f"\n💾 Test Automation Report saved: {tar_path}")

    context["artifacts"].append({
        "name": "Test Automation Report",
        "type": "TAR",
        "path": tar_path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "Test Automation Engineer"
    })
    context["status"] = "TAR_COMPLETE"
    log_event(context, "TAR_COMPLETE", tar_path)
    save_context(context)

    return context, tar_path


if __name__ == "__main__":
    import glob

    logs = sorted(glob.glob("logs/PROJ-*.json"), key=os.path.getmtime, reverse=True)
    if not logs:
        print("No project context found.")
        exit(1)

    with open(logs[0]) as f:
        context = json.load(f)

    mtp_path = bir_path = fir_path = tip_path = None
    for artifact in context.get("artifacts", []):
        if artifact.get("type") == "MTP":
            mtp_path = artifact["path"]
        if artifact.get("type") == "BIR":
            bir_path = artifact["path"]
        if artifact.get("type") == "FIR":
            fir_path = artifact["path"]
        if artifact.get("type") == "TIP":
            tip_path = artifact["path"]

    if not all([mtp_path, bir_path, fir_path, tip_path]):
        print("Missing MTP, BIR, FIR, or TIP.")
        exit(1)

    print(f"📂 Loaded context: {logs[0]}")
    context, tar_path = run_test_automation(
        context, mtp_path, bir_path, fir_path, tip_path
    )

    print(f"\n✅ Test automation complete.")
    print(f"📄 TAR: {tar_path}")
    print(f"\nFirst 500 chars:")
    with open(tar_path) as f:
        print(f.read(500))
