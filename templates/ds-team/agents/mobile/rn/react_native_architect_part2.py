import sys
sys.path.insert(0, "/home/mfelkey/dev-team")

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from agents.shared.knowledge_curator.rag_inject import get_knowledge_context

load_dotenv("/home/mfelkey/dev-team/config/.env")

try:
    from agents.orchestrator.orchestrator import log_event, save_context
except ImportError:
    def log_event(ctx, event, path): pass
    def save_context(ctx): pass


TASK_DESCRIPTION = """
You are the React Native Architect producing Part 2 of the React Native Architecture
Document (RNAD) for the project cross-platform app.

Produce sections 6-10 with complete working TypeScript code.
No placeholders. No "implement logic here". Working code only.

---

## 6. PHI & SECURITY ARCHITECTURE

### Screenshot Prevention (shared/hooks/useScreenCapturePrevention.ts)
Complete hook using expo-screen-capture:
```typescript
import { useEffect } from 'react'
import * as ScreenCapture from 'expo-screen-capture'

export function useScreenCapturePrevention() {
  useEffect(() => {
    ScreenCapture.preventScreenCaptureAsync()
    return () => { ScreenCapture.allowScreenCaptureAsync() }
  }, [])
}
```
Show usage in TripDetailScreen with the hook called at the top of the component.

### Encrypted Cache (shared/services/CacheService.ts)
Complete CacheService using react-native-mmkv with encryption key from Keychain:
- Constructor: retrieves or generates AES key from Keychain, creates MMKV instance
  with that key as encryptionKey
- set<T>(key: string, value: T, ttlHours: number): serializes value + expiry, stores
- get<T>(key: string): deserializes, checks expiry, returns null if expired
- delete(key: string): removes entry
- clearAll(): clears entire MMKV store
- TRIP_DETAIL_KEYS constant: set of keys that must never be cached (assert in set())

### PHI Masked Field (shared/components/PHIMaskedField.tsx)
Complete React Native component:
- Props: value: string, fieldName: string, userSub: string, label: string
- Masked by default showing bullet characters
- Reveal button (eye icon) toggles visibility
- Auto-remask after 10 seconds using useEffect + setTimeout, clears on unmount
- Calls AuditService.logReveal(fieldName, userSub) on reveal
- Accessibility: accessibilityLabel changes with mask state

### App Blur Overlay (shared/components/AppBlurOverlay.tsx)
Complete component + hook:
- useAppBlur hook: AppState listener, sets isBlurred true on background
- AppBlurOverlay component: renders BlurView (expo-blur) covering full screen
  when isBlurred is true, rendered at root app level
- iOS: BlurView with intensity 80, tint "dark"
- Android: BlurView same, or solid dark overlay fallback

### Audit Service (shared/services/AuditService.ts)
Complete AuditService:
- logReveal(fieldName: string, userSub: string): logs to console with structured
  format, never logs PHI value. Format: [PHI_AUDIT] REVEAL field=X user=Y ts=Z
- logSession(event: 'LOGIN' | 'LOGOUT' | 'TIMEOUT' | 'BACKGROUND'): same pattern
- In production would ship to remote audit endpoint; logs locally for now

---

## 7. SHARED COMPONENT LIBRARY

Produce complete working TypeScript + React Native code for each component:

### VAButton (shared/components/VAButton.tsx)
Props: variant ('primary' | 'secondary' | 'destructive'), label, onPress, disabled, loading
- Platform-adapted: iOS uses rounded rect (borderRadius 12), Android uses Material
  ripple via Pressable with android_ripple prop
- Loading state shows ActivityIndicator in place of label
- Disabled state reduces opacity to 0.5
- Full accessibility: accessibilityRole="button", accessibilityState, accessibilityLabel

### VATextInput (shared/components/VATextInput.tsx)
Props: label, value, onChangeText, placeholder, error, disabled, secureTextEntry
- States: default (gray border), focused (blue border), error (red border + message),
  disabled (reduced opacity)
- Uses useRef for focus management
- Full accessibility: accessibilityLabel, accessibilityHint, accessibilityState

### KPICard (shared/components/KPICard.tsx)
Props: title, value, subtitle, trend ('up' | 'down' | 'neutral'), trendValue
- Shows trend arrow and percentage
- accessibilityElement combined, accessibilityLabel includes all values
- Shadow on iOS, elevation on Android

### TripRow (shared/components/TripRow.tsx)
Props: trip (Trip interface), onPress
- Shows date, provider, distance
- Pressable with ripple on Android, highlight on iOS
- accessibilityRole="button", combined accessibilityLabel

### LoadingSkeleton (shared/components/LoadingSkeleton.tsx)
Props: width, height, borderRadius
- Animated shimmer effect using Animated.loop + Animated.sequence
- Fades between 0.3 and 0.7 opacity

### EmptyState (shared/components/EmptyState.tsx)
Props: title, subtitle, onRetry (optional)
- Centered layout with icon, title, subtitle
- Optional retry button using VAButton

### ErrorBanner (shared/components/ErrorBanner.tsx)
Props: message, onRetry, onDismiss
- Dismissible red banner at top of screen
- Shows retry button if onRetry provided

### ToastMessage (shared/components/ToastMessage.tsx)
- Reads from UIStore toastMessage
- Auto-dismisses after durationMs using useEffect + setTimeout
- Calls clearToast on dismiss
- Animated slide-in from bottom

---

## 8. PLATFORM ADAPTATION PATTERNS

### Navigation Headers
```typescript
// iOS: large title on Dashboard
// navigation/DashboardNavigator.tsx screenOptions for Dashboard screen:
options={{
  headerShown: true,
  headerLargeTitle: Platform.OS === 'ios',
  headerTitle: 'Dashboard',
  headerStyle: Platform.select({
    ios: { backgroundColor: '#003366' },
    android: { backgroundColor: '#003366', elevation: 4 },
    default: {},
  }),
}}
```

### Bottom Sheet
Complete example using @gorhom/bottom-sheet for FilterModal on both platforms:
- BottomSheetModal with snapPoints ['50%', '90%']
- FilterModalContent component with pickers
- Called from Dashboard via useBottomSheetModal ref

### Haptics
```typescript
// shared/utils/haptics.ts
import * as Haptics from 'expo-haptics'
import { Platform } from 'react-native'

export const triggerSelection = () => {
  if (Platform.OS !== 'web') {
    Haptics.selectionAsync()
  }
}

export const triggerSuccess = () => {
  if (Platform.OS !== 'web') {
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success)
  }
}
```

### Safe Area
```typescript
// Pattern for all screens:
import { SafeAreaView } from 'react-native-safe-area-context'

export function DashboardScreen() {
  return (
    <SafeAreaView edges={['top', 'left', 'right']} style={{ flex: 1 }}>
      ...content
    </SafeAreaView>
  )
}
```

### KeyboardAvoidingView
```typescript
import { KeyboardAvoidingView, Platform } from 'react-native'

<KeyboardAvoidingView
  behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
  style={{ flex: 1 }}
>
  ...form content
</KeyboardAvoidingView>
```

### Font Selection
```typescript
// shared/theme/typography.ts
import { Platform } from 'react-native'

export const fonts = {
  regular: Platform.select({ ios: 'System', android: 'Roboto', default: 'System' }),
  mono: Platform.select({ ios: 'Courier', android: 'monospace', default: 'monospace' }),
}
```

---

## 9. TESTING ARCHITECTURE

### Jest Configuration (jest.config.js)
Complete jest.config.js for React Native + TypeScript + Expo:
- preset: jest-expo
- transformIgnorePatterns covering all native modules
- moduleNameMapper for assets and SVGs
- setupFilesAfterFramework pointing to jest.setup.ts

### Test Utilities (src/__tests__/utils/renderWithProviders.tsx)
Complete custom render function wrapping:
- QueryClientProvider with test QueryClient (no retries, no caching)
- NavigationContainer with test navigation state
- All Zustand stores reset to initial state before each test
- Returns all React Testing Library utilities plus navigation ref

### Unit Tests

#### AuthService.test.ts
Complete test file:
- mockKeychain setup (jest.mock react-native-keychain)
- mockBiometrics setup (jest.mock react-native-biometrics)
- testLoginSuccess: mocks authApi.login, asserts keychain set + store updated
- testRefreshToken: mocks authApi.refreshToken, asserts new token in keychain
- testBiometricLoginSuccess: mocks simplePrompt success, asserts isAuthenticated
- testBiometricLoginFailure: mocks simplePrompt failure, asserts not authenticated

#### CacheService.test.ts
Complete test file:
- mockMMKV in-memory store
- testSetAndGet: set value, get back same value
- testTTLExpiry: set with 0.001h TTL, advance time, assert null returned
- testTripDetailBlocked: assert set() throws for trip detail keys

#### PHIMaskedField.test.tsx
Complete test file using renderWithProviders:
- testMaskedByDefault: renders bullet characters initially
- testRevealOnPress: tap eye button, assert value visible
- testAutoRemaskAfter10s: use jest.useFakeTimers, advance 10s, assert masked again
- testAuditLogCalled: assert AuditService.logReveal called with correct args

### Detox E2E (e2e/detox.config.js + e2e/flows/login.test.ts)
Complete Detox configuration and login flow test:
- detox.config.js: iOS simulator (iPhone 15 Pro), Android emulator (Pixel 7 API 34)
- login.test.ts: launch app, assert login screen, tap login button, complete OIDC
  (stubbed), assert Dashboard screen visible, assert KPI cards exist

---

## 10. BUILD & ENVIRONMENT CONFIGURATION

### Workflow Decision
Expo bare workflow. Justification: react-native-mmkv and react-native-biometrics
require native module linking not available in managed workflow. Bare workflow
provides full native access while retaining Expo tooling (EAS Build, expo-updates).

### app.config.js (complete)
Complete app.config.js with:
- name, slug, version, platforms
- ios: bundleIdentifier com.proteanpursuits.app, buildNumber from env
- android: package com.proteanpursuits.app, versionCode from env
- plugins array: expo-screen-capture, expo-haptics, expo-build-properties
  (set iOS deployment target 14.0, Android minSdkVersion 24)
- extra: apiBaseUrl from process.env.EXPO_PUBLIC_API_BASE_URL

### eas.json (complete)
Complete EAS Build config:
- cli.version: ">= 9.0.0"
- build.development: developmentClient true, distribution internal, both platforms
- build.preview: distribution internal, iOS simulator false, Android APK
- build.production: autoIncrement true, both platforms, credentials from EAS
- submit.production: iOS App Store Connect config, Android Play Store config

### Environment Variables (.env.example)
Complete example:
- EXPO_PUBLIC_API_BASE_URL
- EXPO_PUBLIC_OIDC_CLIENT_ID
- EXPO_PUBLIC_OIDC_DISCOVERY_URL
- EXPO_PUBLIC_REDIRECT_URI

### OTA Updates (app.config.js updates section)
Complete expo-updates configuration:
- updates.enabled: true
- updates.checkAutomatically: ON_LOAD
- updates.fallbackToCacheTimeout: 3000
- runtimeVersion using appVersion policy
- Channel strategy: development / preview / production

### GitHub Actions Workflow (.github/workflows/rn-ci.yml)
Complete workflow:
- Trigger: push to main, pull_request
- Jobs: test (jest), build_preview (EAS preview on main push)
- Uses: actions/checkout, actions/setup-node, expo/expo-github-action
- Secrets: EXPO_TOKEN, EXPO_PUBLIC_API_BASE_URL

Output all sections as well-formatted markdown with complete TypeScript/JavaScript code.
Every code block must be complete. No section may end with placeholder comments.
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
            "Produce Part 2 of a React Native Architecture Document covering PHI "
            "security, shared components, platform adaptation, testing, and build "
            "configuration — with complete working TypeScript code."
        ),
        backstory=(
            "You are a Senior React Native Architect with 10 years of experience "
            "building HIPAA-compliant cross-platform mobile apps. "
            "You are expert in expo-screen-capture, react-native-mmkv, "
            "react-native-reanimated, Detox, EAS Build, and expo-updates. "
            "You write complete, production-ready TypeScript. "
            "You never write placeholder comments. Every function is complete."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_rn_architecture_part2(context: dict) -> tuple:
    # ── RAG: inject current knowledge (RN/Expo releases, mobile security) ──
    project_title = context.get("structured_spec", {}).get("title", "project")
    knowledge = get_knowledge_context(
        agent_role="RN Architect",
        task_summary=f"React Native PHI security and build config for {project_title}",
    )

    task_description = TASK_DESCRIPTION
    if knowledge:
        task_description += f"""

