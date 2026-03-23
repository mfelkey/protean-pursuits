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
You are the React Native Architect producing Part 1 of the React Native Architecture
Document (RNAD) for the project cross-platform app.

--- Mobile UX Document (excerpt) ---
MUXD_PLACEHOLDER

Produce sections 1-5 of the RNAD with complete working TypeScript code.
No placeholders. No "implement logic here". Working code only.

---

## 1. ARCHITECTURE OVERVIEW

### Technology Decisions Table
Produce a complete markdown table: Library | Version | Justification
Cover: React Native 0.74, Expo SDK 51, React Navigation 6, Zustand 4,
TanStack Query 5, Axios 1.6, react-native-keychain 8, react-native-biometrics 3,
react-native-mmkv 2, react-native-reanimated 3, react-native-gesture-handler 2,
expo-screen-capture, expo-haptics, expo-auth-session 5, Jest 29, Detox 20

### Platform Adaptation — Three Patterns with Code Examples

Pattern A — Platform.OS (one or two properties differ):
```typescript
const fontSize = Platform.OS === 'ios' ? 34 : 24;
```

Pattern B — Platform.select (whole style block differs):
```typescript
const tabBarStyle = Platform.select({
  ios: { backgroundColor: '#003366', borderTopWidth: 0 },
  android: { backgroundColor: '#003366', elevation: 4 },
  default: {},
});
```

Pattern C — platform file extensions (logic differs substantially):
Explain when to create Header.ios.tsx vs Header.android.tsx and how RN resolves them.

---

## 2. NAVIGATION ARCHITECTURE

### navigation/types.ts
Complete TypeScript param lists for:
RootStackParamList, AuthStackParamList, MainTabParamList, DashboardStackParamList

### navigation/RootNavigator.tsx
Complete NavigationContainer with:
- Linking config: app://dashboard, app://detail/:id, app://login
- Auth gate from useAuthStore
- Adaptive theme via useColorScheme

### navigation/AuthNavigator.tsx
Complete Stack.Navigator: Login, BiometricPrompt. headerShown false on both.

### navigation/MainNavigator.tsx
Complete Bottom Tab Navigator: Dashboard tab, Settings tab, About tab.
Platform.select for tabBarStyle and tab icons.

### navigation/DashboardNavigator.tsx
Complete Stack.Navigator: Dashboard, TripList, TripDetail.
iOS Dashboard: headerLargeTitle true. TripDetail: headerShown false.

### navigation/NavigationService.ts
Complete NavigationService: navigationRef, navigate(), goBack(), reset().

---

## 3. STATE MANAGEMENT

### store/types.ts
Complete TypeScript interfaces for:
User, FilterOptions, ToastMessage, AuthPayload, TokenPair

### store/authStore.ts
Complete Zustand store with persist + MMKV adapter:
- State: isAuthenticated, user, accessToken, refreshToken, sessionExpiry
- Actions: setAuth(payload), clearAuth(), updateToken(token, expiry)

### store/dashboardStore.ts
Complete Zustand store:
- State: filters (FilterOptions), lastFetched (number | null)
- Actions: setFilters(partial), resetFilters()

### store/uiStore.ts
Complete Zustand store:
- State: isLoading, error, toastMessage
- Actions: setLoading, setError, showToast, clearToast

### api/queryClient.ts
Complete QueryClient: staleTime 5min, gcTime 10min, retry 2 with exponential backoff.

### api/hooks.ts
Complete custom hooks:
- useKPISummary(filters): useQuery calling dashboardApi.getKPISummary
- useTrips(page, filters): useInfiniteQuery calling tripsApi.getTrips
- useTripDetail(tripId): useQuery with staleTime 0, gcTime 0

---

## 4. API LAYER

### api/types.ts
Complete TypeScript interfaces:
User, TokenPair, FilterOptions, KPICard, KPISummary, Trip, TripDetail, PaginatedResponse<T>

### api/client.ts
Complete Axios instance:
- baseURL from process.env.EXPO_PUBLIC_API_BASE_URL
- timeout: 30000
- Request interceptor: getGenericPassword from keychain, inject Authorization header
- Response interceptor: 401 -> mutex-guarded refresh -> retry
- isRefreshing flag + failedQueue for concurrent refresh protection
- ApiError class extending Error with statusCode, code

