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


def build_mobile_test_verifier() -> Agent:
    llm = LLM(
        model=os.getenv("TIER2_MODEL", "ollama/qwen2.5-coder:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    return Agent(
        role="Mobile Test Verification Engineer",
        goal=(
            "Verify that all pre-written mobile tests from the Mobile Test Plan "
            "pass against the built iOS, Android, and React Native code. Report "
            "pass/fail per test case per platform."
        ),
        backstory=(
            "You are a senior mobile QA engineer with 10 years of experience in "
            "iOS (XCTest, XCUITest), Android (JUnit5, Espresso), and React Native "
            "(Jest, React Native Testing Library, Detox) test automation. You have "
            "worked on federal healthcare mobile apps handling PHI under HIPAA. "
            "\n\n"
            "Your role is the FINAL MOBILE TDD GATE. The Mobile QA Specialist wrote "
            "tests BEFORE the mobile code was built. iOS, Android, and RN developers "
            "then wrote code intended to pass those tests. You verify the contract. "
            "\n\n"
            "You cross-reference every test case against the built artifacts:\n"
            "- Jest unit tests → RN component/service implementations\n"
            "- RNTL component tests → RN screen/component code\n"
            "- Detox E2E scenarios → Complete mobile user journeys\n"
            "- XCTest cases → Swift/SwiftUI implementations\n"
            "- JUnit5/Espresso tests → Kotlin/Compose implementations\n"
            "- Accessibility tests → VoiceOver/TalkBack compliance\n"
            "\n\n"
            "Each test is rated per platform:\n"
            "- ✅ PASS — Code fully satisfies the test assertion\n"
            "- ⚠️ PARTIAL — Code exists but doesn't fully satisfy\n"
            "- ❌ FAIL — Code missing or contradicts the test\n"
            "- ⏭️ SKIP — Cannot verify through static analysis\n"
            "- N/A — Test not applicable to this platform\n"
            "\n\n"
            "Your report concludes with per-platform GO/NO-GO and an overall "
            "mobile release recommendation.\n"
            "\n\n"
            "OUTPUT DISCIPLINE: Write the complete report. Do not repeat sections. "
            "Do not loop. Stop after the recommendation."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_mobile_test_verification(context: dict, test_plan_path: str,
                                  iir_path: str, air_path: str,
                                  rn_guide_path: str, mdir_path: str) -> tuple:
    """Run Mobile Test Verification against all mobile artifacts."""
    verifier = build_mobile_test_verifier()

    # Load upstream artifacts
    test_plan_excerpt = ""
    if test_plan_path and os.path.exists(test_plan_path):
        with open(test_plan_path) as f:
            test_plan_excerpt = f.read()[:8000]

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
Verify that all pre-written mobile tests are satisfied by the built mobile code.
This is the final mobile TDD gate. Tests were written BEFORE code.

=== MOBILE TEST PLAN (PRE-WRITTEN TESTS) ===
{test_plan_excerpt}

=== iOS IMPLEMENTATION REPORT (BUILT CODE) ===
{iir_excerpt}

=== ANDROID IMPLEMENTATION REPORT (BUILT CODE) ===
{air_excerpt}

=== REACT NATIVE GUIDE (BUILT CODE) ===
{rn_excerpt}

=== MOBILE DEVOPS REPORT (CI/CD) ===
{mdir_excerpt}

=== YOUR MOBILE VERIFICATION REPORT MUST INCLUDE ===

1. EXECUTIVE SUMMARY
   - Total test cases by platform
   - Pass / Partial / Fail / Skip counts per platform
   - Per-platform pass rate
   - Overall mobile GO / CONDITIONAL GO / NO-GO

2. REACT NATIVE TEST VERIFICATION
   a. Jest Unit Tests:
      | Test ID | Description | Target | Status | Evidence |
   b. RNTL Component Tests:
      | Test ID | Component | States Tested | Status | Evidence |
   c. Detox E2E Scenarios:
      | Scenario | Steps | Status | Gaps |

3. iOS TEST VERIFICATION (XCTest / XCUITest)
   | Test ID | Description | Target Class | Status | Evidence |
   Verify: Swift/SwiftUI implementations satisfy test assertions
   Special focus: VoiceOver a11y, Keychain, biometric auth

4. ANDROID TEST VERIFICATION (JUnit5 / Espresso)
   | Test ID | Description | Target Class | Status | Evidence |
   Verify: Kotlin/Compose implementations satisfy test assertions
   Special focus: TalkBack a11y, EncryptedSharedPreferences, FLAG_SECURE

5. ACCESSIBILITY VERIFICATION (Cross-Platform)
   | Test ID | Platform | Element | Requirement | Status |
   Verify: VoiceOver labels, TalkBack descriptions, RNTL a11y props

6. COVERAGE ANALYSIS
   - By platform: iOS / Android / React Native
   - By category: unit / component / E2E / accessibility
   - Gaps: tests with no corresponding implementation

7. CI/CD INTEGRATION CHECK
   - Mobile test suite integrated in CI pipeline?
   - Tests gated on build/deploy?
   - Platform-specific test runs configured?

8. PER-PLATFORM RECOMMENDATION
   - iOS: GO / CONDITIONAL GO / NO-GO (with pass rate)
   - Android: GO / CONDITIONAL GO / NO-GO (with pass rate)
   - React Native: GO / CONDITIONAL GO / NO-GO (with pass rate)
   - Overall Mobile: GO / CONDITIONAL GO / NO-GO

No placeholders. No TODO comments. Every test case must be evaluated.
""",
        expected_output=(
            "A complete Mobile Verification Report with per-platform, per-test-case "
            "pass/fail status, coverage analysis, and GO/NO-GO recommendations."
        ),
        agent=verifier
    )

    crew = Crew(
        agents=[verifier],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )

    print("\n✅ Mobile Test Verification: Validating mobile code against pre-written tests...\n")
    result = crew.kickoff()

    os.makedirs("/home/mfelkey/dev-team/dev/mobile/quality", exist_ok=True)
    mvr_path = f"/home/mfelkey/dev-team/dev/mobile/quality/{context['project_id']}_MOBILE_VERIFY.md"
    with open(mvr_path, "w") as f:
        f.write(str(result))

    print(f"\n💾 Mobile Verification Report saved: {mvr_path}")

    context["artifacts"].append({
        "name": "Mobile Verification Report",
        "type": "MOBILE_VERIFY",
        "path": mvr_path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "Mobile Test Verification Engineer"
    })
    log_event(context, "MOBILE_VERIFY_COMPLETE", mvr_path)
    save_context(context)
    return context, mvr_path


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

    test_plan_path = iir_path = air_path = rn_guide_path = mdir_path = None
    for artifact in context.get("artifacts", []):
        atype = artifact.get("type", "")
        if atype == "MOBILE_TEST_PLAN": test_plan_path = artifact["path"]
        elif atype == "IIR": iir_path = artifact["path"]
        elif atype == "AIR": air_path = artifact["path"]
        elif atype in ("RN_GUIDE", "RNIR"): rn_guide_path = artifact["path"]
        elif atype == "MDIR": mdir_path = artifact["path"]

    if not test_plan_path:
        print("Missing Mobile Test Plan. Run Mobile QA Specialist first.")
        exit(1)

    print(f"📂 Loaded context: {logs[0]}")
    print(f"🧪 Test Plan: {test_plan_path}")
    print(f"🍎 IIR: {iir_path or 'NOT FOUND'}")
    print(f"🤖 AIR: {air_path or 'NOT FOUND'}")
    print(f"⚛️  RN:  {rn_guide_path or 'NOT FOUND'}")
    print(f"📦 MDIR: {mdir_path or 'NOT FOUND'}")

    context, mvr_path = run_mobile_test_verification(
        context, test_plan_path, iir_path, air_path, rn_guide_path, mdir_path
    )
    print(f"\n✅ Mobile Test Verification complete: {mvr_path}")
    with open(mvr_path) as f:
        print(f.read()[:500])
