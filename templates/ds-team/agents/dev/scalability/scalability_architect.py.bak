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


def build_scalability_architect() -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/qwen2.5:72b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    return Agent(
        role="Scalability Architect",
        goal=(
            "Review the complete built system and assess its readiness for "
            "commercial-scale deployment across four dimensions: multi-tenant SaaS, "
            "high-throughput API, large dataset handling, and global distribution. "
            "Produce specific, actionable remediation for every scalability gap."
        ),
        backstory=(
            "You are a Principal Scalability Architect with 15 years of experience "
            "scaling SaaS platforms from startup to enterprise. You have scaled systems "
            "to serve 10,000+ tenants, handle 50k+ requests/second, manage datasets "
            "with billions of rows, and operate across multiple global regions with "
            "sub-100ms latency targets. "
            "\n\n"
            "You have led scalability reviews at companies processing millions of "
            "transactions daily. You understand the difference between systems that "
            "work at demo scale and systems that work at commercial scale — and you "
            "know exactly where the breaking points are. "
            "\n\n"
            "YOUR FOUR REVIEW DIMENSIONS: "
            "\n\n"
            "1. MULTI-TENANT SaaS READINESS "
            "You evaluate whether the system can serve many customers from a single "
            "deployment without cross-tenant data leakage, performance interference, "
            "or configuration rigidity. You check for: "
            "- Tenant isolation strategy (row-level, schema-level, or database-level) "
            "- Tenant-aware middleware (every request scoped to a tenant) "
            "- Per-tenant configuration (feature flags, branding, limits) "
            "- Tenant-scoped data access (no unscoped queries that could leak data) "
            "- Tenant onboarding automation (provisioning, seed data, config) "
            "- Billing/usage metering hooks "
            "- Noisy neighbor protection (per-tenant rate limits, resource quotas) "
            "\n\n"
            "2. HIGH-THROUGHPUT API (10,000+ req/sec) "
            "You evaluate whether the API layer can handle commercial traffic volumes "
            "without degradation. You check for: "
            "- Connection pooling (database, HTTP clients, Redis) "
            "- Caching strategy (what's cached, TTL, invalidation, cache-aside vs write-through) "
            "- Redis/Memcached for session and hot-path data "
            "- Async job queues for non-blocking operations (email, reports, ETL) "
            "- Database query efficiency (N+1 detection, missing indexes, full table scans) "
            "- Pagination strategy (cursor-based, not offset-based for large datasets) "
            "- Rate limiting (per-tenant, per-endpoint, with backpressure) "
            "- Horizontal scaling readiness (stateless services, no sticky sessions) "
            "- Load balancing configuration "
            "- Graceful degradation under load (circuit breakers, bulkheads) "
            "\n\n"
            "3. LARGE DATASET HANDLING (millions of records, analytics) "
            "You evaluate whether the data layer can handle commercial data volumes "
            "without query timeouts or storage explosions. You check for: "
            "- Table partitioning strategy (range, hash, or list partitioning) "
            "- Read replica configuration for analytics queries "
            "- Materialized views for expensive aggregations "
            "- Index coverage for all query patterns (composite indexes, partial indexes) "
            "- EXPLAIN ANALYZE on critical queries — estimated row scans "
            "- Archival strategy (hot/warm/cold data tiers) "
            "- Bulk import/export pipelines (streaming, not load-all-into-memory) "
            "- Time-series optimization if applicable "
            "- Search infrastructure (full-text search, Elasticsearch/Typesense) "
            "- Connection pool sizing relative to concurrent users "
            "\n\n"
            "4. GLOBAL DISTRIBUTION (CDN, multi-region, edge) "
            "You evaluate whether the system can serve users worldwide with acceptable "
            "latency. You check for: "
            "- CDN configuration for static assets (JS, CSS, images, fonts) "
            "- Edge caching for API responses where appropriate "
            "- Multi-region database replication strategy "
            "- Session affinity vs stateless design for multi-region "
            "- Asset optimization (image compression, WebP/AVIF, lazy loading) "
            "- Bundle splitting and code splitting (frontend) "
            "- DNS-based routing (latency-based, geolocation-based) "
            "- Data residency compliance (GDPR, regional data requirements) "
            "- Deployment pipeline support for multi-region rollout "
            "- Failover and disaster recovery across regions "
            "\n\n"
            "For every finding you provide: "
            "1. Dimension: MULTI-TENANT / THROUGHPUT / DATASET / GLOBAL "
            "2. Severity: CRITICAL / HIGH / MEDIUM / LOW "
            "3. Component: Which artifact and code section "
            "4. Current state: What exists now "
            "5. Required state: What commercial scale requires "
            "6. Remediation: Specific code/config changes with examples "
            "7. Effort: S / M / L / XL estimate "
            "\n\n"
            "Your Scalability Architecture Report (SAR) concludes with: "
            "- 🟢 SCALE-READY — No CRITICAL findings. System can handle commercial load. "
            "- 🟡 NEEDS WORK — HIGH findings exist with clear remediation path. "
            "- 🔴 NOT SCALABLE — CRITICAL architectural gaps. Redesign required before launch. "
            "\n\n"
            "OUTPUT DISCIPLINE: Write the complete report. Do not repeat sections. "
            "Do not loop. Stop after the remediation roadmap."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_scalability_review(context: dict, tad_path: str, bir_path: str,
                           fir_path: str, dbar_path: str, dir_path: str) -> tuple:
    """Run the Scalability Architect against all built artifacts."""
    architect = build_scalability_architect()

    # Load upstream artifacts with generous context
    tad_excerpt = ""
    if tad_path and os.path.exists(tad_path):
        with open(tad_path) as f:
            tad_excerpt = f.read()[:6000]

    bir_excerpt = ""
    if bir_path and os.path.exists(bir_path):
        with open(bir_path) as f:
            bir_excerpt = f.read()[:8000]

    fir_excerpt = ""
    if fir_path and os.path.exists(fir_path):
        with open(fir_path) as f:
            fir_excerpt = f.read()[:6000]

    dbar_excerpt = ""
    if dbar_path and os.path.exists(dbar_path):
        with open(dbar_path) as f:
            dbar_excerpt = f.read()[:6000]

    dir_excerpt = ""
    if dir_path and os.path.exists(dir_path):
        with open(dir_path) as f:
            dir_excerpt = f.read()[:5000]

    task = Task(
        description=f"""
Perform a comprehensive commercial scalability review of the built system.
Evaluate all artifacts against four dimensions: multi-tenant SaaS, high-throughput
API, large dataset handling, and global distribution.

The target is a system that can serve 10,000+ tenants, handle 10k+ requests/second,
manage millions of database records with analytics workloads, and serve users globally
with sub-200ms latency.

=== TECHNICAL ARCHITECTURE DOCUMENT (TAD) ===
{tad_excerpt}

=== BACKEND IMPLEMENTATION REPORT (BIR) ===
{bir_excerpt}

=== FRONTEND IMPLEMENTATION REPORT (FIR) ===
{fir_excerpt}

=== DATABASE ADMINISTRATION REPORT (DBAR) ===
{dbar_excerpt}

=== DEVOPS IMPLEMENTATION REPORT (DIR) ===
{dir_excerpt}

=== YOUR SCALABILITY ARCHITECTURE REPORT (SAR) MUST INCLUDE ===

1. EXECUTIVE SUMMARY
   - Overall rating: 🟢 SCALE-READY / 🟡 NEEDS WORK / 🔴 NOT SCALABLE
   - Per-dimension rating
   - Finding counts by severity
   - Estimated total remediation effort

2. MULTI-TENANT SaaS ASSESSMENT
   a. Tenant Isolation
      - Current state: How is tenant data separated?
      - Database strategy: row-level (tenant_id column), schema-per-tenant, or DB-per-tenant?
      - Risk: Can an unscoped query return another tenant's data?
      - Findings with specific file/code references
   b. Tenant-Aware Middleware
      - Is every API request scoped to a tenant?
      - How is tenant context injected (JWT claim, subdomain, header)?
      - Findings
   c. Per-Tenant Configuration
      - Feature flags, branding, rate limits, storage quotas
      - Findings
   d. Tenant Onboarding
      - Provisioning automation, seed data, welcome flow
      - Findings
   e. Noisy Neighbor Protection
      - Per-tenant rate limiting, resource quotas, query timeouts
      - Findings

3. HIGH-THROUGHPUT API ASSESSMENT (10k+ req/sec target)
   a. Connection Management
      - Database pool size and configuration
      - HTTP client pooling
      - Redis/cache connections
      - Findings
   b. Caching Strategy
      - What is cached? TTLs? Invalidation strategy?
      - Hot-path identification
      - Findings
   c. Async Processing
      - Job queue for non-blocking operations
      - Background workers, retries, dead letter queues
      - Findings
   d. Query Efficiency
      - N+1 query detection
      - Missing indexes on filtered/sorted columns
      - Pagination strategy (cursor vs offset)
      - Findings
   e. Horizontal Scaling
      - Stateless services? Sticky sessions?
      - Load balancer configuration
      - Auto-scaling rules
      - Findings
   f. Resilience
      - Circuit breakers, bulkheads, retry with backoff
      - Graceful degradation under load
      - Health check endpoints
      - Findings

4. LARGE DATASET ASSESSMENT (millions of records)
   a. Table Partitioning
      - Which tables need partitioning?
      - Partition strategy (range by date, hash by tenant_id)
      - Findings
   b. Read Replicas
      - Analytics queries routed to replicas?
      - Replication lag handling
      - Findings
   c. Materialized Views
      - Expensive aggregations pre-computed?
      - Refresh strategy
      - Findings
   d. Index Analysis
      - Composite indexes for multi-column filters
      - Partial indexes for common WHERE clauses
      - Covering indexes for frequent SELECT patterns
      - Findings
   e. Data Lifecycle
      - Archival strategy (hot/warm/cold)
      - Retention policies
      - Bulk import/export (streaming, not in-memory)
      - Findings

5. GLOBAL DISTRIBUTION ASSESSMENT
   a. CDN & Asset Delivery
      - Static asset CDN configuration
      - Image optimization (WebP/AVIF, responsive images)
      - Font loading strategy
      - Findings
   b. Frontend Performance
      - Bundle splitting, code splitting, tree shaking
      - Lazy loading of routes and components
      - Service worker / offline strategy
      - Findings
   c. Multi-Region Readiness
      - Database replication across regions
      - DNS-based routing
      - Session management for multi-region
      - Findings
   d. Data Residency
      - GDPR / regional compliance
      - Per-tenant data location rules
      - Findings

6. COMPLETE FINDINGS TABLE
   | # | Dimension | Severity | Component | Current State | Required State | Remediation | Effort |

7. REMEDIATION ROADMAP
   - Priority 1 (before launch): CRITICAL items
   - Priority 2 (first month): HIGH items
   - Priority 3 (first quarter): MEDIUM items
   - Estimated total effort in developer-weeks

8. OVERALL RATING
   - Multi-Tenant: 🟢/🟡/🔴
   - High-Throughput: 🟢/🟡/🔴
   - Large Dataset: 🟢/🟡/🔴
   - Global Distribution: 🟢/🟡/🔴
   - OVERALL: 🟢 SCALE-READY / 🟡 NEEDS WORK / 🔴 NOT SCALABLE

No placeholders. No TODO comments. Every finding must reference specific
code/config and include a concrete remediation example.
""",
        expected_output=(
            "A complete Scalability Architecture Report (SAR) with per-dimension "
            "assessment, findings table with specific remediation, and overall "
            "🟢/🟡/🔴 rating."
        ),
        agent=architect
    )

    crew = Crew(
        agents=[architect],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )

    print("\n📈 Scalability Architect reviewing system for commercial readiness...\n")
    result = crew.kickoff()

    os.makedirs("/home/mfelkey/dev-team/dev/scalability", exist_ok=True)
    sar_path = f"/home/mfelkey/dev-team/dev/scalability/{context['project_id']}_SAR.md"
    with open(sar_path, "w") as f:
        f.write(str(result))

    print(f"\n💾 Scalability Architecture Report saved: {sar_path}")

    context["artifacts"].append({
        "name": "Scalability Architecture Report",
        "type": "SAR",
        "path": sar_path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "Scalability Architect"
    })
    log_event(context, "SAR_COMPLETE", sar_path)
    save_context(context)
    return context, sar_path


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

    tad_path = bir_path = fir_path = dbar_path = dir_path = None
    for artifact in context.get("artifacts", []):
        atype = artifact.get("type", "")
        if atype == "TAD": tad_path = artifact["path"]
        elif atype == "BIR": bir_path = artifact["path"]
        elif atype == "FIR": fir_path = artifact["path"]
        elif atype == "DBAR": dbar_path = artifact["path"]
        elif atype == "DIR": dir_path = artifact["path"]

    if not bir_path:
        print("Missing BIR artifact in context. Run build agents first.")
        exit(1)

    print(f"📂 Loaded context: {logs[0]}")
    print(f"🏗️  TAD: {tad_path or 'NOT FOUND'}")
    print(f"⚙️  BIR: {bir_path}")
    print(f"🖥️  FIR: {fir_path or 'NOT FOUND'}")
    print(f"🗄️  DBAR: {dbar_path or 'NOT FOUND'}")
    print(f"🚀 DIR: {dir_path or 'NOT FOUND'}")

    context, sar_path = run_scalability_review(
        context, tad_path, bir_path, fir_path, dbar_path, dir_path
    )
    print(f"\n✅ Scalability review complete: {sar_path}")
    with open(sar_path) as f:
        print(f.read()[:500])
