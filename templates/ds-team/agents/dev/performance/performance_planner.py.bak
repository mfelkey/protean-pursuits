import sys
sys.path.insert(0, "/home/mfelkey/dev-team")

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM

load_dotenv("/home/mfelkey/dev-team/config/.env")

try:
    from agents.orchestrator.orchestrator import log_event, save_context
except ImportError:
    def log_event(ctx, event, path): pass
    def save_context(ctx): pass


def build_performance_planner() -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/qwen2.5:72b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    return Agent(
        role="Performance Engineer (Planning)",
        goal=(
            "Analyze the system architecture and requirements to establish concrete "
            "performance budgets, benchmarking targets, and profiling strategy that "
            "build agents must meet and verify agents will measure against."
        ),
        backstory=(
            "You are a Principal Performance Engineer with 14 years of experience "
            "optimizing web applications, APIs, mobile apps, and desktop software "
            "for commercial-scale workloads. You have worked at companies where "
            "performance was a product differentiator — sub-100ms API responses, "
            "sub-2s page loads, 60fps animations, and efficient battery usage on mobile. "
            "\n\n"
            "You understand that performance is not an afterthought — it must be "
            "designed in from the start. Your job in the planning phase is to set "
            "the performance contract that every build agent must honor. "
            "\n\n"
            "YOUR PERFORMANCE BUDGET CATEGORIES: "
            "\n\n"
            "1. API LATENCY BUDGETS "
            "- Per-endpoint P50/P95/P99 latency targets "
            "- Database query time budgets (per query class) "
            "- Upstream dependency timeout budgets "
            "- Cold start vs warm latency targets "
            "- Batch operation throughput targets "
            "\n\n"
            "2. FRONTEND PERFORMANCE BUDGETS "
            "- Largest Contentful Paint (LCP) target "
            "- First Input Delay (FID) / Interaction to Next Paint (INP) target "
            "- Cumulative Layout Shift (CLS) target "
            "- Time to Interactive (TTI) target "
            "- Total bundle size budget (JS, CSS, images) "
            "- Per-route code split budgets "
            "- Image size budgets by context "
            "\n\n"
            "3. MOBILE PERFORMANCE BUDGETS "
            "- Cold start time target (< 2s) "
            "- Screen transition time (< 300ms) "
            "- Memory ceiling per platform "
            "- Battery drain budget (% per hour of active use) "
            "- Offline-to-online sync time budget "
            "- List scroll performance (60fps target) "
            "\n\n"
            "4. DESKTOP PERFORMANCE BUDGETS "
            "- Startup time target "
            "- Memory baseline and ceiling "
            "- IPC round-trip latency budget "
            "- File operation throughput targets "
            "- Renderer frame budget (16ms for 60fps) "
            "\n\n"
            "5. DATABASE PERFORMANCE BUDGETS "
            "- Query time by complexity class (simple lookup, filtered list, "
            "  aggregation, full-text search, join-heavy report) "
            "- Connection pool utilization ceiling "
            "- Index coverage requirement "
            "- Migration execution time budgets "
            "\n\n"
            "6. INFRASTRUCTURE BUDGETS "
            "- Horizontal scaling trigger thresholds "
            "- Container resource limits (CPU, memory) "
            "- Health check response time "
            "- Deployment rollout time budget "
            "\n\n"
            "7. LOAD TESTING TARGETS "
            "- Concurrent user targets (normal, peak, stress) "
            "- Requests per second targets "
            "- Error rate ceiling under load "
            "- Degradation profile (what degrades first, gracefully) "
            "\n\n"
            "For each budget you specify: "
            "- Target value (e.g., P95 < 200ms) "
            "- Measurement method (tool, metric source) "
            "- Regression threshold (what triggers a build failure) "
            "- Owner (which agent/component is responsible) "
            "\n\n"
            "You also define the BENCHMARKING SUITE: specific k6, Lighthouse, "
            "and profiling scripts that the Performance Auditor will run in the "
            "verify phase. "
            "\n\n"
            "OUTPUT DISCIPLINE: Write the complete plan. Do not repeat sections. "
            "Do not loop. Stop after the benchmarking suite definition."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_performance_planning(context: dict, tad_path: str,
                              prd_path: str, tip_path: str = None) -> tuple:
    """Set performance budgets based on architecture and requirements."""
    planner = build_performance_planner()

    tad_excerpt = ""
    if tad_path and os.path.exists(tad_path):
        with open(tad_path) as f:
            tad_excerpt = f.read()[:6000]

    prd_excerpt = ""
    if prd_path and os.path.exists(prd_path):
        with open(prd_path) as f:
            prd_excerpt = f.read()[:4000]

    tip_excerpt = ""
    if tip_path and os.path.exists(tip_path):
        with open(tip_path) as f:
            tip_excerpt = f.read()[:4000]

    task = Task(
        description=f"""
Analyze the system architecture and requirements to produce a comprehensive
Performance Budget Document (PBD) that sets measurable targets for every
component of the system.

Build agents will code to these budgets. The Performance Auditor will verify
against them after build.

=== PRODUCT REQUIREMENTS DOCUMENT (PRD) ===
{prd_excerpt}

=== TECHNICAL ARCHITECTURE DOCUMENT (TAD) ===
{tad_excerpt}

=== TECHNICAL IMPLEMENTATION PLAN (TIP) ===
{tip_excerpt if tip_excerpt else "(TIP not yet available — set budgets from TAD)"}

=== YOUR PERFORMANCE BUDGET DOCUMENT (PBD) MUST INCLUDE ===

1. EXECUTIVE SUMMARY
   - System performance tier classification (real-time / interactive / batch)
   - Key constraints identified from requirements
   - Top 5 performance risks

2. API LATENCY BUDGETS
   For each endpoint or endpoint class:
   | Endpoint Pattern | P50 | P95 | P99 | DB Budget | Upstream Budget | Owner |
   - Cold start budget
   - Batch operation throughput

3. FRONTEND PERFORMANCE BUDGETS
   | Metric | Target | Regression Threshold | Measurement Tool |
   - Core Web Vitals targets (LCP, INP, CLS)
   - Bundle size budgets per route
   - Image optimization requirements
   - Font loading strategy and budget

4. MOBILE PERFORMANCE BUDGETS (if applicable)
   Per platform (iOS / Android / RN):
   | Metric | Target | Measurement | Regression Threshold |
   - Cold start, screen transitions, memory, battery, scroll FPS

5. DESKTOP PERFORMANCE BUDGETS (if applicable)
   | Metric | Target | Measurement | Regression Threshold |
   - Startup, memory, IPC latency, frame budget

6. DATABASE PERFORMANCE BUDGETS
   | Query Class | Max Time | Max Rows Scanned | Index Required |
   - Connection pool sizing recommendation
   - Migration time budget

7. INFRASTRUCTURE BUDGETS
   | Resource | Baseline | Ceiling | Scale Trigger |
   - Container limits, HPA thresholds, health check budgets

8. LOAD TESTING TARGETS
   | Scenario | Concurrent Users | RPS | Error Rate Ceiling | Latency Ceiling |
   - Normal load, peak load, stress test, soak test

9. BENCHMARKING SUITE DEFINITION
   For each test category, specify:
   - Tool (k6, Lighthouse, React Profiler, Xcode Instruments, Android Profiler)
   - Script outline (what it measures, how it runs)
   - Pass/fail criteria
   - CI integration approach (when it runs, what blocks merge)

10. PERFORMANCE REGRESSION POLICY
    - What triggers a regression alert
    - Who is responsible for each category
    - Escalation path for budget violations
    - Grace period and exception process

No placeholders. Every budget must have a specific number. Every target must
have a measurement method. This document is the contract build agents code against.
""",
        expected_output=(
            "A complete Performance Budget Document (PBD) with specific numeric "
            "targets for every component, measurement methods, and benchmarking "
            "suite definition."
        ),
        agent=planner
    )

    crew = Crew(
        agents=[planner],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )

    print("\n⚡ Performance Engineer setting performance budgets...\n")
    result = crew.kickoff()

    os.makedirs("/home/mfelkey/dev-team/dev/performance", exist_ok=True)
    pbd_path = f"/home/mfelkey/dev-team/dev/performance/{context['project_id']}_PBD.md"
    with open(pbd_path, "w") as f:
        f.write(str(result))

    print(f"\n💾 Performance Budget Document saved: {pbd_path}")

    context["artifacts"].append({
        "name": "Performance Budget Document",
        "type": "PBD",
        "path": pbd_path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "Performance Engineer (Planning)"
    })
    log_event(context, "PBD_COMPLETE", pbd_path)
    save_context(context)
    return context, pbd_path


if __name__ == "__main__":
    import glob

    logs = sorted(
        glob.glob("/home/mfelkey/dev-team/logs/PROJ-*.json"),
        key=os.path.getmtime,
        reverse=True
    )
    if not logs:
        print("No project context found.")
        exit(1)

    with open(logs[0]) as f:
        context = json.load(f)

    tad_path = prd_path = tip_path = None
    for artifact in context.get("artifacts", []):
        atype = artifact.get("type", "")
        if atype == "TAD": tad_path = artifact["path"]
        elif atype == "PRD": prd_path = artifact["path"]
        elif atype == "TIP": tip_path = artifact["path"]

    if not tad_path:
        print("Missing TAD. Run Technical Architect first.")
        exit(1)

    print(f"📂 Loaded context: {logs[0]}")
    print(f"📋 PRD: {prd_path or 'NOT FOUND'}")
    print(f"🏗️  TAD: {tad_path}")
    print(f"📋 TIP: {tip_path or '(not yet available)'}")

    context, pbd_path = run_performance_planning(context, tad_path, prd_path, tip_path)
    print(f"\n✅ Performance budgets set: {pbd_path}")
    with open(pbd_path) as f:
        print(f.read()[:500])
