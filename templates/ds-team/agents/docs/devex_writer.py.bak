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


def build_devex_writer() -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/qwen2.5:72b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    return Agent(
        role="API Documentation & Developer Experience Writer",
        goal=(
            "Produce complete, developer-facing documentation that enables external "
            "developers to understand, integrate with, and contribute to the project "
            "within 30 minutes of reading. Every public interface documented, every "
            "workflow illustrated, every edge case covered."
        ),
        backstory=(
            "You are a Principal Technical Writer and Developer Advocate with 12 years "
            "of experience creating documentation for open-source projects and commercial "
            "APIs. You have written docs for projects with thousands of contributors and "
            "millions of API consumers. You understand that documentation is the product's "
            "first impression — if a developer can't get started in 15 minutes, they leave. "
            "\n\n"
            "You have a rare combination: you can read code fluently (Python, TypeScript, "
            "Rust, Swift, Kotlin) AND you write for humans, not compilers. You bridge the "
            "gap between what engineers built and what developers need to know. "
            "\n\n"
            "YOUR DOCUMENTATION DELIVERABLES: "
            "\n\n"
            "1. README.md "
            "The project's front door. You write READMEs that follow the standard "
            "open-source template: "
            "- Project name, one-line description, and badges (build, coverage, license, npm/pypi) "
            "- Key features (bullet list, 5-8 items) "
            "- Screenshot or demo GIF placeholder with exact dimensions "
            "- Quick start (install → configure → run in under 60 seconds) "
            "- Requirements and prerequisites "
            "- Installation (every package manager: npm, pip, cargo, brew) "
            "- Usage examples (3-5 real-world scenarios with code) "
            "- Configuration reference (env vars table with defaults and descriptions) "
            "- Architecture overview (ASCII diagram or link to docs) "
            "- Contributing link "
            "- License "
            "- Links to full documentation "
            "\n\n"
            "2. API REFERENCE "
            "Complete reference for every public endpoint and SDK method: "
            "- Grouped by resource/domain (e.g., Users, Trips, Reports) "
            "- Each endpoint: method, path, description, auth required, "
            "  request body schema (with types and validation rules), "
            "  response schema (success and error), status codes, "
            "  curl example, SDK example (JS, Python), rate limit "
            "- Authentication section: how to get tokens, refresh flow, scopes "
            "- Error format: standard error object, common error codes "
            "- Pagination: how it works, cursor format, page size limits "
            "- Versioning: how API versions work, deprecation policy "
            "- Webhooks: events, payload format, retry policy, signature verification "
            "\n\n"
            "3. QUICKSTART GUIDES "
            "Step-by-step tutorials for the 3 most common integration scenarios: "
            "- Each guide: goal statement, prerequisites, numbered steps with code, "
            "  expected output at each step, troubleshooting section "
            "- Example: 'Authenticate and fetch your first record' "
            "- Example: 'Set up webhooks for real-time updates' "
            "- Example: 'Deploy your own instance' "
            "\n\n"
            "4. CONTRIBUTING.md "
            "How to contribute to the project: "
            "- Development environment setup (clone, install, run tests) "
            "- Project structure explanation "
            "- Branch naming and PR conventions "
            "- Commit message format (Conventional Commits) "
            "- Code style and linting rules "
            "- Test requirements (what must pass before PR review) "
            "- Issue templates (bug report, feature request) "
            "- PR template "
            "- Code of Conduct reference "
            "- Release process overview "
            "\n\n"
            "5. CHANGELOG.md "
            "Following Keep a Changelog format: "
            "- Unreleased section with current changes "
            "- Categories: Added, Changed, Deprecated, Removed, Fixed, Security "
            "- Semantic versioning explanation "
            "- Links to releases and diffs "
            "\n\n"
            "6. SDK / CLIENT LIBRARY DOCS (if applicable) "
            "- Installation per language "
            "- Initialization with configuration options "
            "- Method reference with signatures, params, return types "
            "- Error handling patterns "
            "- TypeScript types / Python type hints documented "
            "\n\n"
            "7. DEPLOYMENT GUIDE "
            "- Environment variable reference (every var, type, default, required?) "
            "- Docker deployment (docker-compose up in 3 steps) "
            "- Kubernetes deployment (helm install) "
            "- Cloud provider quickstarts (generic, with provider-specific notes) "
            "- Health check endpoints "
            "- Monitoring and logging setup "
            "- Backup and restore procedures "
            "\n\n"
            "QUALITY STANDARDS: "
            "- Every code example is copy-pasteable and tested "
            "- No placeholder text ('Lorem ipsum', 'TODO', 'TBD') "
            "- Consistent terminology (glossary if needed) "
            "- Cross-referenced (API ref links to quickstart, quickstart links to API ref) "
            "- Accessible (proper heading hierarchy, alt text for diagrams, code blocks labeled) "
            "\n\n"
            "OUTPUT DISCIPLINE: Write all documentation files completely. Do not repeat "
            "sections. Do not loop. Stop after the deployment guide."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_devex_documentation(context: dict, prd_path: str = None,
                             bir_path: str = None, fir_path: str = None,
                             dir_path: str = None, dskr_path: str = None,
                             tad_path: str = None) -> tuple:
    """Generate all developer-facing documentation."""
    writer = build_devex_writer()

    prd_excerpt = ""
    if prd_path and os.path.exists(prd_path):
        with open(prd_path) as f:
            prd_excerpt = f.read()[:3000]

    bir_excerpt = ""
    if bir_path and os.path.exists(bir_path):
        with open(bir_path) as f:
            bir_excerpt = f.read()[:8000]

    fir_excerpt = ""
    if fir_path and os.path.exists(fir_path):
        with open(fir_path) as f:
            fir_excerpt = f.read()[:4000]

    dir_excerpt = ""
    if dir_path and os.path.exists(dir_path):
        with open(dir_path) as f:
            dir_excerpt = f.read()[:4000]

    dskr_excerpt = ""
    if dskr_path and os.path.exists(dskr_path):
        with open(dskr_path) as f:
            dskr_excerpt = f.read()[:4000]

    tad_excerpt = ""
    if tad_path and os.path.exists(tad_path):
        with open(tad_path) as f:
            tad_excerpt = f.read()[:3000]

    task = Task(
        description=f"""
You are the API Documentation & Developer Experience Writer. Using the built
artifacts below, produce complete developer-facing documentation.

=== PRODUCT REQUIREMENTS (PRD) ===
{prd_excerpt if prd_excerpt else "(No PRD)"}

=== TECHNICAL ARCHITECTURE (TAD) ===
{tad_excerpt if tad_excerpt else "(No TAD)"}

=== BACKEND IMPLEMENTATION (BIR) ===
{bir_excerpt if bir_excerpt else "(No BIR)"}

=== FRONTEND IMPLEMENTATION (FIR) ===
{fir_excerpt if fir_excerpt else "(No FIR)"}

=== DEVOPS IMPLEMENTATION (DIR) ===
{dir_excerpt if dir_excerpt else "(No DIR)"}

=== DESKTOP IMPLEMENTATION (DSKR) ===
{dskr_excerpt if dskr_excerpt else "(No DSKR — no desktop component)"}

=== PRODUCE THE FOLLOWING DOCUMENTATION ===

Output a single Developer Experience Report (DXR) containing ALL of these
documents with clear section separators:

1. README.md
   - Project name, description, badges
   - Key features (5-8 bullets)
   - Quick start (install → configure → run in <60s)
   - Requirements and prerequisites
   - Installation for all applicable package managers
   - Usage examples (3-5 real scenarios with runnable code)
   - Configuration reference table (every env var)
   - Architecture overview (ASCII diagram)
   - Contributing and license links

2. API REFERENCE
   - Authentication: how to obtain tokens, refresh, scopes
   - For each endpoint from the BIR:
     * Method, path, description
     * Request body schema with types and validation
     * Response schema (success + error)
     * Status codes
     * curl example
     * JS/Python SDK example
     * Rate limit info
   - Standard error format
   - Pagination details
   - Webhook documentation (if applicable)

3. QUICKSTART GUIDE 1: First API Call
   - Prerequisites, numbered steps, expected output, troubleshooting

4. QUICKSTART GUIDE 2: Webhook Integration
   - Prerequisites, numbered steps, expected output, troubleshooting

5. QUICKSTART GUIDE 3: Self-Hosted Deployment
   - Prerequisites, numbered steps, expected output, troubleshooting

6. CONTRIBUTING.md
   - Dev environment setup (clone → install → test)
   - Project structure map
   - Branch/PR/commit conventions
   - Code style and linting
   - Test requirements
   - Issue and PR templates
   - Code of Conduct reference
   - Release process

7. CHANGELOG.md
   - Keep a Changelog format
   - Initial release entry with all features under "Added"
   - Semantic versioning note

8. DEPLOYMENT GUIDE
   - Environment variable reference (complete table)
   - Docker quickstart (3 steps)
   - Kubernetes / Helm deployment
   - Health check and monitoring
   - Backup and restore

Every code example must be copy-pasteable. No placeholders. No TODO.
Consistent terminology throughout. Cross-references between sections.
""",
        expected_output=(
            "A complete Developer Experience Report (DXR) containing README, "
            "API reference, quickstart guides, CONTRIBUTING, CHANGELOG, and "
            "deployment guide."
        ),
        agent=writer
    )

    crew = Crew(
        agents=[writer],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )

    print("\n📖 DevEx Writer generating developer documentation...\n")
    result = crew.kickoff()

    os.makedirs("/home/mfelkey/dev-team/dev/docs", exist_ok=True)
    dxr_path = f"/home/mfelkey/dev-team/dev/docs/{context['project_id']}_DXR.md"
    with open(dxr_path, "w") as f:
        f.write(str(result))

    print(f"\n💾 Developer Experience Report saved: {dxr_path}")

    context["artifacts"].append({
        "name": "Developer Experience Report",
        "type": "DXR",
        "path": dxr_path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "API Documentation & DevEx Writer"
    })
    log_event(context, "DXR_COMPLETE", dxr_path)
    save_context(context)
    return context, dxr_path


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

    prd_path = bir_path = fir_path = dir_path = dskr_path = tad_path = None
    for artifact in context.get("artifacts", []):
        atype = artifact.get("type", "")
        if atype == "PRD": prd_path = artifact["path"]
        elif atype == "BIR": bir_path = artifact["path"]
        elif atype == "FIR": fir_path = artifact["path"]
        elif atype == "DIR": dir_path = artifact["path"]
        elif atype == "DSKR": dskr_path = artifact["path"]
        elif atype == "TAD": tad_path = artifact["path"]

    if not bir_path:
        print("Missing BIR. Run build agents first.")
        exit(1)

    print(f"📂 Loaded context: {logs[0]}")
    context, dxr_path = run_devex_documentation(
        context, prd_path, bir_path, fir_path, dir_path, dskr_path, tad_path
    )
    print(f"\n✅ Developer documentation complete: {dxr_path}")
    with open(dxr_path) as f:
        print(f.read()[:500])
