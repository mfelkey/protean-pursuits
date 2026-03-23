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


def build_mobile_scalability_reviewer() -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/qwen2.5:72b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    return Agent(
        role="Mobile Scalability Reviewer",
        goal=(
            "Review the mobile application architecture for commercial scalability "
            "across API efficiency, local data management, asset delivery, push "
            "notification infrastructure, and multi-tenant mobile patterns."
        ),
        backstory=(
            "You are a senior mobile platform architect with 12 years of experience "
            "scaling mobile apps to millions of users across iOS, Android, and React "
            "Native. You have scaled mobile apps for SaaS platforms with 10,000+ "
            "enterprise tenants, each with hundreds of users on mobile devices. "
            "\n\n"
            "You understand the unique scalability challenges of mobile: "
            "constrained bandwidth and battery, unreliable networks, limited local "
            "storage, app store update cycles, and the need for offline capability "
            "with eventual consistency. "
            "\n\n"
            "YOUR REVIEW DIMENSIONS: "
            "\n\n"
            "1. API CLIENT EFFICIENCY "
            "- Request batching (combine multiple API calls) "
            "- Pagination (cursor-based for large lists) "
            "- Delta sync (only fetch changed records) "
            "- Offline-first architecture with conflict resolution "
            "- Request deduplication and caching (ETags, If-Modified-Since) "
            "- Background sync scheduling (WorkManager / BGTaskScheduler) "
            "- Retry with exponential backoff "
            "\n\n"
            "2. LOCAL DATA MANAGEMENT "
            "- SQLite/Realm/WatermelonDB optimization for large datasets "
            "- Cache eviction policies (LRU, TTL, size-based) "
            "- Storage budget management (warn users before exceeding limits) "
            "- Database migration strategy across app versions "
            "- Efficient list rendering (FlatList/RecyclerView virtualization) "
            "\n\n"
            "3. ASSET DELIVERY & PERFORMANCE "
            "- Image optimization (responsive images, progressive loading, caching) "
            "- Bundle size analysis and code splitting "
            "- Lazy loading of screens and heavy components "
            "- OTA update strategy (CodePush / EAS Update) "
            "- App startup time optimization (< 2s cold start target) "
            "- Memory management and leak prevention "
            "\n\n"
            "4. PUSH NOTIFICATION INFRASTRUCTURE "
            "- Per-tenant notification routing "
            "- High-volume delivery (batch sends, rate limiting) "
            "- Notification channels/categories for user control "
            "- Silent push for background data sync "
            "- Delivery tracking and retry "
            "\n\n"
            "5. MULTI-TENANT MOBILE PATTERNS "
            "- Tenant switching (user belongs to multiple tenants) "
            "- Config-driven feature flags per tenant "
            "- Branded themes/white-labeling support "
            "- Per-tenant data isolation on device "
            "- Tenant-scoped deep linking "
            "\n\n"
            "For every finding: "
            "1. Dimension: API / DATA / ASSETS / PUSH / MULTI-TENANT "
            "2. Severity: CRITICAL / HIGH / MEDIUM / LOW "
            "3. Platform: iOS / Android / RN / All "
            "4. Current state: What exists "
            "5. Required state: What commercial scale requires "
            "6. Remediation: Specific code changes with examples "
            "7. Effort: S / M / L / XL "
            "\n\n"
            "Overall rating per platform: 🟢 SCALE-READY / 🟡 NEEDS WORK / 🔴 NOT SCALABLE "
            "\n\n"
            "OUTPUT DISCIPLINE: Write the complete report. Do not repeat. Do not loop."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_mobile_scalability_review(context: dict, muxd_path: str,
                                   iir_path: str, air_path: str,
                                   rn_guide_path: str, mdir_path: str) -> tuple:
    """Run the Mobile Scalability Review against all mobile artifacts."""
    reviewer = build_mobile_scalability_reviewer()

    muxd_excerpt = ""
    if muxd_path and os.path.exists(muxd_path):
        with open(muxd_path) as f:
            muxd_excerpt = f.read()[:4000]

    iir_excerpt = ""
    if iir_path and os.path.exists(iir_path):
        with open(iir_path) as f:
            iir_excerpt = f.read()[:6000]

    air_excerpt = ""
    if air_path and os.path.exists(air_path):
        with open(air_path) as f:
            air_excerpt = f.read()[:6000]

    rn_excerpt = ""
    if rn_guide_path and os.path.exists(rn_guide_path):
        with open(rn_guide_path) as f:
            rn_excerpt = f.read()[:6000]

    mdir_excerpt = ""
    if mdir_path and os.path.exists(mdir_path):
        with open(mdir_path) as f:
            mdir_excerpt = f.read()[:4000]

    task = Task(
        description=f"""
Perform a comprehensive mobile scalability review. Evaluate whether the mobile
apps can support commercial-scale deployment: 10,000+ tenants, millions of users,
large datasets on device, and global user base.

=== MOBILE UX DOCUMENT ===
{muxd_excerpt}

=== iOS IMPLEMENTATION REPORT ===
{iir_excerpt}

=== ANDROID IMPLEMENTATION REPORT ===
{air_excerpt}

=== REACT NATIVE GUIDE ===
{rn_excerpt}

=== MOBILE DEVOPS REPORT ===
{mdir_excerpt}

=== YOUR MOBILE SCALABILITY REPORT MUST INCLUDE ===

1. EXECUTIVE SUMMARY
   - Per-platform rating: iOS / Android / RN
   - Overall mobile scalability rating
   - Finding counts by dimension and severity

2. API CLIENT EFFICIENCY
   - Request batching implementation
   - Pagination strategy (cursor-based?)
   - Delta sync / incremental fetch
   - Offline-first with conflict resolution
   - Background sync scheduling
   - Retry and backoff patterns
   - Findings per platform

3. LOCAL DATA MANAGEMENT
   - Database choice and optimization
   - Cache eviction policies
   - Storage budget management
   - List virtualization (large datasets in UI)
   - Migration strategy across versions
   - Findings per platform

4. ASSET DELIVERY & PERFORMANCE
   - Image loading and caching strategy
   - Bundle size analysis
   - Lazy loading implementation
   - OTA update strategy
   - Cold start time estimate
   - Memory management patterns
   - Findings per platform

5. PUSH NOTIFICATION INFRASTRUCTURE
   - Notification architecture
   - Per-tenant routing
   - High-volume handling
   - Silent push for background sync
   - Findings

6. MULTI-TENANT MOBILE PATTERNS
   - Tenant switching support
   - Feature flags per tenant
   - Branded themes / white-label readiness
   - Per-tenant data isolation on device
   - Tenant-scoped deep linking
   - Findings per platform

7. FINDINGS TABLE
   | # | Dimension | Severity | Platform | Current | Required | Remediation | Effort |

8. REMEDIATION ROADMAP
   - Priority 1 (before launch)
   - Priority 2 (first month)
   - Priority 3 (first quarter)

9. PER-PLATFORM RATING
   - iOS: 🟢/🟡/🔴
   - Android: 🟢/🟡/🔴
   - React Native: 🟢/🟡/🔴
   - OVERALL MOBILE: 🟢 SCALE-READY / 🟡 NEEDS WORK / 🔴 NOT SCALABLE

No placeholders. No TODO comments. Every finding must reference specific
code and include a concrete remediation example.
""",
        expected_output=(
            "A complete Mobile Scalability Report with per-platform assessment, "
            "findings table, remediation roadmap, and 🟢/🟡/🔴 rating."
        ),
        agent=reviewer
    )

    crew = Crew(
        agents=[reviewer],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )

    print("\n📈 Mobile Scalability Review: Analyzing mobile apps for commercial readiness...\n")
    result = crew.kickoff()

    os.makedirs("/home/mfelkey/dev-team/dev/mobile/scalability", exist_ok=True)
    msar_path = f"/home/mfelkey/dev-team/dev/mobile/scalability/{context['project_id']}_MOBILE_SAR.md"
    with open(msar_path, "w") as f:
        f.write(str(result))

    print(f"\n💾 Mobile Scalability Report saved: {msar_path}")

    context["artifacts"].append({
        "name": "Mobile Scalability Architecture Report",
        "type": "MOBILE_SAR",
        "path": msar_path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "Mobile Scalability Reviewer"
    })
    log_event(context, "MOBILE_SAR_COMPLETE", msar_path)
    save_context(context)
    return context, msar_path


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

    muxd_path = iir_path = air_path = rn_guide_path = mdir_path = None
    for artifact in context.get("artifacts", []):
        atype = artifact.get("type", "")
        if atype == "MUXD": muxd_path = artifact["path"]
        elif atype == "IIR": iir_path = artifact["path"]
        elif atype == "AIR": air_path = artifact["path"]
        elif atype in ("RN_GUIDE", "RNIR"): rn_guide_path = artifact["path"]
        elif atype == "MDIR": mdir_path = artifact["path"]

    if not (iir_path or air_path or rn_guide_path):
        print("No mobile artifacts found. Run mobile build agents first.")
        exit(1)

    print(f"📂 Loaded context: {logs[0]}")
    print(f"📱 MUXD: {muxd_path or 'NOT FOUND'}")
    print(f"🍎 IIR: {iir_path or 'NOT FOUND'}")
    print(f"🤖 AIR: {air_path or 'NOT FOUND'}")
    print(f"⚛️  RN:  {rn_guide_path or 'NOT FOUND'}")
    print(f"📦 MDIR: {mdir_path or 'NOT FOUND'}")

    context, msar_path = run_mobile_scalability_review(
        context, muxd_path, iir_path, air_path, rn_guide_path, mdir_path
    )
    print(f"\n✅ Mobile Scalability Review complete: {msar_path}")
    with open(msar_path) as f:
        print(f.read()[:500])
