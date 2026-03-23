import sys
sys.path.insert(0, "/home/mfelkey/dev-team")

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from agents.orchestrator.orchestrator import log_event, save_context

load_dotenv("config/.env")


def build_ios_developer() -> Agent:
    llm = LLM(
        model=os.getenv("TIER2_MODEL", "ollama/qwen2.5-coder:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    return Agent(
        role="iOS Developer",
        goal=(
            "Produce the missing sections of an iOS Implementation Report — "
            "specifically the PHI security controls, VoiceOver accessibility "
            "implementation, XCTest/XCUITest test suite, and Fastlane "
            "build/distribution configuration. All output must be working "
            "Swift code, no placeholders."
        ),
        backstory=(
            "You are a Senior iOS Engineer with 12 years of experience building "
            "native iOS applications for government and healthcare clients. "
            "You specialize in three areas: HIPAA-compliant PHI security controls "
            "on iOS, VoiceOver accessibility implementation, and Fastlane CI/CD. "
            "You write production-ready Swift code. You never write placeholder "
            "comments like '// implement logic here'. Every function you write "
            "is complete and correct."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_ios_patch(context: dict, iir_path: str) -> tuple:

    with open(iir_path) as f:
        iir_content = f.read()[:3000]

    ios_dev = build_ios_developer()

    patch_task = Task(
        description=f"""
You are patching an iOS Implementation Report that is missing critical sections.
The existing IIR is shown below for context.

--- Existing IIR (excerpt) ---
{iir_content}

Produce ONLY the following missing sections with complete, working Swift code.
No summaries. No bullet points. No placeholders. Working code only.

---

## 7-PATCH. PHI & SECURITY IMPLEMENTATION (COMPLETE)

### App Switcher Blur
Complete implementation using SceneDelegate:
- applicationWillResignActive: add blur overlay to window
- applicationDidBecomeActive: remove blur overlay
- Use UIBlurEffect with UIVisualEffectView covering the key window
- Include the complete SceneDelegate methods

### Screenshot Prevention
- SplashView and all non-PHI screens: no restriction
- TripDetailView: implement via UITextField secureTextEntry trick on a hidden field
  added to the window in viewDidAppear equivalent (use .onAppear in SwiftUI)
- Provide the complete WindowSecureHelper class

### PHI Auto-Remask Timer
Complete implementation:
- PHIMaskingViewModel class with @Published var isRevealed = false
- startRevealTimer() using Task + sleep for 10 seconds then sets isRevealed = false
- cancelRevealTimer() cancels the task
- PHIMaskedField SwiftUI view that uses PHIMaskingViewModel
- Includes the eye icon toggle button with accessibilityLabel("Show patient ID")
- Auto-re-masks with toast: "Field auto-hidden for security"

### AES-256 Encrypted Cache
Complete implementation:
- EncryptedCacheService class using CryptoKit (AES.GCM)
- Keychain-stored symmetric key generation and retrieval
- save<T: Codable>(key: String, value: T, ttlHours: Int) async throws
- load<T: Codable>(key: String, type: T.Type) async throws -> T?
- TTL enforcement: stores expiry timestamp alongside encrypted data
- clear(key: String) and clearAll()
- TripDetail explicitly excluded (never cached)

### Audit Log
- PHIAuditLogger class using os_log with .private
- logReveal(fieldName: String, userSub: String) — logs field name and user sub, never PHI value
- logSession(event: SessionEvent) for login/logout/timeout events

---

## 8. ACCESSIBILITY IMPLEMENTATION (COMPLETE)

### VoiceOver for All Screens
For each screen, provide the complete SwiftUI view body showing EVERY
accessibility modifier. No screen may be omitted.

DashboardView — KPI cards:
- Each KPICard: .accessibilityLabel("Total trips: \\(count)")
- Chart: .accessibilityLabel("Data trend chart") .accessibilityHint("Shows monthly data records")
- Filter button: .accessibilityLabel("Filter") .accessibilityHint("Opens filter options")

TripListView — rows:
- Each row: .accessibilityLabel("Trip \\(trip.date), \\(trip.provider), \\(trip.distance) miles")
- Pull to refresh: .accessibilityLabel("Pull to refresh trip list")

TripDetailView — PHI fields:
- Masked field: .accessibilityLabel("Patient ID hidden") .accessibilityHint("Double tap to reveal for 10 seconds")
- Reveal button: .accessibilityLabel("Show patient ID") .accessibilityTraits(.button)

BiometricPromptView:
- .accessibilityLabel("Biometric authentication required")
- Authenticate button: .accessibilityHint("Authenticates using Face ID or Touch ID")

FilterModalView:
- Each picker: .accessibilityLabel("Select \\(filterName)")

SettingsView:
- Logout button: .accessibilityLabel("Logout") .accessibilityHint("Signs you out and clears session")
- Biometric toggle: .accessibilityLabel("Biometric authentication \\(isEnabled ? "enabled" : "disabled")")

### Dynamic Type
- Complete DynamicTypeModifier ViewModifier
- Shows how to use .minimumScaleFactor and lineLimit(nil) for all text
- Font scale test: preview at .accessibilityExtraExtraExtraLarge size

### Reduce Motion
- ReducedMotionWrapper ViewModifier
- Uses @Environment(\\.accessibilityReduceMotion)
- Wraps any animation: if reduceMotion → .opacity transition only, else → full animation
- Complete example wrapping DashboardView chart animation

---

## 9. TESTING (COMPLETE)

### XCTest Unit Tests

AuthServiceTests.swift — complete test file:
- testLoginSuccess: mock URLSession returns valid token response, assert isAuthenticated == true
- testLoginFailure: mock returns 401, assert error state
- testTokenRefresh: expired token triggers refresh, assert new token stored in Keychain
- testBiometricFallback: LAContext mock returns false, assert fallback to password shown
- testSessionTimeout: advance timer past 10 min, assert timeout dialog shown

DashboardViewModelTests.swift — complete test file:
- testLoadDashboardSuccess: mock API returns KPISummary, assert kpiCards populated
- testLoadDashboardNetworkError: mock throws URLError, assert errorMessage set
- testCacheHit: valid cache exists, assert API not called
- testCacheExpiry: cache older than 24h, assert API called and cache refreshed

TripDetailViewModelTests.swift — complete test file:
- testPHIRevealAutoMasks: call startRevealTimer(), advance 10s, assert isRevealed == false
- testPHIRevealCancelled: reveal then navigate away, assert timer cancelled
- testTripDetailNotCached: assert EncryptedCacheService.load never called for TripDetail

### XCUITest UI Tests

LoginUITests.swift — complete test file:
- testLoginScreenLoadsCorrectly: assert login button exists and is hittable
- testBiometricPromptAppears: stub biometric, tap login, assert prompt appears
- testOIDCLoginFlow: use ASWebAuthenticationSession stub, complete flow, assert Dashboard shown

DashboardUITests.swift — complete test file:
- testKPICardsVisible: assert at least 3 KPI cards exist after login
- testFilterModalOpens: tap filter button, assert FilterModalView appears
- testPullToRefreshTriggersReload: pull list, assert loading indicator appears

TripDetailUITests.swift — complete test file:
- testPHIMaskedByDefault: navigate to trip detail, assert "••••••••" text exists
- testRevealButtonUnmasks: tap eye button, assert PHI field not masked
- testAutoRemaskAfter10Seconds: tap reveal, wait 11s, assert field masked again
- testBiometricRequiredForTripDetail: assert biometric prompt shown before detail loads

### Mock Helpers
- MockURLProtocol: complete implementation for network mocking
- MockKeychainService: in-memory Keychain substitute for tests
- MockEncryptedCacheService: in-memory cache for tests

---

## 10. BUILD & DISTRIBUTION (COMPLETE)

### Fastlane Setup

Matchfile (complete):
```ruby
git_url(ENV["MATCH_GIT_URL"])
storage_mode("git")
type("development")
app_identifier(["com.proteanpursuits.app"])
username(ENV["APPLE_ID"])
```

Fastfile (complete, all lanes):
```ruby
default_platform(:ios)

platform :ios do

  desc "Run all unit and UI tests"
  lane :test do
    run_tests(
      scheme: "AppProject",
      devices: ["iPhone 15 Pro"],
      clean: true,
      code_coverage: true
    )
  end

  desc "Build and distribute to TestFlight (Staging)"
  lane :build_staging do
    setup_ci if ENV["CI"]
    match(type: "appstore", readonly: is_ci)
    increment_build_number(
      build_number: ENV["BUILD_NUMBER"] || Time.now.strftime("%Y%m%d%H%M")
    )
    build_app(
      scheme: "AppProject",
      configuration: "Staging",
      export_method: "app-store"
    )
    upload_to_testflight(
      skip_waiting_for_build_processing: true,
      groups: ["VA Internal Testers"]
    )
  end

  desc "Build and submit to App Store (Release)"
  lane :build_release do
    setup_ci if ENV["CI"]
    match(type: "appstore", readonly: is_ci)
    increment_build_number(
      build_number: ENV["BUILD_NUMBER"]
    )
    build_app(
      scheme: "AppProject",
      configuration: "Release",
      export_method: "app-store"
    )
    upload_to_app_store(
      skip_metadata: false,
      skip_screenshots: true,
      submit_for_review: false
    )
  end

end
```

### Privacy Manifest (PrivacyInfo.xcprivacy)
Complete XML with:
- NSPrivacyAccessedAPITypes for all accessed APIs (UserDefaults, FileTimestamp, etc.)
- NSPrivacyCollectedDataTypes: none (no analytics)
- NSPrivacyTrackingDomains: empty array
- NSPrivacyTracking: false

### GitHub Actions CI Snippet (.github/workflows/ios-ci.yml)
Complete workflow:
- Trigger: push to main and pull_request
- Jobs: test (runs fastlane test), build_staging (on main push only)
- Uses: actions/checkout, ruby/setup-ruby, macos-latest runner
- Secrets: MATCH_GIT_URL, APPLE_ID, MATCH_PASSWORD, BUILD_NUMBER

---

Output all sections as well-formatted markdown with complete Swift/Ruby/YAML code.
Absolutely no placeholders. Every code block must be complete and correct.
""",
        expected_output="Complete patch covering PHI security, accessibility, testing, and build/distribution sections.",
        agent=ios_dev
    )

    crew = Crew(
        agents=[ios_dev],
        tasks=[patch_task],
        process=Process.sequential,
        verbose=True
    )

    print(f"\n🔧 iOS Developer patching missing IIR sections...\n")
    result = crew.kickoff()

    patch_path = iir_path.replace("_IIR.md", "_IIR_PATCH.md")
    with open(patch_path, "w") as f:
        f.write(str(result))

    # Append patch to original IIR
    with open(iir_path, "a") as f:
        f.write("\n\n---\n\n# IIR PATCH — Missing Sections\n\n")
        f.write(str(result))

    print(f"\n💾 IIR patch saved: {patch_path}")
    print(f"💾 IIR updated with patch appended: {iir_path}")

    context["artifacts"].append({
        "name": "iOS Implementation Report Patch",
        "type": "IIR_PATCH",
        "path": patch_path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "iOS Developer"
    })
    log_event(context, "IIR_PATCH_COMPLETE", patch_path)
    save_context(context)

    return context, patch_path


if __name__ == "__main__":
    import glob

    logs = sorted(glob.glob("logs/PROJ-*.json"), key=os.path.getmtime, reverse=True)
    if not logs:
        print("No project context found.")
        exit(1)

    with open(logs[0]) as f:
        context = json.load(f)

    iir_path = None
    for artifact in context.get("artifacts", []):
        if artifact.get("type") == "IIR":
            iir_path = artifact["path"]

    if not iir_path:
        print("No IIR found in context.")
        exit(1)

    print(f"📂 Loaded context: {logs[0]}")
    print(f"📄 Patching IIR: {iir_path}")
    context, patch_path = run_ios_patch(context, iir_path)

    print(f"\n✅ IIR patch complete.")
    print(f"📄 Patch: {patch_path}")
    with open(patch_path) as f:
        print(f.read(500))
