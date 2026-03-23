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


def build_performance_auditor() -> Agent:
    llm = LLM(
        model=os.getenv("TIER2_MODEL", "ollama/qwen2.5-coder:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    return Agent(
        role="Performance Engineer (Audit)",
        goal=(
            "Review all built code against the Performance Budget Document and "
            "identify every violation, potential bottleneck, and optimization "
            "opportunity. Produce a rated Performance Audit Report."
        ),
        backstory=(
            "You are a Principal Performance Engineer conducting a post-build audit. "
            "The Performance Planner set budgets in the PBD. Your job is to review "
            "every line of built code and determine whether those budgets will be met. "
            "\n\n"
            "You are expert at static performance analysis — identifying bottlenecks "
            "from code review without running it. You look for: "
            "\n\n"
            "API & BACKEND: "
            "- N+1 query patterns (ORM loops that generate one query per iteration) "
            "- Missing database indexes for WHERE/ORDER BY/JOIN columns "
            "- Synchronous operations that should be async (email, file I/O, external API) "
            "- Unbounded queries (SELECT * with no LIMIT on large tables) "
            "- Missing pagination or offset-based pagination on large datasets "
            "- Inefficient serialization (entire object graphs instead of projections) "
            "- Missing connection pooling or misconfigured pool sizes "
            "- Missing caching on hot-path reads "
            "- Blocking operations in request handlers "
            "- Memory leaks (unclosed streams, growing arrays, event listener accumulation) "
            "\n\n"
            "FRONTEND: "
            "- Bundle size violations (unoptimized imports, no tree shaking) "
            "- Missing code splitting on routes "
            "- Render-blocking resources (synchronous scripts, unoptimized CSS) "
            "- Unoptimized images (no lazy loading, no responsive srcset, no WebP) "
            "- Excessive re-renders (missing memoization, unstable references) "
            "- Layout thrashing (forced synchronous layouts) "
            "- Missing virtual scrolling for long lists "
            "\n\n"
            "MOBILE: "
            "- Main thread blocking (heavy computation, synchronous I/O) "
            "- Memory leaks (unreleased listeners, retained views) "
            "- Excessive bridge calls (React Native JS-to-native overhead) "
            "- Unoptimized list rendering (missing keyExtractor, no getItemLayout) "
            "- Large image loading without caching/resizing "
            "- Missing background task scheduling "
            "\n\n"
            "DESKTOP: "
            "- Main process blocking (Electron) / main thread blocking (Tauri) "
            "- IPC overhead (too many round trips, large payloads) "
            "- Memory accumulation over long sessions "
            "- Renderer process memory leaks "
            "\n\n"
            "DATABASE: "
            "- Full table scans on tables > 10k rows "
            "- Missing composite indexes for multi-column filters "
            "- Expensive JOINs without index support "
            "- Missing EXPLAIN ANALYZE annotations on complex queries "
            "- Unpartitioned tables that will grow past 1M rows "
            "\n\n"
            "For every finding you provide: "
            "1. Category: API / FRONTEND / MOBILE / DESKTOP / DATABASE / INFRA "
            "2. Budget violated: Reference specific PBD target "
            "3. Severity: CRITICAL / HIGH / MEDIUM / LOW "
            "4. File and line reference "
            "5. Current code (the problematic pattern) "
            "6. Recommended fix (concrete code example) "
            "7. Expected improvement (quantified where possible) "
            "\n\n"
            "Your Performance Audit Report (PAR) concludes with: "
            "- 🟢 MEETS BUDGETS — No CRITICAL/HIGH violations. Ship it. "
            "- 🟡 NEEDS OPTIMIZATION — HIGH violations with clear fixes. "
            "- 🔴 BUDGET VIOLATION — CRITICAL performance gaps. Fix before launch. "
            "\n\n"
            "OUTPUT DISCIPLINE: Write the complete report. Do not repeat. Stop "
            "after the overall rating."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_performance_audit(context: dict, pbd_path: str,
                           bir_path: str, fir_path: str = None,
                           dir_path: str = None, dbar_path: str = None,
                           dskr_path: str = None) -> tuple:
    """Audit built code against performance budgets."""
    auditor = build_performance_auditor()

    pbd_excerpt = ""
    if pbd_path and os.path.exists(pbd_path):
        with open(pbd_path) as f:
            pbd_excerpt = f.read()[:6000]

    bir_excerpt = ""
    if bir_path and os.path.exists(bir_path):
        with open(bir_path) as f:
            bir_excerpt = f.read()[:8000]

    fir_excerpt = ""
    if fir_path and os.path.exists(fir_path):
        with open(fir_path) as f:
            fir_excerpt = f.read()[:6000]

    dir_excerpt = ""
    if dir_path and os.path.exists(dir_path):
        with open(dir_path) as f:
            dir_excerpt = f.read()[:4000]

    dbar_excerpt = ""
    if dbar_path and os.path.exists(dbar_path):
        with open(dbar_path) as f:
            dbar_excerpt = f.read()[:4000]

    dskr_excerpt = ""
    if dskr_path and os.path.exists(dskr_path):
        with open(dskr_path) as f:
            dskr_excerpt = f.read()[:4000]

    task = Task(
        description=f"""
Perform a comprehensive performance audit of all built code against the
Performance Budget Document. Identify every budget violation, bottleneck,
and optimization opportunity.

=== PERFORMANCE BUDGET DOCUMENT (PBD) ===
{pbd_excerpt}

=== BACKEND IMPLEMENTATION REPORT (BIR) ===
{bir_excerpt}

=== FRONTEND IMPLEMENTATION REPORT (FIR) ===
{fir_excerpt if fir_excerpt else "(No FIR)"}

=== DEVOPS IMPLEMENTATION REPORT (DIR) ===
{dir_excerpt if dir_excerpt else "(No DIR)"}

=== DATABASE ADMINISTRATION REPORT (DBAR) ===
{dbar_excerpt if dbar_excerpt else "(No DBAR)"}

=== DESKTOP IMPLEMENTATION REPORT (DSKR) ===
{dskr_excerpt if dskr_excerpt else "(No DSKR — no desktop component)"}

=== YOUR PERFORMANCE AUDIT REPORT (PAR) MUST INCLUDE ===

1. EXECUTIVE SUMMARY
   - Overall rating: 🟢 MEETS BUDGETS / 🟡 NEEDS OPTIMIZATION / 🔴 BUDGET VIOLATION
   - Findings by severity and category
   - Top 5 highest-impact issues

2. API & BACKEND AUDIT
   For each finding:
   | # | Budget Reference | Severity | File:Line | Issue | Fix | Expected Improvement |
   - N+1 queries detected
   - Missing async patterns
   - Unbounded queries
   - Caching gaps
   - Connection pool issues

3. FRONTEND AUDIT
   | # | Budget Reference | Severity | File:Line | Issue | Fix | Expected Improvement |
   - Bundle size analysis
   - Core Web Vitals risk assessment
   - Render performance issues
   - Image optimization gaps

4. DATABASE AUDIT
   | # | Budget Reference | Severity | File:Line | Issue | Fix | Expected Improvement |
   - Missing indexes
   - Full table scan risks
   - Partition recommendations
   - Query optimization

5. INFRASTRUCTURE AUDIT
   | # | Budget Reference | Severity | Issue | Fix |
   - Container sizing
   - Auto-scaling configuration
   - Health check performance

6. DESKTOP AUDIT (if applicable)
   | # | Budget Reference | Severity | File:Line | Issue | Fix |
   - Main thread blocking
   - IPC efficiency
   - Memory management

7. COMPLETE FINDINGS TABLE
   | # | Category | Budget Ref | Severity | File:Line | Issue | Fix | Effort |

8. OPTIMIZATION ROADMAP
   - Priority 1 (CRITICAL — fix before launch)
   - Priority 2 (HIGH — fix in first sprint)
   - Priority 3 (MEDIUM — optimization backlog)

9. BENCHMARKING SCRIPT REVIEW
   - Are the PBD-defined benchmark scripts implementable against the built code?
   - Any gaps in benchmark coverage?
   - CI integration recommendations

10. OVERALL RATING
    - API: 🟢/🟡/🔴
    - Frontend: 🟢/🟡/🔴
    - Database: 🟢/🟡/🔴
    - Infrastructure: 🟢/🟡/🔴
    - Desktop: 🟢/🟡/🔴 (if applicable)
    - OVERALL: 🟢 MEETS BUDGETS / 🟡 NEEDS OPTIMIZATION / 🔴 BUDGET VIOLATION

No placeholders. Every finding must reference specific code and include
a concrete fix with expected performance improvement.
""",
        expected_output=(
            "A complete Performance Audit Report (PAR) with findings table, "
            "optimization roadmap, and 🟢/🟡/🔴 rating against PBD budgets."
        ),
        agent=auditor
    )

    crew = Crew(
        agents=[auditor],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )

    print("\n⚡ Performance Auditor reviewing built code against budgets...\n")
    result = crew.kickoff()

    os.makedirs("/home/mfelkey/dev-team/dev/performance", exist_ok=True)
    par_path = f"/home/mfelkey/dev-team/dev/performance/{context['project_id']}_PAR.md"
    with open(par_path, "w") as f:
        f.write(str(result))

    print(f"\n💾 Performance Audit Report saved: {par_path}")

    context["artifacts"].append({
        "name": "Performance Audit Report",
        "type": "PAR",
        "path": par_path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "Performance Engineer (Audit)"
    })
    log_event(context, "PAR_COMPLETE", par_path)
    save_context(context)
    return context, par_path


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

    pbd_path = bir_path = fir_path = dir_path = dbar_path = dskr_path = None
    for artifact in context.get("artifacts", []):
        atype = artifact.get("type", "")
        if atype == "PBD": pbd_path = artifact["path"]
        elif atype == "BIR": bir_path = artifact["path"]
        elif atype == "FIR": fir_path = artifact["path"]
        elif atype == "DIR": dir_path = artifact["path"]
        elif atype == "DBAR": dbar_path = artifact["path"]
        elif atype == "DSKR": dskr_path = artifact["path"]

    if not pbd_path:
        print("Missing PBD. Run Performance Planner first.")
        exit(1)
    if not bir_path:
        print("Missing BIR. Run build agents first.")
        exit(1)

    print(f"📂 Loaded context: {logs[0]}")
    print(f"⚡ PBD: {pbd_path}")
    print(f"⚙️  BIR: {bir_path}")
    print(f"🖥️  FIR: {fir_path or 'N/A'}")
    print(f"🚀 DIR: {dir_path or 'N/A'}")
    print(f"🗄️  DBAR: {dbar_path or 'N/A'}")
    print(f"🖥️  DSKR: {dskr_path or 'N/A'}")

    context, par_path = run_performance_audit(
        context, pbd_path, bir_path, fir_path, dir_path, dbar_path, dskr_path
    )
    print(f"\n✅ Performance audit complete: {par_path}")
    with open(par_path) as f:
        print(f.read()[:500])
