import sys
sys.path.insert(0, "/home/mfelkey/dev-team")

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from agents.orchestrator.context_manager import load_agent_context, format_context_for_prompt, on_artifact_saved


load_dotenv("/home/mfelkey/dev-team/config/.env")

try:
    from agents.orchestrator.orchestrator import log_event, save_context
except ImportError:
    def log_event(ctx, event, path): pass
    def save_context(ctx): pass


TASK_DESCRIPTION = """
You are the React Native Developer implementing the the project
cross-platform app. The React Native Architect has defined the architecture.
Your job is to implement the screen-level code.

Produce the React Native Implementation Report (RNIR) with complete working
TypeScript/React Native code for all screens and feature implementations.
No placeholders. No "implement logic here". Working code only.

---

## 1. SPLASH SCREEN (features/auth/screens/SplashScreen.tsx)

Complete implementation:
- VA logo centered on screen with backgroundColor #003366
- Animated fade-in using Animated.Value + Animated.timing on mount
- useEffect: checks Keychain for existing token on mount
  - If token exists and not expired: navigates to Main
  - If token expired: attempts silent refresh, on fail navigates to Auth
  - If no token: navigates to Auth after animation completes
- Uses NavigationService to navigate imperatively
- StatusBar: light-content on both platforms

---

## 2. LOGIN SCREEN (features/auth/screens/LoginScreen.tsx)

Complete implementation:
- App branding: logo, app title, subtitle
- Single "Sign in with VA Credentials" button using VAButton (primary variant)
- Loading state: button shows ActivityIndicator while OIDC flow in progress
- Error state: ErrorBanner below button showing error message
- onPress: calls AuthService.login(), handles success (navigate Main) and error
- Biometric option: if biometric available, show "Use Face ID / Fingerprint" link below button
  calls AuthService.biometricLogin() on press
- useEffect: calls AuthService.checkBiometricAvailability() to conditionally show link
- KeyboardAvoidingView wrapper with platform behavior
- SafeAreaView with edges top/bottom

---

## 3. BIOMETRIC PROMPT SCREEN (features/auth/screens/BiometricPromptScreen.tsx)

Complete implementation:
- Full-screen modal appearance
- Lock icon centered
- Title: "Authentication Required"
- Subtitle: "Please authenticate to access protected health information"
- "Authenticate" button: calls AuthService.biometricLogin()
  On success: navigates back to previous screen
  On failure: shows error message, offers "Cancel" option
- "Cancel" button: navigates back without authenticating
- Triggered automatically when navigating to TripDetail screen

---

## 4. DASHBOARD SCREEN (features/dashboard/screens/DashboardScreen.tsx)

Complete implementation:
- useKPISummary(filters) from React Query — shows LoadingSkeleton while loading
- Three KPICard components: Total Trips, In-House %, Cost Avoidance
- Line chart using react-native-chart-kit or Victory Native showing monthly trends
  (use a simple mock data structure if chart library not specified)
- Filter button in header (toolbar) — opens FilterModal via navigation
- Pull-to-refresh: refetch on refresh using queryClient.invalidateQueries
- "View Trip List" button navigates to TripList with current filters
- Error state: ErrorBanner with retry button
- useSession() called at top to initialize session management
- useFocusEffect: invalidates queries when screen comes back into focus

---

## 5. FILTER MODAL SCREEN (features/dashboard/screens/FilterModal.tsx)

Complete implementation:
- Presented as modal (gestureEnabled true, detents ['medium', 'large'] on iOS)
- Three pickers: Month (1-12 + All), Trip Type (All/In-House/Contracted), Region
- Current filter values pre-populated from DashboardStore
- "Apply" button: updates DashboardStore filters, dismisses modal
- "Reset" button: resets filters to defaults, dismisses modal
- "Cancel" X button in header
- All pickers have accessibilityLabel and accessibilityHint

---

## 6. TRIP LIST SCREEN (features/trips/screens/TripListScreen.tsx)

Complete implementation:
- useTrips(page, filters) with useInfiniteQuery for pagination
- FlatList with TripRow components
- Pull-to-refresh: refetch first page
- Infinite scroll: onEndReached loads next page, shows LoadingSkeleton footer
- Empty state: EmptyState component with "No trips found" and filter reset option
- Error state: ErrorBanner with retry
- Each TripRow: onPress navigates to TripDetail with trip.id
  Before navigating: checks if biometric re-auth needed (always required for TripDetail)
  navigates to BiometricPrompt first, then TripDetail on success
- Filter chips shown below header showing active filters

---

## 7. TRIP DETAIL SCREEN (features/trips/screens/TripDetailScreen.tsx)

Complete implementation:
- useScreenCapturePrevention() called at top
- useTripDetail(tripId) from React Query — no caching (staleTime 0)
- Custom header with back button (headerShown false in navigator)
- Non-PHI fields displayed normally: date, provider, distance, trip type, region
- PHI fields use PHIMaskedField component:
  - Patient ID: PHIMaskedField with fieldName="patient_id"
  - Cost: PHIMaskedField with fieldName="trip_cost"
- LoadingSkeleton shown while loading
- Error state: full-screen error with back button
- AppBlurOverlay rendered conditionally (handled at app root, not here)
- useAuthStore to get user.sub for PHIMaskedField userSub prop

---

## 8. SETTINGS SCREEN (features/settings/screens/SettingsScreen.tsx)

Complete implementation:
- Account section:
  - User name and email from AuthStore (non-editable display)
  - Biometric toggle: reads/writes biometric preference to MMKV via CacheService
    calls AuthService.checkBiometricAvailability() to gate toggle
- Security section:
  - Session timeout display: "Auto-lock after 10 minutes"
  - Privacy Policy row: opens VA privacy URL via Linking.openURL
- App section:
  - App version from expo-constants
  - About row: navigates to About screen
- Logout button (destructive): shows confirmation Alert, calls AuthService.logout()
  on confirm, navigates to Auth stack
- All rows have accessibilityRole and accessibilityLabel

---

## 9. ABOUT SCREEN (features/settings/screens/AboutScreen.tsx)

Complete implementation:
- VA logo
- App name and version from expo-constants
- VA disclaimer text (placeholder text acceptable)
- Open Source Licenses row: navigates to licenses list
- Contact/Support row: opens mailto link
- All text selectable for accessibility

---

## 10. APP ROOT (App.tsx)

Complete implementation:
- QueryClientProvider wrapping everything
- SafeAreaProvider from react-native-safe-area-context
- GestureHandlerRootView (required for react-native-gesture-handler)
- RootNavigator
- AppBlurOverlay rendered at root level using useAppBlur hook
- ToastMessage rendered at root level reading from UIStore
- TouchableWithoutFeedback wrapping entire app resetting session timer
  via useSession().resetTimer on every touch

Output all screens as well-formatted markdown with complete TypeScript code.
Every screen must be fully implemented. No screen may end with placeholder comments.
Each screen should import from the correct paths based on the architecture defined
in the RNAD (features/*, shared/components/*, shared/services/*, store/*, api/*).
"""


