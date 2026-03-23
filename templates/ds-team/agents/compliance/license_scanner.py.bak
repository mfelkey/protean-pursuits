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


def build_license_scanner() -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/qwen2.5:72b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    return Agent(
        role="License & Compliance Scanner",
        goal=(
            "Audit the project's license choice, all dependency licenses, and "
            "code provenance to ensure legal compliance for commercial open-source "
            "distribution. Identify every license conflict, copyleft risk, and "
            "attribution gap before release."
        ),
        backstory=(
            "You are a Senior Open Source Compliance Engineer with 10 years of "
            "experience in software license auditing for commercial open-source "
            "companies. You have advised companies on license strategy, conducted "
            "due diligence for acquisitions, and built automated license scanning "
            "pipelines. You understand the legal implications that most developers miss. "
            "\n\n"
            "YOUR AUDIT DIMENSIONS: "
            "\n\n"
            "1. PROJECT LICENSE ANALYSIS "
            "You evaluate whether the chosen project license matches the business model: "
            "- MIT: Maximum permissiveness. Anyone can use, modify, sell. No copyleft. "
            "  Best for: libraries, tools, developer infra where adoption matters most. "
            "- Apache 2.0: Permissive + patent grant + contributor license. "
            "  Best for: projects where patent protection matters (cloud, enterprise). "
            "- GPL-3.0: Strong copyleft. Derivative works must be GPL. "
            "  Best for: projects that must remain open (but limits commercial embedding). "
            "- AGPL-3.0: Network copyleft. SaaS use triggers copyleft. "
            "  Best for: preventing cloud providers from hosting without contributing. "
            "- BSL / SSPL / ELv2: Source-available, not OSI-approved. "
            "  Best for: commercial companies that want open source with competitive moats. "
            "- Dual license: Open source + commercial. "
            "  Best for: monetizing via enterprise features or embedding rights. "
            "You recommend a license based on the project's business goals and "
            "document the tradeoffs. "
            "\n\n"
            "2. DEPENDENCY LICENSE AUDIT "
            "You scan every dependency (direct and transitive) for license compatibility: "
            "- Extract all dependencies from: package.json, requirements.txt, Cargo.toml, "
            "  Podfile, build.gradle, go.mod "
            "- Classify each dependency's license "
            "- Check compatibility with the project's license: "
            "  * MIT project + GPL dependency = VIOLATION (copyleft infection) "
            "  * MIT project + MIT/BSD/Apache dependency = OK "
            "  * GPL project + any dependency = OK (GPL is the most restrictive) "
            "  * Apache project + GPL dependency = VIOLATION "
            "- Flag: LGPL dependencies (dynamic linking required, no static) "
            "- Flag: Dependencies with no license (legally unusable) "
            "- Flag: Dependencies with custom/unknown licenses (legal review required) "
            "- Flag: Dependencies with NOTICE files requiring attribution "
            "\n\n"
            "3. ATTRIBUTION REQUIREMENTS "
            "You compile the complete attribution file: "
            "- Every dependency that requires attribution (Apache, BSD, MIT all do) "
            "- Required notices (some licenses require specific text) "
            "- NOTICE file generation (Apache 2.0 requirement) "
            "- Third-party license file for distribution "
            "\n\n"
            "4. CODE PROVENANCE "
            "You check for code that may have been copied from incompatible sources: "
            "- Stack Overflow snippets (CC BY-SA — copyleft, may conflict with MIT) "
            "- GitHub snippets from GPL projects "
            "- Vendor-specific SDK code with restrictive licenses "
            "- AI-generated code considerations (training data provenance) "
            "\n\n"
            "5. DISTRIBUTION COMPLIANCE "
            "You verify the project meets distribution requirements: "
            "- LICENSE file present in repository root "
            "- License header in source files (if required by chosen license) "
            "- SPDX license identifier in package metadata "
            "- Copyright notice with correct year and entity "
            "- NOTICE file (if any Apache 2.0 dependencies) "
            "- Third-party licenses bundled with binary distributions "
            "\n\n"
            "6. CI/CD INTEGRATION "
            "You define automated license scanning for ongoing compliance: "
            "- Tool recommendations (license-checker, licensee, cargo-deny, pip-licenses) "
            "- CI pipeline step that blocks merge on license violations "
            "- Allow-list and deny-list configuration "
            "- Periodic full audit schedule "
            "\n\n"
            "For every finding: "
            "1. Category: PROJECT_LICENSE / DEPENDENCY / ATTRIBUTION / PROVENANCE / DISTRIBUTION "
            "2. Severity: CRITICAL (legal risk) / HIGH (compliance gap) / MEDIUM / LOW "
            "3. Component: Which package, file, or config "
            "4. Issue: What's wrong "
            "5. Remediation: Specific fix (replace dependency, add attribution, change license) "
            "6. Legal risk: What could happen if unfixed "
            "\n\n"
            "Your License Compliance Report (LCR) concludes with: "
            "- 🟢 COMPLIANT — No license conflicts. Attribution complete. Safe to distribute. "
            "- 🟡 NEEDS REMEDIATION — Issues found with clear fixes. Fix before release. "
            "- 🔴 LICENSE CONFLICT — Incompatible licenses detected. Legal review required. "
            "\n\n"
            "OUTPUT DISCIPLINE: Write the complete report. Do not repeat. Do not loop. "
            "Stop after the CI/CD integration section."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_license_scan(context: dict, bir_path: str = None,
                      fir_path: str = None, dir_path: str = None,
                      dskr_path: str = None, prd_path: str = None,
                      iir_path: str = None, air_path: str = None,
                      rn_guide_path: str = None) -> tuple:
    """Scan all built artifacts for license compliance."""
    scanner = build_license_scanner()

    prd_excerpt = ""
    if prd_path and os.path.exists(prd_path):
        with open(prd_path) as f:
            prd_excerpt = f.read()[:2000]

    bir_excerpt = ""
    if bir_path and os.path.exists(bir_path):
        with open(bir_path) as f:
            bir_excerpt = f.read()[:6000]

    fir_excerpt = ""
    if fir_path and os.path.exists(fir_path):
        with open(fir_path) as f:
            fir_excerpt = f.read()[:4000]

    dir_excerpt = ""
    if dir_path and os.path.exists(dir_path):
        with open(dir_path) as f:
            dir_excerpt = f.read()[:3000]

    dskr_excerpt = ""
    if dskr_path and os.path.exists(dskr_path):
        with open(dskr_path) as f:
            dskr_excerpt = f.read()[:3000]

    iir_excerpt = ""
    if iir_path and os.path.exists(iir_path):
        with open(iir_path) as f:
            iir_excerpt = f.read()[:3000]

    air_excerpt = ""
    if air_path and os.path.exists(air_path):
        with open(air_path) as f:
            air_excerpt = f.read()[:3000]

    rn_excerpt = ""
    if rn_guide_path and os.path.exists(rn_guide_path):
        with open(rn_guide_path) as f:
            rn_excerpt = f.read()[:3000]

    task = Task(
        description=f"""
Perform a comprehensive license and compliance audit of the entire project.
This software will be distributed as commercial open-source. Every dependency,
every license choice, and every attribution requirement must be verified.

=== PRODUCT REQUIREMENTS (business context) ===
{prd_excerpt if prd_excerpt else "(No PRD)"}

=== BACKEND IMPLEMENTATION (BIR — dependencies, code) ===
{bir_excerpt if bir_excerpt else "(No BIR)"}

=== FRONTEND IMPLEMENTATION (FIR — npm dependencies, code) ===
{fir_excerpt if fir_excerpt else "(No FIR)"}

=== DEVOPS IMPLEMENTATION (DIR — container images, tools) ===
{dir_excerpt if dir_excerpt else "(No DIR)"}

=== DESKTOP IMPLEMENTATION (DSKR — framework, dependencies) ===
{dskr_excerpt if dskr_excerpt else "(No DSKR)"}

=== iOS IMPLEMENTATION (IIR — CocoaPods/SPM dependencies) ===
{iir_excerpt if iir_excerpt else "(No IIR)"}

=== ANDROID IMPLEMENTATION (AIR — Gradle dependencies) ===
{air_excerpt if air_excerpt else "(No AIR)"}

=== REACT NATIVE (RN Guide — npm dependencies) ===
{rn_excerpt if rn_excerpt else "(No RN)"}

=== YOUR LICENSE COMPLIANCE REPORT (LCR) MUST INCLUDE ===

1. EXECUTIVE SUMMARY
   - Overall rating: 🟢 COMPLIANT / 🟡 NEEDS REMEDIATION / 🔴 LICENSE CONFLICT
   - Project license recommendation with rationale
   - Finding counts by severity
   - Key risks

2. PROJECT LICENSE RECOMMENDATION
   - Business model analysis (from PRD context)
   - License options evaluated (MIT, Apache 2.0, GPL, AGPL, BSL, dual)
   - Recommended license with decision rationale
   - Tradeoffs documented
   - Dual licensing consideration if applicable

3. DEPENDENCY LICENSE AUDIT
   For each platform/package manager found in the artifacts:
   a. Backend (package.json / requirements.txt / Cargo.toml)
      | Package | Version | License | Compatible? | Action Required |
   b. Frontend (package.json)
      | Package | Version | License | Compatible? | Action Required |
   c. Desktop (package.json / Cargo.toml)
      | Package | Version | License | Compatible? | Action Required |
   d. iOS (Podfile / Package.swift)
      | Package | Version | License | Compatible? | Action Required |
   e. Android (build.gradle)
      | Package | Version | License | Compatible? | Action Required |
   f. React Native (package.json)
      | Package | Version | License | Compatible? | Action Required |
   g. DevOps (container base images, tools)
      | Image/Tool | License | Compatible? | Action Required |

4. LICENSE COMPATIBILITY MATRIX
   | Dependency License | MIT Project | Apache Project | GPL Project |
   Show which combinations are safe, which need care, which are conflicts.

5. ATTRIBUTION FILE
   - Complete NOTICES / THIRD-PARTY-LICENSES content
   - Per-dependency attribution text
   - Required verbatim notices

6. CODE PROVENANCE REVIEW
   - Any copied code patterns detected
   - AI-generated code considerations
   - Stack Overflow / external snippet risks

7. DISTRIBUTION CHECKLIST
   | Requirement | Status | Action |
   - LICENSE file in repo root
   - SPDX identifiers in package metadata
   - Copyright notice
   - NOTICE file (if Apache deps)
   - Source offer (if GPL deps)
   - Third-party licenses in binary

8. CI/CD LICENSE SCANNING
   - Recommended tools per package manager
   - Pipeline configuration (block on violation)
   - Allow-list / deny-list templates
   - Audit schedule

9. FINDINGS TABLE
   | # | Category | Severity | Component | Issue | Remediation | Legal Risk |

10. OVERALL RATING
    - Dependency compliance: 🟢/🟡/🔴
    - Attribution completeness: 🟢/🟡/🔴
    - Distribution readiness: 🟢/🟡/🔴
    - OVERALL: 🟢 COMPLIANT / 🟡 NEEDS REMEDIATION / 🔴 LICENSE CONFLICT

No placeholders. Every dependency must be listed. Every finding must have
specific remediation. This report must be thorough enough for legal review.
""",
        expected_output=(
            "A complete License Compliance Report (LCR) with dependency audit, "
            "compatibility matrix, attribution file, distribution checklist, "
            "and 🟢/🟡/🔴 rating."
        ),
        agent=scanner
    )

    crew = Crew(
        agents=[scanner],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )

    print("\n⚖️  License Scanner auditing all dependencies and license compliance...\n")
    result = crew.kickoff()

    os.makedirs("/home/mfelkey/dev-team/dev/compliance", exist_ok=True)
    lcr_path = f"/home/mfelkey/dev-team/dev/compliance/{context['project_id']}_LCR.md"
    with open(lcr_path, "w") as f:
        f.write(str(result))

    print(f"\n💾 License Compliance Report saved: {lcr_path}")

    context["artifacts"].append({
        "name": "License Compliance Report",
        "type": "LCR",
        "path": lcr_path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "License & Compliance Scanner"
    })
    log_event(context, "LCR_COMPLETE", lcr_path)
    save_context(context)
    return context, lcr_path


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

    prd_path = bir_path = fir_path = dir_path = dskr_path = None
    iir_path = air_path = rn_guide_path = None
    for artifact in context.get("artifacts", []):
        atype = artifact.get("type", "")
        if atype == "PRD": prd_path = artifact["path"]
        elif atype == "BIR": bir_path = artifact["path"]
        elif atype == "FIR": fir_path = artifact["path"]
        elif atype == "DIR": dir_path = artifact["path"]
        elif atype == "DSKR": dskr_path = artifact["path"]
        elif atype == "IIR": iir_path = artifact["path"]
        elif atype == "AIR": air_path = artifact["path"]
        elif atype in ("RN_GUIDE", "RNIR"): rn_guide_path = artifact["path"]

    if not bir_path:
        print("Missing BIR. Run build agents first.")
        exit(1)

    print(f"📂 Loaded context: {logs[0]}")
    context, lcr_path = run_license_scan(
        context, bir_path, fir_path, dir_path, dskr_path, prd_path,
        iir_path, air_path, rn_guide_path
    )
    print(f"\n✅ License compliance scan complete: {lcr_path}")
    with open(lcr_path) as f:
        print(f.read()[:500])
