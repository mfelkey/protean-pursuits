import sys
sys.path.insert(0, "/home/mfelkey/dev-team")

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from agents.orchestrator.orchestrator import log_event, save_context

load_dotenv("config/.env")

def build_database_admin() -> Agent:
    llm = LLM(
        model=os.getenv("TIER2_MODEL", "ollama/qwen3-coder:30b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    return Agent(
        role="Database Administrator",
        goal=(
            "Own the database layer completely — schema integrity, query performance, "
            "index strategy, migration safety, audit design, and capacity planning — "
            "so that the application runs reliably, securely, and at scale."
        ),
        backstory=(
            "You are a Senior Database Administrator with 15 years of experience "
            "designing, optimizing, and operating relational databases for government "
            "and healthcare systems. You are expert-level in three database platforms: "
            "PostgreSQL, Microsoft SQL Server (including Azure SQL), and MySQL. "
            "You know the strengths, limitations, and idiosyncrasies of each — you "
            "know when PostgreSQL's MVCC gives you an edge, when SQL Server's "
            "columnstore indexes are the right call, and when MySQL's replication "
            "topology fits the use case. You can read and write execution plans for "
            "all three platforms and know which query patterns perform differently "
            "across them. "
            "For PostgreSQL you know: query planning, VACUUM, autovacuum tuning, "
            "TOAST, index types (B-tree, GIN, GiST, BRIN), logical replication, "
            "pg_stat_* views, and PgBouncer connection pooling. "
            "For SQL Server / Azure SQL you know: execution plans, columnstore indexes, "
            "Always Encrypted, Transparent Data Encryption, Row-Level Security, "
            "Azure SQL tiers and DTU/vCore sizing, and SQL Server Agent jobs. "
            "For MySQL you know: InnoDB internals, query cache, replication topology, "
            "slow query log analysis, and performance_schema. "
            "You write SQL as naturally as most people write English — complex CTEs, "
            "window functions, recursive queries, and execution plan analysis are "
            "second nature to you across all three platforms. "
            "You have designed database schemas for HIPAA-compliant systems handling "
            "millions of records, and you understand that PHI data requires not just "
            "encryption but careful schema design — audit tables, surrogate keys, "
            "tokenization columns, and row-level security policies must be built into "
            "the schema from day one, not bolted on later. "
            "You review every schema that comes out of application development and "
            "you always find things to fix — missing indexes, wrong data types, "
            "nullable columns that should never be null, missing foreign key constraints, "
            "audit columns not following the standard pattern, and N+1 query traps "
            "waiting to happen in the ORM layer. "
            "You work from the Backend Implementation Report (schema), the Technical "
            "Architecture Document (data model), and the Security Review Report "
            "(PHI and compliance requirements). You own the database from the moment "
            "the Backend Developer hands off the schema until the DevOps Engineer "
            "takes over backup and DR. "
            "You produce a Database Administration Report (DBAR) that is the single "
            "source of truth for everything database-related in the project. "
            "Developers do not modify the schema without your review. Migrations do "
            "not run in production without your sign-off."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_database_administration(context: dict, bir_path: str, tad_path: str, srr_path: str) -> dict:
    """
    Reads BIR, TAD, and SRR and produces a Database Administration Report (DBAR).
    Returns updated context.
    """

    with open(bir_path) as f:
        bir_content = f.read()[:2000]

    with open(tad_path) as f:
        tad_content = f.read()[:1500]

    with open(srr_path) as f:
        srr_content = f.read()[:1000]

    dba = build_database_admin()

    dbar_task = Task(
        description=f"""
You are the Database Administrator for the following project. Review the documents
below and produce a complete Database Administration Report (DBAR).

--- Backend Implementation Report / Schema (excerpt) ---
{bir_content}

--- Technical Architecture Document (excerpt) ---
{tad_content}

--- Security Review Report (excerpt) ---
{srr_content}

Produce a complete Database Administration Report (DBAR) with ALL of the following sections:

1. SCHEMA REVIEW & CORRECTIONS
   - Review the schema from the BIR
   - Identify and fix: wrong data types, missing constraints, nullable issues,
     missing audit columns, naming inconsistencies
   - Produce the corrected final DDL (CREATE TABLE statements)
   - Document every change made and why

2. INDEX STRATEGY
   - Complete index design for all tables
   - For each index: columns, type (B-tree, GIN, partial), justification
   - Indexes for: primary lookups, filter queries, sort operations, foreign keys
   - Indexes to avoid (over-indexing warnings)
   - Index maintenance strategy (REINDEX, ANALYZE schedule)

3. QUERY OPTIMIZATION GUIDE
   - The 10 most likely slow queries for this application
   - For each: the problematic pattern, the optimized version, explanation
   - ORM anti-patterns to avoid (N+1, missing select_related, unbounded queries)
   - Query guidelines for the backend development team
   - EXPLAIN ANALYZE examples for key queries

4. PARTITIONING STRATEGY
   - Which tables benefit from partitioning and why
   - Partition key selection
   - Partition maintenance (creation, archival, dropping old partitions)
   - Impact on queries and indexes

5. PHI & AUDIT DESIGN
   - Complete audit log table design (PHI-safe)
   - Row-level security (RLS) policy definitions
   - Tokenization/surrogate key implementation in schema
   - Data masking views for non-PHI roles
   - Retention and purge procedures with SQL

6. MIGRATION STRATEGY
   - Migration naming convention and versioning
   - Safe migration patterns (zero-downtime)
   - Dangerous migration patterns to avoid
   - Rollback procedures for each migration type
   - Production migration checklist

7. CONNECTION & POOLING CONFIGURATION
   - PgBouncer or built-in pooling configuration
   - Connection limits per role/application
   - Pool sizing formula for this application
   - Connection timeout and retry settings
   - Max connections calculation for Azure SQL tier

8. PERFORMANCE MONITORING
   - Key metrics to monitor (pg_stat_*, slow query log)
   - Alert thresholds for: query time, connection count, lock waits, vacuum lag
   - Azure SQL monitoring configuration
   - Recommended monitoring queries (top slow queries, bloat, index usage)

9. BACKUP & RECOVERY PROCEDURES
   - Backup schedule and retention policy
   - Point-in-time recovery procedure (step by step)
   - Backup verification procedure
   - Geo-redundant backup configuration for Azure SQL
   - Recovery time objective (RTO) validation test

10. CAPACITY PLANNING
    - Current data volume estimates (based on project scope)
    - Growth projections (1 year, 3 years, 5 years)
    - Storage requirements
    - When to consider: partitioning, archival, read replicas, sharding
    - Azure SQL tier upgrade triggers

11. DATABASE STANDARDS
    - Naming conventions (tables, columns, indexes, constraints)
    - Required columns on every table (id, created_at, updated_at, etc.)
    - Column type standards (UUIDs vs integers, timestamp with/without timezone)
    - Constraint standards (NOT NULL defaults, check constraints)
    - Documentation requirements for schema changes

Output the complete DBAR as well-formatted markdown with working SQL code blocks.
All SQL must be PostgreSQL 15 compatible and production-ready.
PHI handling must address every relevant finding from the SRR.
""",
        expected_output="A complete Database Administration Report with working SQL in markdown format.",
        agent=dba
    )

    crew = Crew(
        agents=[dba],
        tasks=[dbar_task],
        process=Process.sequential,
        verbose=True
    )

    print(f"\n🗄️  Database Administrator reviewing schema and producing DBAR...\n")
    result = crew.kickoff()

    os.makedirs("dev/build", exist_ok=True)
    dbar_path = f"dev/build/{context['project_id']}_DBAR.md"
    with open(dbar_path, "w") as f:
        f.write(str(result))

    print(f"\n💾 Database Administration Report saved: {dbar_path}")

    context["artifacts"].append({
        "name": "Database Administration Report",
        "type": "DBAR",
        "path": dbar_path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "Database Administrator"
    })
    context["status"] = "DBA_COMPLETE"
    log_event(context, "DBA_COMPLETE", dbar_path)
    save_context(context)

    return context, dbar_path


if __name__ == "__main__":
    import glob

    logs = sorted(glob.glob("logs/PROJ-*.json"), key=os.path.getmtime, reverse=True)
    if not logs:
        print("No project context found.")
        exit(1)

    with open(logs[0]) as f:
        context = json.load(f)

    bir_path = tad_path = srr_path = None
    for artifact in context.get("artifacts", []):
        if artifact.get("type") == "BIR":
            bir_path = artifact["path"]
        if artifact.get("type") == "TAD":
            tad_path = artifact["path"]
        if artifact.get("type") == "SRR":
            srr_path = artifact["path"]

    if not all([bir_path, tad_path, srr_path]):
        print("Missing BIR, TAD, or SRR.")
        exit(1)

    print(f"📂 Loaded context: {logs[0]}")
    context, dbar_path = run_database_administration(context, bir_path, tad_path, srr_path)

    print(f"\n✅ Database administration complete.")
    print(f"📄 DBAR: {dbar_path}")
    print(f"\nFirst 500 chars:")
    with open(dbar_path) as f:
        print(f.read(500))
