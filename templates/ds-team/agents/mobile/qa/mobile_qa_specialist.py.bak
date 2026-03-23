import sys
sys.path.insert(0, "/home/mfelkey/dev-team")

import os
import re
import json
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from agents.orchestrator.orchestrator import log_event, save_context

load_dotenv("config/.env")


# ---------------------------------------------------------------------------
# Agent Builder
# ---------------------------------------------------------------------------

def build_mobile_qa_specialist() -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/gpt-oss:120b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    return Agent(
        role="Mobile QA Specialist",
        goal=(
            "Own the complete mobile quality assurance strategy — define the "
            "mobile test plan, write executable automated tests (unit, component, "
            "and E2E), and be the final gate before any build reaches the App "
            "Store or Google Play."
        ),
        backstory=(
            "You are a Senior Mobile QA Specialist with 12 years of experience in "
            "mobile application quality assurance for healthcare and government "
            "systems. You have led mobile QA programs for HIPAA-regulated apps, "
            "Section 508-accessible mobile interfaces, and apps that must pass "
            "rigorous App Store and Google Play review processes. "
            "You think about mobile quality at every level — unit, component, "
            "integration, E2E, performance, security, accessibility, and device "
            "compatibility. You know that mobile testing has unique dimensions that "
            "web testing does not — gesture handling, offline behavior, push "
            "notifications, background/foreground lifecycle, deep linking, OTA "
            "update integrity, and platform-specific rendering differences. "
            "You have deep experience with both manual device testing and automated "
            "mobile testing. You are fluent in Jest, React Native Testing Library, "
            "Detox for E2E, Appium for cross-platform automation, and Maestro for "
            "mobile UI flows. You know when to automate and when hands-on device "
            "testing is irreplaceable. "
            "You don't just write test plans — you write real, executable test code. "
            "Every test file you produce is syntactically correct, imports the right "
            "libraries, and can run with `npx jest` or `npx detox test` inside the "
            "React Native project. "
            "You review every artifact the mobile team produces — the RN Developer "
            "guide, the Mobile DevOps Implementation Report, the UX designs — and "
            "you find the gaps, ambiguities, and untestable requirements before they "
            "become production defects or store rejections. "
            "You are the voice of the mobile end user in the development process. "
            "Nothing ships to the stores without your sign-off."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


# ---------------------------------------------------------------------------
# Test File Extraction
# ---------------------------------------------------------------------------

def extract_test_files(output: str, output_dir: str) -> list:
    """
    Parse the agent output for fenced code blocks that contain file path
    comments (e.g. // src/__tests__/HomeScreen.test.tsx) and write each
    to disk under output_dir.

    Returns list of dicts: [{"path": ..., "relative_path": ..., "chars": ...}]
    """
    # Match code blocks with a file path comment on the first line
    pattern = re.compile(
        r"```(?:tsx?|js|jsx)\s*\n"
        r"(?://|#)\s*((?:src|e2e|__tests__)/\S+\.(?:tsx?|js|jsx))\s*\n"
        r"(.*?)"
        r"```",
        re.DOTALL
    )

    written = []
    for match in pattern.finditer(output):
        rel_path = match.group(1).strip()
        code = match.group(2)

        full_path = os.path.join(output_dir, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(code)

        written.append({
            "path": full_path,
            "relative_path": rel_path,
            "chars": len(code),
        })

    return written


# ---------------------------------------------------------------------------
# Task 1: Mobile Master Test Plan (MMTP)
# ---------------------------------------------------------------------------

MMTP_TASK_TEMPLATE = """
You are the Mobile QA Specialist for the following project. Review the documents
below and produce a complete Mobile Master Test Plan (MMTP).

--- PRD (excerpt) ---
{prd_content}

--- Technical Implementation Plan (excerpt) ---
{tip_content}

--- React Native Implementation Guide (excerpt) ---
{rn_content}

--- Mobile DevOps Implementation Report (excerpt) ---
{mdir_content}

--- User Experience Document (excerpt) ---
{uxd_content}

Produce a complete Mobile Master Test Plan (MMTP) with ALL of the following sections:

1. MOBILE TEST STRATEGY OVERVIEW
   - Testing philosophy and approach for React Native (Expo)
   - Test levels: unit, component, integration, E2E, performance, security,
     accessibility, device compatibility
   - Testing tools and frameworks for each level:
     * Unit/Component: Jest + React Native Testing Library
     * E2E: Detox (iOS/Android) and/or Maestro
     * Performance: Flashlight, React Native Performance Monitor
     * Accessibility: axe-react-native, manual VoiceOver/TalkBack
     * API: Jest + MSW (Mock Service Worker)
   - Entry and exit criteria for each test level
   - Risk-based testing approach for mobile-specific risks

2. DEVICE & OS COMPATIBILITY MATRIX
   - Minimum supported iOS and Android versions
   - Target device matrix (phones and tablets)
   - Screen size and density breakpoints to test
   - OS-specific behavior differences to verify
   - Emulator/simulator vs physical device testing requirements

3. TEST ENVIRONMENT REQUIREMENTS
   - Environment specifications (dev, staging, production-mirror)
   - Test data requirements (PHI-safe synthetic data for mobile)
   - Mock API setup with MSW for offline/isolated testing
   - EAS Build profiles for test builds (dev client, preview)
   - Environment setup and teardown procedures

4. TEST CASES — FUNCTIONAL (MOBILE-SPECIFIC)
   - Complete test cases for every major screen and flow:
     * Authentication: login, registration, biometric unlock, session timeout
     * Home screen: trip list, pull-to-refresh, infinite scroll, empty state
     * Trip detail: route params, data loading, action buttons, error state
     * Create trip: multi-step form wizard, step validation, back navigation
     * Search: debounced input, filter chips, results rendering
     * Profile: settings toggles, logout, dark mode switch
     * Navigation: tab switching, deep linking, back button behavior (Android)
   - Format: Test ID | Description | Preconditions | Steps | Expected Result | Priority

5. TEST CASES — MOBILE GESTURES & INTERACTIONS
   - Pull-to-refresh, swipe, long press, keyboard handling
   - Orientation changes, safe area rendering
   - Touch target minimum sizes (44pt iOS, 48dp Android)

6. TEST CASES — OFFLINE & NETWORK CONDITIONS
   - No connectivity, slow network (3G), network transitions
   - Offline queue, optimistic UI, sync on reconnect
   - Cached data display, error messaging

7. TEST CASES — APP LIFECYCLE & BACKGROUNDING
   - Cold start, warm start, resume from background
   - Memory pressure, push notification deep linking
   - OTA update detection and apply, force update prompt
   - Form data preservation on app kill

8. TEST CASES — ACCESSIBILITY (Section 508 / WCAG 2.1 AA)
   - VoiceOver (iOS) and TalkBack (Android) per screen
   - Focus management, dynamic type scaling (up to 200%)
   - Color contrast, ARIA labels, form error announcements
   - Reduced motion support

9. TEST CASES — PERFORMANCE
   - Cold start time (< 2s), screen transitions (< 300ms)
   - FlatList scroll 60fps with 1000+ items
   - Memory usage per screen, API response render time
   - Bundle size thresholds

10. TEST CASES — SECURITY (MOBILE-SPECIFIC)
    - Secure storage (Keychain/Keystore), certificate pinning
    - Jailbreak/root detection, screen capture prevention
    - Network traffic inspection (no PHI in plain text)
    - Debug mode disabled in production builds

11. DEFECT MANAGEMENT PROCESS
    - Severity definitions with mobile-specific criteria
    - Defect lifecycle, report template, resolution SLAs
    - Regression testing requirements after fixes

12. RELEASE CRITERIA & SIGN-OFF
    - Ready for TestFlight / Internal Track criteria
    - Ready for Production Store Submission criteria
    - Device matrix minimum coverage, sign-off matrix
    - App Store / Google Play review risk assessment

Output the complete MMTP as well-formatted markdown.
Every test case must have actual steps — no vague descriptions.
"""


# ---------------------------------------------------------------------------
# Task 2: Executable Automated Test Files
# ---------------------------------------------------------------------------

TEST_CODE_TASK_TEMPLATE = """
You are the Mobile QA Specialist. You have just written the Mobile Master Test
Plan. Now write the actual executable test code.

Using the React Native Implementation Guide below as reference for component
structure, imports, hooks, and file paths, produce complete, runnable test files.

--- React Native Implementation Guide (excerpt) ---
{rn_content}

Generate the following test files. Each file must:
- Be a complete, syntactically valid TypeScript/TSX file
- Start with a comment showing its file path (e.g. // src/__tests__/HomeScreen.test.tsx)
- Import from the correct locations based on the RN guide
- Use Jest + React Native Testing Library for unit/component tests
- Use Detox for E2E tests
- Include descriptive test names and meaningful assertions
- Cover happy path, error states, and edge cases

REQUIRED TEST FILES:

1. // src/__tests__/components/Button.test.tsx
   - Renders with title
   - Calls onPress when pressed
   - Renders primary and secondary variants
   - Respects disabled state
   - Has correct accessibility label

2. // src/__tests__/components/Card.test.tsx
   - Renders title and children
   - Applies correct styles

3. // src/__tests__/components/FormField.test.tsx
   - Renders label and input
   - Displays error message when error prop set
   - Calls onChangeText
   - Sets accessibility props correctly (accessibilityLabel, accessibilityInvalid)

4. // src/__tests__/screens/HomeScreen.test.tsx
   - Renders loading state
   - Renders trip list when data loaded (mock useTrips)
   - Renders error state
   - Pull-to-refresh calls refetch
   - Navigate to TripDetail on card press
   - Navigate to CreateTrip on button press

5. // src/__tests__/screens/LoginScreen.test.tsx
   - Renders email and password fields
   - Shows validation errors for empty submit
   - Shows validation error for invalid email
   - Shows validation error for short password
   - Calls login handler with valid data

6. // src/__tests__/screens/CreateTripScreen.test.tsx
   - Renders step 1 initially
   - Navigates to step 2 on Next press
   - Navigates back to step 1 on Back press
   - Renders step 3 (review) with Submit button
   - Calls submit handler on final step

7. // src/__tests__/hooks/useTrips.test.ts
   - Returns loading state initially
   - Returns trip data after fetch
   - Handles fetch error

8. // src/__tests__/store/authStore.test.ts
   - Initial state has null token and user
   - login() sets token and user
   - logout() clears token and user
   - setError() sets error message

9. // src/__tests__/store/tripStore.test.ts
   - Initial state has empty trips array
   - addTrip() appends to trips
   - fetchTrips() sets loading then resolves

10. // e2e/login.e2e.ts (Detox)
    - Shows login screen on launch
    - Login with valid credentials navigates to Home
    - Login with invalid credentials shows error
    - Tapping register navigates to registration

11. // e2e/createTrip.e2e.ts (Detox)
    - Full create trip wizard flow: fill step 1 → step 2 → step 3 → submit
    - New trip appears in home list after creation
    - Back button returns to previous step

12. // src/__tests__/setup/testUtils.tsx
    - Reusable render wrapper with providers (QueryClientProvider, NavigationContainer)
    - Mock navigation helpers
    - Mock MSW server setup

Output each file as a fenced code block with the file path comment on line 1.
Every test must be complete — no placeholder comments like "// add tests here".
"""


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_mobile_qa(context: dict, prd_path: str, tip_path: str,
                  rn_guide_path: str, mdir_path: str, uxd_path: str) -> dict:
    """
    Two-phase execution:
      Phase 1: Generate the Mobile Master Test Plan (MMTP) document
      Phase 2: Generate executable automated test files

    Returns updated context with both artifacts registered.
    """

    with open(prd_path) as f:
        prd_content = f.read()[:1500]

    with open(tip_path) as f:
        tip_content = f.read()[:1000]

    with open(rn_guide_path) as f:
        rn_content = f.read()[:3000]

    with open(mdir_path) as f:
        mdir_content = f.read()[:1500]

    with open(uxd_path) as f:
        uxd_content = f.read()[:1000]

    mqa = build_mobile_qa_specialist()

    # ------------------------------------------------------------------
    # Phase 1: MMTP
    # ------------------------------------------------------------------

    mmtp_task = Task(
        description=MMTP_TASK_TEMPLATE.format(
            prd_content=prd_content,
            tip_content=tip_content,
            rn_content=rn_content,
            mdir_content=mdir_content,
            uxd_content=uxd_content,
        ),
        expected_output="A complete Mobile Master Test Plan in markdown format.",
        agent=mqa,
    )

    # ------------------------------------------------------------------
    # Phase 2: Executable Test Files
    # ------------------------------------------------------------------

    test_code_task = Task(
        description=TEST_CODE_TASK_TEMPLATE.format(
            rn_content=rn_content,
        ),
        expected_output=(
            "Complete, runnable test files for Jest + RNTL (unit/component), "
            "Zustand stores, custom hooks, and Detox E2E specs, plus a shared "
            "test utilities file."
        ),
        agent=mqa,
    )

    crew = Crew(
        agents=[mqa],
        tasks=[mmtp_task, test_code_task],
        process=Process.sequential,
        verbose=True,
    )

    print(f"\n🧪 Mobile QA Specialist: Phase 1 (MMTP) + Phase 2 (Test Code)...\n")
    result = crew.kickoff()

    # ------------------------------------------------------------------
    # Save MMTP
    # ------------------------------------------------------------------

    os.makedirs("dev/quality", exist_ok=True)

    # task_output for the first task contains the MMTP
    mmtp_output = str(crew.tasks[0].output) if crew.tasks[0].output else ""
    mmtp_path = f"dev/quality/{context['project_id']}_MMTP.md"
    with open(mmtp_path, "w") as f:
        f.write(mmtp_output)
    print(f"\n💾 Mobile Master Test Plan saved: {mmtp_path}")

    context["artifacts"].append({
        "name": "Mobile Master Test Plan",
        "type": "MMTP",
        "path": mmtp_path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "Mobile QA Specialist"
    })

    # ------------------------------------------------------------------
    # Save Test Files
    # ------------------------------------------------------------------

    test_output = str(crew.tasks[1].output) if crew.tasks[1].output else str(result)
    test_dir = f"dev/quality/{context['project_id']}_mobile_tests"
    os.makedirs(test_dir, exist_ok=True)

    # Save raw output as reference
    raw_path = os.path.join(test_dir, "GENERATED_TESTS_RAW.md")
    with open(raw_path, "w") as f:
        f.write(test_output)

    # Extract individual test files from code blocks
    written_files = extract_test_files(test_output, test_dir)

    if written_files:
        print(f"\n💾 Extracted {len(written_files)} test files to {test_dir}/")
        for tf in written_files:
            print(f"   ✅ {tf['relative_path']} ({tf['chars']} chars)")
    else:
        print(f"\n⚠️  No test files extracted (check raw output: {raw_path})")

    context["artifacts"].append({
        "name": "Mobile Automated Tests",
        "type": "MOBILE_TESTS",
        "path": test_dir,
        "test_files": [tf["relative_path"] for tf in written_files],
        "test_count": len(written_files),
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "Mobile QA Specialist"
    })

    context["status"] = "MOBILE_QA_COMPLETE"
    log_event(context, "MOBILE_QA_COMPLETE", mmtp_path)
    save_context(context)

    return context, mmtp_path, test_dir


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import glob

    logs = sorted(glob.glob("logs/PROJ-*.json"), key=os.path.getmtime, reverse=True)
    if not logs:
        print("No project context found.")
        exit(1)

    with open(logs[0]) as f:
        context = json.load(f)

    prd_path = tip_path = rn_guide_path = mdir_path = uxd_path = None
    for artifact in context.get("artifacts", []):
        if artifact.get("type") == "PRD":
            prd_path = artifact["path"]
        if artifact.get("type") == "TIP":
            tip_path = artifact["path"]
        if artifact.get("type") in ("RN_GUIDE", "RN_COMBINED"):
            rn_guide_path = artifact["path"]
        if artifact.get("type") == "MDIR":
            mdir_path = artifact["path"]
        if artifact.get("type") == "UXD":
            uxd_path = artifact["path"]

    if not all([prd_path, tip_path, rn_guide_path, mdir_path, uxd_path]):
        missing = []
        if not prd_path: missing.append("PRD")
        if not tip_path: missing.append("TIP")
        if not rn_guide_path: missing.append("RN_GUIDE / RN_COMBINED")
        if not mdir_path: missing.append("MDIR")
        if not uxd_path: missing.append("UXD")
        print(f"Missing upstream artifacts: {', '.join(missing)}")
        exit(1)

    print(f"📂 Loaded context: {logs[0]}")
    context, mmtp_path, test_dir = run_mobile_qa(
        context, prd_path, tip_path, rn_guide_path, mdir_path, uxd_path
    )

    print(f"\n✅ Mobile QA complete.")
    print(f"📄 MMTP: {mmtp_path}")
    print(f"📁 Tests: {test_dir}")
    print(f"\nFirst 500 chars of MMTP:")
    with open(mmtp_path) as f:
        print(f.read(500))
