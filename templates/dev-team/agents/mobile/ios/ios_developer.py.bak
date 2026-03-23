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
            "Implement a complete, production-ready native iOS application "
            "from the Mobile UX Document — using Swift and SwiftUI, following "
            "Apple's Human Interface Guidelines, meeting HIPAA and Section 508 "
            "requirements, and producing an iOS Implementation Report that "
            "documents every screen, component, and integration point."
        ),
        backstory=(
            "You are a Senior iOS Engineer with 12 years of experience building "
            "native iOS applications for government, healthcare, and enterprise clients. "
            "You are expert-level in Swift and SwiftUI, with deep knowledge of UIKit "
            "for components that SwiftUI cannot yet handle reliably in production. "
            "You understand the full iOS development lifecycle: Xcode project setup, "
            "target configuration, signing and provisioning, TestFlight distribution, "
            "and App Store submission. "
            "You follow Apple's Human Interface Guidelines without exception. You know "
            "when to use a NavigationStack vs NavigationSplitView, when a sheet is "
            "appropriate vs a full-screen cover, and how to implement a proper tab bar "
            "that behaves exactly as iOS users expect. "
            "You are an accessibility specialist for iOS. You implement VoiceOver "
            "support natively — accessibilityLabel, accessibilityHint, "
            "accessibilityTraits, and custom rotors where needed. You test with "
            "VoiceOver enabled before every PR. "
            "You handle PHI with extreme care. You use the Keychain for all sensitive "
            "storage, never UserDefaults. You implement biometric authentication via "
            "LocalAuthentication framework. You suppress screenshots and app switcher "
            "previews on PHI screens using the documented iOS techniques. "
            "You use Swift Concurrency (async/await, actors) for all asynchronous "
            "work — no callbacks, no completion handlers in new code. "
            "You write unit tests with XCTest and UI tests with XCUITest. "
            "You produce an iOS Implementation Report (IIR) that documents every "
            "screen, component, data flow, and security control implemented, so the "
            "Mobile DevOps Engineer and Mobile QA Specialist know exactly what was "
            "built and how to test it."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_ios_implementation(context: dict, muxd_path: str, prd_path: str) -> tuple:

    with open(muxd_path) as f:
        muxd_content = f.read()[:4000]

    with open(prd_path) as f:
        prd_content = f.read()[:1000]

    ios_dev = build_ios_developer()

    iir_task = Task(
        description=f"""
You are the iOS Developer. Using the Mobile UX Document and PRD below,
produce a complete iOS Implementation Report (IIR) with working Swift/SwiftUI code.

--- Mobile UX Document (excerpt) ---
{muxd_content}

--- Product Requirements Document (excerpt) ---
{prd_content}

Produce a complete iOS Implementation Report (IIR) with ALL of the following sections:

1. PROJECT SETUP
   - Xcode project structure (targets, schemes, configurations)
   - Swift Package Manager dependencies with versions:
     * Networking: Alamofire or URLSession (native preferred)
     * Keychain: KeychainAccess
     * Charts: Swift Charts (iOS 16+) with fallback
     * Biometrics: LocalAuthentication (system framework)
   - Info.plist required keys (NSFaceIDUsageDescription, etc.)
   - Build configurations: Debug, Staging, Release
   - Environment configuration via xcconfig files
   - No hardcoded URLs or credentials — all via xcconfig/environment

2. APP ARCHITECTURE
   - Architecture pattern: MVVM with Swift Concurrency
   - Folder structure (Features/, Shared/, Services/, Models/)
   - Dependency injection approach
   - Navigation architecture: NavigationStack (iOS 16+)
   - State management: @StateObject, @EnvironmentObject, @Published

3. AUTHENTICATION
   - OIDC login flow using ASWebAuthenticationSession
   - JWT storage in Keychain (never UserDefaults)
   - Token refresh logic using async/await
   - Biometric authentication via LocalAuthentication
     * Face ID and Touch ID support
     * Fallback to passcode
     * LAContext reuse policy
   - Session timeout implementation (10 min idle, 15 min background)
   - Complete AuthService implementation

4. SCREEN IMPLEMENTATIONS
   For each of the 10 screens in the MUXD, provide:
   - Complete SwiftUI View code
   - ViewModel with all @Published properties
   - Navigation integration
   - Accessibility modifiers (.accessibilityLabel, .accessibilityHint, .accessibilityTraits)
   - PHI masking where required

   Screens:
   * SplashView
   * LoginView + LoginViewModel
   * BiometricPromptView
   * DashboardView + DashboardViewModel (KPI cards, charts)
   * FilterModalView + FilterViewModel
   * TripListView + TripListViewModel (pagination, pull-to-refresh)
   * TripDetailView + TripDetailViewModel (PHI masking, show/hide toggle)
   * SettingsView + SettingsViewModel
   * ErrorView / EmptyStateView
   * AboutView

5. NETWORKING LAYER
   - APIClient using async/await and URLSession
   - Request/response models (Codable structs)
   - JWT injection via URLRequest extension
   - Error handling (network, auth, server errors)
   - Endpoint definitions (no hardcoded base URLs — reads from config)
   - Offline cache using encrypted UserDefaults wrapper or FileManager + AES

6. DATA MODELS
   - Complete Swift structs for all API responses (Codable)
   - KPISummary, Trip, TripDetail, FilterOptions
   - PHI field annotations (custom property wrapper for masked display)

7. PHI & SECURITY IMPLEMENTATION
   - Keychain wrapper implementation
   - App switcher blur: applicationWillResignActive implementation
   - Screenshot prevention approach
   - AES-256 encrypted cache implementation
   - PHI field auto-mask after 10 seconds (Timer-based)
   - Audit log trigger on PHI field reveal
   - os_log usage with .private flag for sensitive data

8. ACCESSIBILITY IMPLEMENTATION
   - VoiceOver support for all interactive elements
   - Dynamic Type support in all Text views
   - Reduce Motion detection and alternative animations
   - Focus management after async data loads
   - Custom accessibility actions for complex components

9. TESTING
   - XCTest unit tests for all ViewModels and Services
   - XCUITest UI tests for critical flows (login, dashboard, trip detail)
   - Mock URLProtocol for network mocking
   - Test coverage targets per module (90%+)
   - Accessibility audit in XCUITest

10. BUILD & DISTRIBUTION
    - Fastlane Matchfile for code signing
    - Fastlane Fastfile lanes: test, build_staging, build_release
    - TestFlight distribution lane
    - Required App Store Connect metadata notes
    - Privacy manifest (PrivacyInfo.xcprivacy) — required for App Store

Output the complete IIR as well-formatted markdown with working Swift code.
All code must be production-ready, properly typed, and follow Swift best practices.
No hardcoded credentials, URLs, or provider-specific assumptions.
""",
        expected_output="A complete iOS Implementation Report with working Swift/SwiftUI code.",
        agent=ios_dev
    )

    crew = Crew(
        agents=[ios_dev],
        tasks=[iir_task],
        process=Process.sequential,
        verbose=True
    )

    print(f"\n📱 iOS Developer implementing native iOS application...\n")
    result = crew.kickoff()

    os.makedirs("dev/mobile", exist_ok=True)
    iir_path = f"dev/mobile/{context['project_id']}_IIR.md"
    with open(iir_path, "w") as f:
        f.write(str(result))

    print(f"\n💾 iOS Implementation Report saved: {iir_path}")

    context["artifacts"].append({
        "name": "iOS Implementation Report",
        "type": "IIR",
        "path": iir_path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "iOS Developer"
    })
    context["status"] = "IIR_COMPLETE"
    log_event(context, "IIR_COMPLETE", iir_path)
    save_context(context)

    return context, iir_path


if __name__ == "__main__":
    import glob

    logs = sorted(glob.glob("logs/PROJ-*.json"), key=os.path.getmtime, reverse=True)
    if not logs:
        print("No project context found.")
        exit(1)

    with open(logs[0]) as f:
        context = json.load(f)

    muxd_path = prd_path = None
    for artifact in context.get("artifacts", []):
        if artifact.get("type") == "MUXD":
            muxd_path = artifact["path"]
        if artifact.get("type") == "PRD":
            prd_path = artifact["path"]

    if not all([muxd_path, prd_path]):
        print("Missing MUXD or PRD.")
        exit(1)

    print(f"📂 Loaded context: {logs[0]}")
    print(f"📄 Using MUXD: {muxd_path}")
    context, iir_path = run_ios_implementation(context, muxd_path, prd_path)

    print(f"\n✅ iOS implementation complete.")
    print(f"📄 IIR: {iir_path}")
    with open(iir_path) as f:
        print(f.read(500))
