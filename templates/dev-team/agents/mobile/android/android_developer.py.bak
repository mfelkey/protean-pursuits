import sys
sys.path.insert(0, "/home/mfelkey/dev-team")

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from agents.orchestrator.orchestrator import log_event, save_context

load_dotenv("config/.env")


def build_android_developer() -> Agent:
    llm = LLM(
        model=os.getenv("TIER2_MODEL", "ollama/qwen2.5-coder:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    return Agent(
        role="Android Developer",
        goal=(
            "Implement a complete, production-ready native Android application "
            "from the Mobile UX Document — using Kotlin and Jetpack Compose, "
            "following Material Design 3, meeting HIPAA and accessibility "
            "requirements, and producing an Android Implementation Report that "
            "documents every screen, component, and integration point."
        ),
        backstory=(
            "You are a Senior Android Engineer with 12 years of experience building "
            "native Android applications for government, healthcare, and enterprise clients. "
            "You are expert-level in Kotlin and Jetpack Compose, with deep knowledge of "
            "the Android SDK, Jetpack libraries, and the full Android development lifecycle. "
            "You follow Material Design 3 without exception. You know when to use a "
            "BottomNavigationBar vs a NavigationDrawer, how to implement proper back stack "
            "behavior with NavController, and how Android users expect the system back "
            "gesture to behave. You never fight the platform. "
            "You use the modern Android architecture stack exclusively: "
            "ViewModel + StateFlow + Compose, Hilt for dependency injection, "
            "Retrofit + OkHttp for networking, Room for local storage, "
            "DataStore for preferences, WorkManager for background tasks, "
            "and the Navigation component for all navigation. "
            "You are an accessibility specialist for Android. You implement TalkBack "
            "support natively — contentDescription, importantForAccessibility, "
            "semantics blocks in Compose, and logical focus order. You test with "
            "TalkBack enabled before every PR. "
            "You handle PHI with extreme care. You use EncryptedSharedPreferences "
            "and the Android Keystore for sensitive storage. You implement biometric "
            "authentication via BiometricPrompt. You apply FLAG_SECURE to all "
            "Activities displaying PHI to prevent screenshots and hide content "
            "in the recent apps screen. "
            "You write unit tests with JUnit5 + MockK and UI tests with Espresso "
            "and Compose UI Testing. "
            "You produce an Android Implementation Report (AIR) that documents every "
            "screen, component, data flow, and security control implemented, so the "
            "Mobile DevOps Engineer and Mobile QA Specialist know exactly what was "
            "built and how to test it."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_android_implementation(context: dict, muxd_path: str, prd_path: str) -> tuple:

    with open(muxd_path) as f:
        muxd_content = f.read()[:4000]

    with open(prd_path) as f:
        prd_content = f.read()[:1000]

    android_dev = build_android_developer()

    air_task = Task(
        description=f"""
You are the Android Developer. Using the Mobile UX Document and PRD below,
produce a complete Android Implementation Report (AIR) with working Kotlin/Compose code.

--- Mobile UX Document (excerpt) ---
{muxd_content}

--- Product Requirements Document (excerpt) ---
{prd_content}

Produce a complete Android Implementation Report (AIR) with ALL of the following sections.
You MUST produce working code for every section — no bullet-point summaries, no
"implement logic here" placeholders. Every section requires actual Kotlin code.

1. PROJECT SETUP
   - Gradle project structure (app module, build.gradle.kts)
   - Complete dependencies block with versions:
     * Jetpack Compose BOM (latest stable)
     * Hilt for dependency injection
     * Retrofit + OkHttp for networking
     * Room for encrypted local cache
     * DataStore for preferences
     * Navigation Compose
     * Biometric library
     * Security Crypto (EncryptedSharedPreferences)
     * Accompanist (if needed)
   - AndroidManifest.xml required permissions and features
   - Build variants: debug, staging, release
   - BuildConfig fields for environment-specific URLs (no hardcoded values)
   - ProGuard/R8 rules for release builds

2. APP ARCHITECTURE
   - Architecture: MVVM + UDF with StateFlow
   - Complete package structure
   - Hilt dependency injection setup (AppModule, NetworkModule, DatabaseModule)
   - Navigation graph (NavHost with all destinations)
   - State management pattern: UiState sealed class per screen

3. AUTHENTICATION
   - OIDC login via AppAuth-Android library
   - JWT storage in EncryptedSharedPreferences
   - Token refresh with OkHttp Authenticator interceptor
   - BiometricPrompt implementation:
     * Class 3 (Strong) biometric required
     * CryptoObject tied to Android Keystore key
     * Fallback to device credential
   - Session timeout: 10 min foreground idle, 15 min background
   - Complete AuthRepository and AuthViewModel implementations

4. SCREEN IMPLEMENTATIONS
   For each of the 10 screens in the MUXD, provide complete Composable functions
   and ViewModels. No placeholders — working Compose UI code required.

   Screens:
   * SplashScreen — animated logo, init check
   * LoginScreen + LoginViewModel — OIDC button, biometric option
   * BiometricPromptScreen — BiometricPrompt integration
   * DashboardScreen + DashboardViewModel — KPI cards, charts (Vico or MPAndroidChart)
   * FilterBottomSheet + FilterViewModel — ModalBottomSheet, date/type/region pickers
   * TripListScreen + TripListViewModel — LazyColumn, pull-to-refresh, infinite scroll
   * TripDetailScreen + TripDetailViewModel — PHI masking, show/hide toggle, auto-remask timer
   * SettingsScreen + SettingsViewModel — biometric toggle, logout
   * ErrorScreen / EmptyStateScreen — retry action, empty illustration
   * AboutScreen — version, VA disclaimer

   Each screen must include:
   - Complete @Composable function
   - UiState sealed class
   - ViewModel with StateFlow<UiState>
   - Semantics/contentDescription for TalkBack
   - FLAG_SECURE applied where PHI is displayed

5. NETWORKING LAYER
   - Retrofit service interface for all endpoints
   - OkHttp client with:
     * AuthInterceptor (injects Bearer token)
     * Authenticator (handles 401, refreshes token)
     * HttpLoggingInterceptor (DEBUG only, no PHI logged)
     * Certificate pinning configuration
   - ApiResponse sealed class wrapper
   - Coroutines-based repository pattern
   - No hardcoded base URLs — reads from BuildConfig.BASE_URL

6. LOCAL STORAGE & CACHE
   - Room database with SQLCipher encryption
   - Entities: TripEntity, KpiCacheEntity
   - DAOs with Flow return types
   - Repository cache-then-network strategy
   - Cache TTL enforcement (24h for KPI/TripList, never for TripDetail)
   - EncryptedSharedPreferences for tokens and settings

7. PHI & SECURITY IMPLEMENTATION
   - FLAG_SECURE: applied in onCreate() for PHI Activities/Composables
   - BiometricPrompt with CryptoObject (Keystore-backed AES key)
   - PHI field auto-remask after 10 seconds (coroutine-based timer)
   - Audit log trigger on PHI field reveal (logs sub claim + timestamp, no PHI)
   - EncryptedSharedPreferences wrapper class
   - Android Keystore key generation and management
   - Timber logging with no PHI — all sensitive fields tagged @Suppress

8. ACCESSIBILITY IMPLEMENTATION
   - TalkBack: semantics blocks for all interactive Composables
   - contentDescription for all icons and images
   - Logical focus traversal order
   - Font scaling support: sp units throughout, no fixed text sizes
   - Reduced motion: check animatorDurationScale, provide fade alternatives
   - Touch target enforcement: minimum 48dp for all tappable elements
   - Compose UI test accessibility checks

9. TESTING
   - JUnit5 + MockK unit tests for all ViewModels and Repositories
   - Compose UI tests for critical screens (Dashboard, TripDetail, Login)
   - Espresso tests for BiometricPrompt flow
   - Hilt testing setup (HiltAndroidTest)
   - Mock Retrofit responses using MockWebServer
   - Test coverage targets: 90%+ for ViewModels and Repositories

10. BUILD & DISTRIBUTION
    - Fastlane Appfile and Fastfile lanes: test, build_staging, build_release
    - Google Play internal track distribution lane
    - Signing config via environment variables (no keystore in repo)
    - Firebase App Distribution lane for beta testing
    - Complete .github/workflows/android-ci.yml snippet

Output the complete AIR as well-formatted markdown with working Kotlin code.
All code must be production-ready, idiomatic Kotlin, and follow Android best practices.
No hardcoded credentials, URLs, or provider-specific assumptions.
Every section must have actual working code — not descriptions of what code should do.
""",
        expected_output="A complete Android Implementation Report with working Kotlin/Compose code.",
        agent=android_dev
    )

    crew = Crew(
        agents=[android_dev],
        tasks=[air_task],
        process=Process.sequential,
        verbose=True
    )

    print(f"\n🤖 Android Developer implementing native Android application...\n")
    result = crew.kickoff()

    os.makedirs("dev/mobile", exist_ok=True)
    air_path = f"dev/mobile/{context['project_id']}_AIR.md"
    with open(air_path, "w") as f:
        f.write(str(result))

    print(f"\n💾 Android Implementation Report saved: {air_path}")

    context["artifacts"].append({
        "name": "Android Implementation Report",
        "type": "AIR",
        "path": air_path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "Android Developer"
    })
    context["status"] = "AIR_COMPLETE"
    log_event(context, "AIR_COMPLETE", air_path)
    save_context(context)

    return context, air_path


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
    context, air_path = run_android_implementation(context, muxd_path, prd_path)

    print(f"\n✅ Android implementation complete.")
    print(f"📄 AIR: {air_path}")
    with open(air_path) as f:
        print(f.read(500))
