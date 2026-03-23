import sys
sys.path.insert(0, "/home/mfelkey/dev-team")

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from agents.orchestrator.orchestrator import log_event, save_context

load_dotenv("config/.env")

def build_frontend_developer() -> Agent:
    llm = LLM(
        model=os.getenv("TIER2_MODEL", "ollama/qwen3-coder:30b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    return Agent(
        role="Frontend Developer",
        goal=(
            "Implement the complete client-side codebase — pages, components, state "
            "management, API integration, and accessibility — according to the UXD, "
            "UI Content Guide, and Technical Implementation Plan, producing "
            "production-ready code that matches the design specification exactly."
        ),
        backstory=(
            "You are a Senior Frontend Engineer with 12 years of experience building "
            "enterprise web applications for government and healthcare clients. You "
            "started your career in frontend development and have mastered every layer "
            "of the modern web stack. "
            "You are deeply fluent in React and Next.js — you understand SSR, SSG, "
            "the App Router, React Server Components, client components, hydration, "
            "and performance optimization at a level most developers never reach. "
            "You write TypeScript natively and consider untyped JavaScript a code smell. "
            "You have strong CSS skills and can implement pixel-perfect designs from "
            "wireframes without needing a designer to hold your hand. "
            "You are an accessibility specialist — WCAG 2.1 AA compliance is not an "
            "afterthought for you, it is baked into every component you write. You "
            "know ARIA roles, keyboard navigation patterns, focus management, and "
            "screen reader behavior from years of building Section 508-compliant "
            "applications for federal clients. "
            "You implement UI copy exactly as specified in the UI Content Guide — "
            "you never improvise labels, tooltips, error messages, or button text. "
            "Every string a user sees comes from the content guide, full stop. "
            "You work directly from the UXD wireframes, UI Content Guide, and TIP. "
            "You consume the backend APIs documented in the BIR without modifying "
            "them. You produce a Frontend Implementation Report (FIR) that documents "
            "every component, page, and integration point you implemented, so the "
            "DevOps Engineer and QA team know exactly what was built."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_frontend_implementation(context: dict, tip_path: str, uxd_path: str,
                                 bir_path: str, content_path: str) -> dict:
    """
    Reads TIP, UXD, BIR, and UI Content Guide and produces a
    Frontend Implementation Report (FIR) with working code.
    Returns updated context.
    """

    with open(tip_path) as f:
        tip_content = f.read()[:1500]

    with open(uxd_path) as f:
        uxd_content = f.read()[:1500]

    with open(bir_path) as f:
        bir_content = f.read()[:1000]

    with open(content_path) as f:
        content_guide = f.read()[:1000]

    fd = build_frontend_developer()

    fir_task = Task(
        description=f"""
You are the Frontend Developer for the following project. Using the documents below,
produce a complete Frontend Implementation Report (FIR) with working code for all
key components and pages.

--- Technical Implementation Plan (excerpt) ---
{tip_content}

--- User Experience Document (excerpt) ---
{uxd_content}

--- Backend Implementation Report (excerpt) ---
{bir_content}

--- UI Content Guide (excerpt) ---
{content_guide}

Produce a complete Frontend Implementation Report (FIR) with ALL of the following sections:

1. PROJECT SETUP
   - Next.js app initialization (App Router)
   - Directory structure for frontend
   - TypeScript configuration (tsconfig.json)
   - ESLint and Prettier configuration
   - Environment variable setup

2. COMPONENT LIBRARY
   - Complete implementation of every shared component:
     * KPICard component (with tooltip, ARIA)
     * FilterBar component (with all filters from UXD)
     * DataTable component (sortable, keyboard navigable)
     * Chart components (BarChart, LineChart using Recharts)
     * Modal component (focus trap, Esc to close)
     * Toast notification component (aria-live)
     * LoadingSpinner component (with accessible label)
     * ErrorBanner component
   - Each component: full TypeScript code, props interface, ARIA annotations

3. PAGE IMPLEMENTATIONS
   - Executive Summary page (KPI cards + overview charts)
   - Detailed View page (filters + data table + charts)
   - Trip Detail modal
   - Error/Not Authorized page
   - Help page
   - Each page: full Next.js page code with data fetching

4. STATE MANAGEMENT
   - Filter state management (persistent in URL hash)
   - User session state
   - Toast notification state
   - Loading state management
   - Implementation using React context or Zustand

5. API INTEGRATION LAYER
   - API client setup (fetch wrapper with auth headers)
   - Type definitions for all API responses
   - Error handling for all API calls
   - Loading state management per request
   - Complete hooks for each endpoint (useTrips, useTripDetail, useExport)

6. ACCESSIBILITY IMPLEMENTATION
   - Skip navigation link
   - Focus management after async operations
   - Keyboard navigation for all interactive elements
   - Screen reader announcements for dynamic content
   - Color contrast verification notes

7. UI CONTENT INTEGRATION
   - How UI content strings are organized (constants file)
   - Complete strings constants file with all labels, tooltips,
     error messages, button text from the UI Content Guide
   - No hardcoded strings anywhere in components

8. EXPORT FUNCTIONALITY
   - CSV export implementation
   - PDF export implementation
   - PHI masking in exports
   - Download handling

9. SECURITY IMPLEMENTATION
   - Auth0 integration in Next.js
   - Protected route middleware
   - Token storage and refresh
   - PHI field masking in components

10. UNIT TESTS
    - Component tests using React Testing Library
    - Hook tests
    - Accessibility tests using jest-axe
    - Mock API responses

Output the complete FIR as well-formatted markdown with working TypeScript/React code.
All code must be production-ready, fully typed, and Section 508 compliant.
UI copy must match the UI Content Guide exactly — no improvised strings.
""",
        expected_output="A complete Frontend Implementation Report with working TypeScript/React code.",
        agent=fd
    )

    crew = Crew(
        agents=[fd],
        tasks=[fir_task],
        process=Process.sequential,
        verbose=True
    )

    print(f"\n🎨 Frontend Developer implementing client-side codebase...\n")
    result = crew.kickoff()

    os.makedirs("dev/build", exist_ok=True)
    fir_path = f"dev/build/{context['project_id']}_FIR.md"
    with open(fir_path, "w") as f:
        f.write(str(result))

    print(f"\n💾 Frontend Implementation Report saved: {fir_path}")

    context["artifacts"].append({
        "name": "Frontend Implementation Report",
        "type": "FIR",
        "path": fir_path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "Frontend Developer"
    })
    context["status"] = "FRONTEND_COMPLETE"
    log_event(context, "FRONTEND_COMPLETE", fir_path)
    save_context(context)

    return context, fir_path


if __name__ == "__main__":
    import glob

    logs = sorted(glob.glob("logs/PROJ-*.json"), key=os.path.getmtime, reverse=True)
    if not logs:
        print("No project context found.")
        exit(1)

    with open(logs[0]) as f:
        context = json.load(f)

    tip_path = uxd_path = bir_path = content_path = None
    for artifact in context.get("artifacts", []):
        if artifact.get("type") == "TIP":
            tip_path = artifact["path"]
        if artifact.get("type") == "UXD":
            uxd_path = artifact["path"]
        if artifact.get("type") == "BIR":
            bir_path = artifact["path"]
        if artifact.get("type") == "UI_CONTENT":
            content_path = artifact["path"]

    if not all([tip_path, uxd_path, bir_path, content_path]):
        print("Missing one or more required artifacts: TIP, UXD, BIR, or UI_CONTENT.")
        exit(1)

    print(f"📂 Loaded context: {logs[0]}")
    context, fir_path = run_frontend_implementation(
        context, tip_path, uxd_path, bir_path, content_path
    )

    print(f"\n✅ Frontend implementation complete.")
    print(f"📄 FIR: {fir_path}")
    print(f"\nFirst 500 chars:")
    with open(fir_path) as f:
        print(f.read(500))