### api/authApi.ts
Complete auth API functions: login(code, redirectUri), refreshToken(token), logout()

### api/dashboardApi.ts
Complete: getKPISummary(filters: FilterOptions): Promise<KPISummary>

### api/tripsApi.ts
Complete: getTrips(page, filters), getTripDetail(id)

---

## 5. AUTHENTICATION ARCHITECTURE

### shared/services/AuthService.ts
Complete AuthService class:
- login(): expo-auth-session AuthRequest with PKCE
- handleCallback(code): exchange code, store via setGenericPassword
- refreshToken(): exchange refresh token, update Keychain
- logout(): resetGenericPassword, clearAuth store, MMKV clearAll
- biometricLogin(): react-native-biometrics isSensorAvailable + simplePrompt
- checkBiometricAvailability(): returns BiometryType or null

### shared/services/SessionManager.ts
Complete SessionManager class:
- AppState listener: records backgroundedAt, checks 15min limit on foreground
- Foreground idle timer: 10min, reset via resetTimer()
- Warning at 9min 30s
- onExpiry(): logout + navigate to Login

### shared/hooks/useSession.ts
Complete hook: mounts SessionManager, exposes resetTimer, drives SessionWarningModal

Output all sections as well-formatted markdown with complete TypeScript code.
Every code block must be complete. No placeholders.
"""


def build_rn_architect() -> Agent:
    llm = LLM(
        model=os.getenv("TIER2_MODEL", "ollama/qwen2.5-coder:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=3600
    )
    return Agent(
        role="React Native Architect",
        goal=(
            "Produce Part 1 of a React Native Architecture Document with complete "
            "working TypeScript code covering project structure, navigation, state "
            "management, API layer, and authentication."
        ),
        backstory=(
            "You are a Senior React Native Architect with 10 years of experience "
            "building cross-platform healthcare and government mobile apps. "
            "You are expert in React Navigation 6, Zustand, TanStack Query, Axios, "
            "react-native-keychain, react-native-biometrics, and expo-auth-session. "
            "You write complete, production-ready TypeScript. "
            "You never write placeholder comments. Every function is complete."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_rn_architecture_part1(context: dict, muxd_path: str) -> tuple:
    # ── Smart extraction: load relevant sections for rn_arch_p1 ──
    ctx = load_agent_context(
        context=context,
        consumer="rn_arch_p1",
        artifact_types=["MUXD", "MOBILE_TEST_PLAN"],
        max_chars_per_artifact=6000
    )
    prompt_context = format_context_for_prompt(ctx)


    task_description = TASK_DESCRIPTION.replace("MUXD_PLACEHOLDER", muxd_content)

    architect = build_rn_architect()
    task = Task(
        description=task_description,
        expected_output=(
            "RNAD Part 1: Architecture overview, navigation, state management, "
            "API layer, and authentication with complete TypeScript code."
        ),
        agent=architect
    )
    crew = Crew(
        agents=[architect],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )

    print("\n⚛️  React Native Architect — Part 1 (sections 1-5)...\n")
    result = crew.kickoff()

    os.makedirs("/home/mfelkey/dev-team/dev/mobile", exist_ok=True)
    rnad_path = f"/home/mfelkey/dev-team/dev/mobile/{context['project_id']}_RNAD_P1.md"
    with open(rnad_path, "w") as f:
        f.write(str(result))

    print(f"\n💾 RNAD Part 1 saved: {rnad_path}")

    context["artifacts"].append({
        "name": "React Native Architecture Document Part 1",
        "type": "RNAD_P1",
        "path": rnad_path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "React Native Architect"
    })
    on_artifact_saved(context, "RNAD_P1", rnad_path)
    log_event(context, "RNAD_P1_COMPLETE", rnad_path)
    save_context(context)
    return context, rnad_path


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

    muxd_path = None
    for artifact in context.get("artifacts", []):
        if artifact.get("type") == "MUXD":
            muxd_path = artifact["path"]

    if not muxd_path:
        print("Missing MUXD in context.")
        exit(1)

    print(f"📂 Loaded context: {logs[0]}")
    print(f"📄 Using MUXD: {muxd_path}")
    context, rnad_path = run_rn_architecture_part1(context, muxd_path)
    print(f"\n✅ RNAD Part 1 complete: {rnad_path}")
