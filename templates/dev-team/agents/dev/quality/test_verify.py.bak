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


def build_test_verifier() -> Agent:
    llm = LLM(
        model=os.getenv("TIER2_MODEL", "ollama/qwen2.5-coder:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    return Agent(
        role="Test Verification Engineer",
        goal=(
            "Verify that all pre-written tests from the Test Automation Report (TAR) "
            "pass against the built code. Report pass/fail per test case, coverage "
            "metrics, and any regressions."
        ),
        backstory=(
            "You are a senior QA automation engineer with 10 years of experience in "
            "test-driven development, continuous integration, and quality assurance "
            "for enterprise applications. You have worked on federal healthcare systems "
            "including VA and CMS projects with strict quality gates. "
            "\n\n"
            "Your role in the TDD pipeline is the FINAL GATE. The QA Lead and Test "
            "Automation Engineer wrote tests BEFORE the code was built. The build "
            "agents (Backend, Frontend, DBA, DevOps) then wrote code intended to pass "
            "those tests. Your job is to verify that contract was honored. "
            "\n\n"
            "You perform a systematic cross-reference:\n"
            "1. For every test case in the TAR, verify the corresponding code exists in "
            "the BIR/FIR and would satisfy the test assertion.\n"
            "2. For every API contract test, verify the endpoint exists with the correct "
            "method, path, request/response schema, and error handling.\n"
            "3. For every component test, verify the component renders and handles the "
            "specified states (loading, error, empty, populated).\n"
            "4. For every E2E scenario, verify the complete user journey is supported "
            "by the built code path.\n"
            "5. For every accessibility test, verify ARIA labels, roles, and keyboard "
            "navigation are implemented.\n"
            "\n\n"
            "Your Verification Report rates each test case as:\n"
            "- ✅ PASS — Code fully satisfies the test assertion\n"
            "- ⚠️ PARTIAL — Code exists but doesn't fully satisfy the assertion\n"
            "- ❌ FAIL — Code is missing or contradicts the test assertion\n"
            "- ⏭️ SKIP — Test cannot be verified through static analysis\n"
            "\n\n"
            "The report concludes with:\n"
            "- Overall pass rate (target: ≥95% for release)\n"
            "- Coverage analysis by category (unit, API, component, E2E, a11y)\n"
            "- Regression risk assessment\n"
            "- GO / CONDITIONAL GO / NO-GO recommendation\n"
            "\n\n"
            "OUTPUT DISCIPLINE: Write the complete report. Do not repeat sections. "
            "Do not loop. Stop after the recommendation."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_test_verification(context: dict, tar_path: str, bir_path: str,
                          fir_path: str, dir_path: str) -> tuple:
    """Run the Test Verification agent to validate built code against pre-written tests."""
    verifier = build_test_verifier()

    # Load upstream artifacts
    tar_excerpt = ""
    if tar_path and os.path.exists(tar_path):
        with open(tar_path) as f:
            tar_excerpt = f.read()[:8000]

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

    task = Task(
        description=f"""
Verify that all pre-written tests from the Test Automation Report (TAR) are
satisfied by the built code in the BIR, FIR, and DIR. This is the final TDD
gate — the tests were written BEFORE the code, and the code must pass them.

=== TEST AUTOMATION REPORT (PRE-WRITTEN TESTS) ===
{tar_excerpt}

=== BACKEND IMPLEMENTATION REPORT (BUILT CODE) ===
{bir_excerpt}

=== FRONTEND IMPLEMENTATION REPORT (BUILT CODE) ===
{fir_excerpt}

=== DEVOPS IMPLEMENTATION REPORT (CI/CD) ===
{dir_excerpt}

=== YOUR VERIFICATION REPORT MUST INCLUDE ===

1. EXECUTIVE SUMMARY
   - Total test cases analyzed
   - Pass / Partial / Fail / Skip counts
   - Overall pass rate
   - GO / CONDITIONAL GO / NO-GO recommendation

2. UNIT TEST VERIFICATION
   For each unit test in the TAR:
   | Test ID | Test Description | Target Function | Status | Evidence |
   Status: ✅ PASS / ⚠️ PARTIAL / ❌ FAIL / ⏭️ SKIP
   Evidence: The specific code that satisfies (or fails) the assertion

3. API CONTRACT TEST VERIFICATION
   For each API test in the TAR:
   | Test ID | Endpoint | Method | Expected | Actual | Status |
   Verify: route exists, method correct, request schema validated,
   response shape matches, error codes returned, auth enforced

4. COMPONENT TEST VERIFICATION
   For each component test in the TAR:
   | Test ID | Component | State Tested | Status | Evidence |
   Verify: component exists, renders expected states, handles props

5. E2E SCENARIO VERIFICATION
   For each E2E scenario in the TAR:
   | Scenario | Steps | Status | Gaps |
   Trace the complete user journey through the built code

6. ACCESSIBILITY TEST VERIFICATION
   | Test ID | Element | ARIA/A11y Requirement | Status |
   Verify: labels, roles, keyboard nav, screen reader support

7. COVERAGE ANALYSIS
   - By category: unit / API / component / E2E / accessibility
   - By module: backend / frontend / infrastructure
   - Gaps: test cases with no corresponding implementation

8. REGRESSION RISK ASSESSMENT
   - Areas where tests pass but code quality is concerning
   - Integration points that static analysis cannot fully verify
   - Recommended manual verification steps

9. RECOMMENDATION
   - GO: ≥95% pass rate, no ❌ FAIL on critical paths
   - CONDITIONAL GO: 85-94% pass rate, FAIL items have workarounds
   - NO-GO: <85% pass rate or FAIL on critical user journeys

No placeholders. No TODO comments. Every test case must be evaluated.
""",
        expected_output=(
            "A complete Verification Report with per-test-case pass/fail status, "
            "coverage analysis, regression assessment, and GO/NO-GO recommendation."
        ),
        agent=verifier
    )

    crew = Crew(
        agents=[verifier],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )

    print("\n✅ Test Verification: Validating built code against pre-written tests...\n")
    result = crew.kickoff()

    os.makedirs("/home/mfelkey/dev-team/dev/quality", exist_ok=True)
    vr_path = f"/home/mfelkey/dev-team/dev/quality/{context['project_id']}_VERIFY.md"
    with open(vr_path, "w") as f:
        f.write(str(result))

    print(f"\n💾 Verification Report saved: {vr_path}")

    context["artifacts"].append({
        "name": "Verification Report",
        "type": "VERIFY",
        "path": vr_path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "Test Verification Engineer"
    })
    log_event(context, "VERIFY_COMPLETE", vr_path)
    save_context(context)
    return context, vr_path


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

    tar_path = bir_path = fir_path = dir_path = None
    for artifact in context.get("artifacts", []):
        atype = artifact.get("type", "")
        if atype == "TAR": tar_path = artifact["path"]
        elif atype == "BIR": bir_path = artifact["path"]
        elif atype == "FIR": fir_path = artifact["path"]
        elif atype == "DIR": dir_path = artifact["path"]

    if not tar_path:
        print("Missing TAR artifact in context. Run Test Automation Engineer first.")
        exit(1)

    print(f"📂 Loaded context: {logs[0]}")
    print(f"🧪 TAR: {tar_path}")
    print(f"⚙️  BIR: {bir_path or 'NOT FOUND'}")
    print(f"🖥️  FIR: {fir_path or 'NOT FOUND'}")
    print(f"🚀 DIR: {dir_path or 'NOT FOUND'}")

    context, vr_path = run_test_verification(context, tar_path, bir_path, fir_path, dir_path)
    print(f"\n✅ Test Verification complete: {vr_path}")
    with open(vr_path) as f:
        print(f.read()[:500])
