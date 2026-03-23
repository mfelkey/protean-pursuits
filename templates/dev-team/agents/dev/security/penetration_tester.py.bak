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


def build_penetration_tester() -> Agent:
    llm = LLM(
        model=os.getenv("TIER2_MODEL", "ollama/qwen2.5-coder:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    return Agent(
        role="Penetration Tester",
        goal=(
            "Perform static security analysis of all built code artifacts against "
            "the Security Review Report threat model. Identify every exploitable "
            "vulnerability with specific file:line references and severity ratings."
        ),
        backstory=(
            "You are a senior application security engineer with 12 years of "
            "experience in penetration testing, secure code review, and vulnerability "
            "assessment. You hold OSCP, CEH, and GWAPT certifications. You have "
            "performed security assessments for federal healthcare systems including "
            "VA, CMS, and DoD projects subject to FISMA, HIPAA, and FedRAMP compliance. "
            "\n\n"
            "Your approach is methodical and adversarial. You think like an attacker. "
            "You take the Security Review Report (SRR) as your threat model and "
            "systematically verify whether each identified risk was properly mitigated "
            "in the built code. You also hunt for vulnerabilities the SRR may have missed. "
            "\n\n"
            "Your analysis covers the OWASP Top 10 and beyond:\n"
            "- SQL Injection / NoSQL Injection — parameterized queries, ORM usage\n"
            "- Cross-Site Scripting (XSS) — output encoding, CSP headers, DOM sanitization\n"
            "- Authentication bypass — session management, token validation, password policy\n"
            "- Insecure Direct Object References (IDOR) — authorization checks on every endpoint\n"
            "- Server-Side Request Forgery (SSRF) — URL validation, allowlists\n"
            "- Secrets in code — API keys, passwords, tokens in source files or configs\n"
            "- Misconfigured CORS — overly permissive origins, credentials exposure\n"
            "- Open debug endpoints — dev routes, stack traces, verbose error responses\n"
            "- Insecure deserialization — untrusted input to deserializers\n"
            "- Missing rate limiting — brute force, credential stuffing, API abuse\n"
            "- Security header gaps — HSTS, X-Frame-Options, X-Content-Type-Options\n"
            "- Dependency vulnerabilities — known CVEs in declared packages\n"
            "- Logging sensitive data — PII/PHI in log output, request logging\n"
            "\n\n"
            "For every finding you provide:\n"
            "1. Severity: CRITICAL / HIGH / MEDIUM / LOW / INFO\n"
            "2. Category: OWASP classification\n"
            "3. Location: Exact file path and line number (or function name)\n"
            "4. Evidence: The specific code pattern that is vulnerable\n"
            "5. Impact: What an attacker could achieve\n"
            "6. Remediation: Specific fix with code example\n"
            "\n\n"
            "Your Penetration Test Report (PTR) concludes with an overall rating:\n"
            "- 🟢 PASS — No CRITICAL or HIGH findings. Ready for release.\n"
            "- 🟡 CONDITIONAL — HIGH findings exist but have documented mitigations "
            "or accepted risk. Release with conditions.\n"
            "- 🔴 FAIL — CRITICAL findings exist. Release blocked until resolved.\n"
            "\n\n"
            "OUTPUT DISCIPLINE: Write the complete report. Do not repeat sections. "
            "Do not loop. Stop after the overall rating and remediation summary."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_penetration_test(context: dict, srr_path: str, bir_path: str,
                         fir_path: str, dir_path: str, dbar_path: str = None) -> tuple:
    """Run the Penetration Tester agent against built code artifacts."""
    tester = build_penetration_tester()

    # Load upstream artifacts
    srr_excerpt = ""
    if srr_path and os.path.exists(srr_path):
        with open(srr_path) as f:
            srr_excerpt = f.read()[:6000]

    bir_excerpt = ""
    if bir_path and os.path.exists(bir_path):
        with open(bir_path) as f:
            bir_excerpt = f.read()[:8000]

    fir_excerpt = ""
    if fir_path and os.path.exists(fir_path):
        with open(fir_path) as f:
            fir_excerpt = f.read()[:8000]

    dir_excerpt = ""
    if dir_path and os.path.exists(dir_path):
        with open(dir_path) as f:
            dir_excerpt = f.read()[:5000]

    dbar_excerpt = ""
    if dbar_path and os.path.exists(dbar_path):
        with open(dbar_path) as f:
            dbar_excerpt = f.read()[:4000]

    task = Task(
        description=f"""
Perform a comprehensive penetration test / static security analysis of the
built application code. Use the Security Review Report (SRR) as your threat
model and verify every risk was properly mitigated.

=== SECURITY REVIEW REPORT (THREAT MODEL) ===
{srr_excerpt}

=== BACKEND IMPLEMENTATION REPORT (BIR) ===
{bir_excerpt}

=== FRONTEND IMPLEMENTATION REPORT (FIR) ===
{fir_excerpt}

=== DEVOPS IMPLEMENTATION REPORT (DIR) ===
{dir_excerpt}

{f'=== DATABASE ADMINISTRATION REPORT (DBAR) ==={chr(10)}{dbar_excerpt}' if dbar_excerpt else ''}

=== YOUR PENETRATION TEST REPORT MUST INCLUDE ===

1. EXECUTIVE SUMMARY
   - Scope of analysis
   - Overall rating: 🟢 PASS / 🟡 CONDITIONAL / 🔴 FAIL
   - Finding counts by severity

2. SRR THREAT MODEL VERIFICATION
   - For each risk identified in the SRR, verify if it was mitigated
   - Status: MITIGATED / PARTIALLY MITIGATED / NOT MITIGATED

3. OWASP TOP 10 ANALYSIS
   - Systematic check of each OWASP category against the code
   - Findings with file:line references, evidence, impact, remediation

4. AUTHENTICATION & AUTHORIZATION
   - Session management review
   - Token validation patterns
   - Role-based access control enforcement
   - Password/credential handling

5. DATA PROTECTION
   - PII/PHI handling (especially for VA healthcare data)
   - Encryption at rest and in transit
   - Secrets management (no hardcoded credentials)
   - Logging sanitization (no sensitive data in logs)

6. INFRASTRUCTURE SECURITY
   - Container configuration (Docker hardening)
   - CI/CD pipeline security (secrets injection, artifact signing)
   - Network exposure (ports, CORS, security headers)
   - Dependency vulnerability scan (known CVEs)

7. FINDINGS TABLE
   | # | Severity | Category | Location | Description | Remediation |
   For every finding, one row with specific details.

8. OVERALL RATING & REMEDIATION ROADMAP
   - Final rating with justification
   - Prioritized remediation order
   - Estimated effort per finding

No placeholders. No TODO comments. Every finding must have a specific
file:line reference and concrete remediation code example.
""",
        expected_output=(
            "A complete Penetration Test Report (PTR) with executive summary, "
            "SRR verification matrix, OWASP Top 10 analysis, findings table "
            "with file:line references, and overall 🟢/🟡/🔴 rating."
        ),
        agent=tester
    )

    crew = Crew(
        agents=[tester],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )

    print("\n🔓 Penetration Tester analyzing built code for vulnerabilities...\n")
    result = crew.kickoff()

    os.makedirs("/home/mfelkey/dev-team/dev/security", exist_ok=True)
    ptr_path = f"/home/mfelkey/dev-team/dev/security/{context['project_id']}_PTR.md"
    with open(ptr_path, "w") as f:
        f.write(str(result))

    print(f"\n💾 Penetration Test Report saved: {ptr_path}")

    context["artifacts"].append({
        "name": "Penetration Test Report",
        "type": "PTR",
        "path": ptr_path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "Penetration Tester"
    })
    log_event(context, "PTR_COMPLETE", ptr_path)
    save_context(context)
    return context, ptr_path


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

    # Find upstream artifacts
    srr_path = bir_path = fir_path = dir_path = dbar_path = None
    for artifact in context.get("artifacts", []):
        atype = artifact.get("type", "")
        if atype == "SRR": srr_path = artifact["path"]
        elif atype == "BIR": bir_path = artifact["path"]
        elif atype == "FIR": fir_path = artifact["path"]
        elif atype == "DIR": dir_path = artifact["path"]
        elif atype == "DBAR": dbar_path = artifact["path"]

    if not bir_path:
        print("Missing BIR artifact in context. Run build agents first.")
        exit(1)

    if not srr_path:
        print("⚠️  No SRR found — running without threat model baseline.")

    print(f"📂 Loaded context: {logs[0]}")
    print(f"🔒 SRR: {srr_path or 'NOT FOUND'}")
    print(f"⚙️  BIR: {bir_path}")
    print(f"🖥️  FIR: {fir_path or 'NOT FOUND'}")
    print(f"🚀 DIR: {dir_path or 'NOT FOUND'}")

    context, ptr_path = run_penetration_test(
        context, srr_path, bir_path, fir_path, dir_path, dbar_path
    )
    print(f"\n✅ Penetration Test complete: {ptr_path}")
    with open(ptr_path) as f:
        print(f.read()[:500])