CURRENT KNOWLEDGE (from knowledge base — use only if relevant to this task):
{knowledge}
"""

    architect = build_rn_architect()

    task = Task(
        description=task_description,
        expected_output=(
            "RNAD Part 2: PHI security, shared components, platform adaptation, "
            "testing architecture, and build configuration with complete TypeScript code."
        ),
        agent=architect
    )

    crew = Crew(
        agents=[architect],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )

    print("\n⚛️  React Native Architect — Part 2 (sections 6-10)...\n")
    result = crew.kickoff()

    os.makedirs("/home/mfelkey/dev-team/dev/mobile", exist_ok=True)
    rnad_path = f"/home/mfelkey/dev-team/dev/mobile/{context['project_id']}_RNAD_P2.md"
    with open(rnad_path, "w") as f:
        f.write(str(result))

    print(f"\n💾 RNAD Part 2 saved: {rnad_path}")

    context["artifacts"].append({
        "name": "React Native Architecture Document Part 2",
        "type": "RNAD_P2",
        "path": rnad_path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "React Native Architect"
    })
    log_event(context, "RNAD_P2_COMPLETE", rnad_path)
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

    print(f"📂 Loaded context: {logs[0]}")
    context, rnad_path = run_rn_architecture_part2(context)
    print(f"\n✅ RNAD Part 2 complete: {rnad_path}")