def build_rn_developer() -> Agent:
    llm = LLM(
        model=os.getenv("TIER2_MODEL", "ollama/qwen2.5-coder:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=3600
    )
    return Agent(
        role="React Native Developer",
        goal=(
            "Implement all 10 screens of the the project React Native "
            "app with complete, working TypeScript code — consuming the architecture "
            "defined in the RNAD."
        ),
        backstory=(
            "You are a Senior React Native Developer with 8 years of experience "
            "implementing production mobile apps for government and healthcare clients. "
            "You are expert in React Native screens, FlatList, navigation, "
            "React Query hooks, Zustand stores, and HIPAA-compliant PHI handling. "
            "You implement from architecture documents precisely — your imports match "
            "the defined folder structure, your hooks match the defined API, and your "
            "components use the shared component library correctly. "
            "You write complete, compilable TypeScript. "
            "You never write '// TODO' or placeholder comments. "
            "Every screen you implement is production-ready."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_rn_developer(context: dict, rnad_p1_path: str, rnad_p2_path: str) -> tuple:
    # Give developer a summary of the architecture to reference
    # ── Smart extraction: load relevant sections for rn_dev ──
    ctx = load_agent_context(
        context=context,
        consumer="rn_dev",
        artifact_types=["RNAD_P1", "RNAD_P2", "MOBILE_TEST_PLAN"],
        max_chars_per_artifact=6000
    )
    prompt_context = format_context_for_prompt(ctx)


    task_description = TASK_DESCRIPTION + f"""

---
## ARCHITECTURE REFERENCE (from RNAD Part 1)
"""

    developer = build_rn_developer()

    task = Task(
        description=task_description,
        expected_output=(
            "React Native Implementation Report with complete TypeScript code "
            "for all 10 screens: Splash, Login, BiometricPrompt, Dashboard, "
            "FilterModal, TripList, TripDetail, Settings, About, and App root."
        ),
        agent=developer
    )

    crew = Crew(
        agents=[developer],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )

    print("\n⚛️  React Native Developer implementing all screens...\n")
    result = crew.kickoff()

    os.makedirs("/home/mfelkey/dev-team/dev/mobile", exist_ok=True)
    rnir_path = f"/home/mfelkey/dev-team/dev/mobile/{context['project_id']}_RNIR.md"
    with open(rnir_path, "w") as f:
        f.write(str(result))

    print(f"\n💾 React Native Implementation Report saved: {rnir_path}")

    context["artifacts"].append({
        "name": "React Native Implementation Report",
        "type": "RNIR",
        "path": rnir_path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "React Native Developer"
    })
    on_artifact_saved(context, "RN_GUIDE", rnir_path)
    log_event(context, "RNIR_COMPLETE", rnir_path)
    save_context(context)
    return context, rnir_path


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

    rnad_p1_path = rnad_p2_path = None
    for artifact in context.get("artifacts", []):
        if artifact.get("type") == "RNAD_P1":
            rnad_p1_path = artifact["path"]
        if artifact.get("type") == "RNAD_P2":
            rnad_p2_path = artifact["path"]

    if not rnad_p1_path:
        print("Missing RNAD_P1 in context.")
        exit(1)

    print(f"📂 Loaded context: {logs[0]}")
    print(f"📄 Using RNAD_P1: {rnad_p1_path}")
    context, rnir_path = run_rn_developer(context, rnad_p1_path, rnad_p2_path)
    print(f"\n✅ React Native Implementation Report complete: {rnir_path}")
