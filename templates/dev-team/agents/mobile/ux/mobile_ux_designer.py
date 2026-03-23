import sys
sys.path.insert(0, "/home/mfelkey/dev-team")

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from agents.orchestrator.orchestrator import log_event, save_context

load_dotenv("config/.env")


def build_mobile_ux_designer() -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/qwen2.5:72b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    return Agent(
        role="Mobile UI/UX Designer",
        goal=(
            "Design a complete, platform-appropriate mobile user experience — "
            "producing a Mobile UX Document that serves as the single source of "
            "truth for all three mobile tracks (iOS native, Android native, and "
            "React Native), covering interaction patterns, visual design system, "
            "accessibility requirements, and platform-specific adaptations."
        ),
        backstory=(
            "You are a Senior Mobile UI/UX Designer with 12 years of experience "
            "designing native and cross-platform mobile applications for government, "
            "healthcare, and enterprise clients. "
            "You are deeply fluent in both Apple's Human Interface Guidelines (HIG) "
            "and Google's Material Design 3. You understand that iOS and Android users "
            "have different mental models, interaction patterns, and expectations — "
            "and you design for each platform's idioms rather than forcing one "
            "platform's patterns onto the other. "
            "You know that a bottom tab bar feels natural on iOS, while a navigation "
            "drawer or bottom navigation bar is appropriate on Android. You know that "
            "iOS users expect swipe-back navigation, while Android users rely on the "
            "system back gesture. You design for these differences explicitly. "
            "For React Native cross-platform work, you define a shared design system "
            "that adapts to each platform's conventions through platform-specific "
            "style overrides — not by forcing a single look that feels foreign on both. "
            "You are an accessibility specialist for mobile. You design for VoiceOver "
            "(iOS) and TalkBack (Android) from the start — not as an afterthought. "
            "You know touch target sizing requirements (44x44pt iOS, 48x48dp Android), "
            "dynamic type scaling, reduced motion preferences, and high contrast modes. "
            "You design with PHI protection in mind — you know when to mask sensitive "
            "data, when to require biometric re-authentication, and how to prevent "
            "data leakage through screenshots, app switcher previews, and background "
            "state. "
            "You produce a Mobile UX Document (MUXD) that is the authoritative design "
            "specification for all mobile tracks. The iOS Developer, Android Developer, "
            "React Native Architect, and Mobile QA Specialist all work from your MUXD. "
            "Your document is precise enough that developers can implement it without "
            "needing to ask design questions."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_mobile_ux_design(context: dict, prd_path: str) -> tuple:

    with open(prd_path) as f:
        prd_content = f.read()

    designer = build_mobile_ux_designer()

    muxd_task = Task(
        description=f"""
You are the Mobile UI/UX Designer. Using the Product Requirements Document below,
produce a complete Mobile UX Document (MUXD) that serves all three mobile tracks:
iOS native, Android native, and React Native cross-platform.

--- Product Requirements Document ---
{prd_content[:4000]}

Produce a complete Mobile UX Document (MUXD) with ALL of the following sections:

1. MOBILE PRODUCT OVERVIEW
   - Core user journeys on mobile
   - Target devices and OS versions
     * iOS: minimum version, target version, supported device sizes
     * Android: minimum API level, target API level, supported screen sizes/densities
   - Offline capability requirements
   - Performance expectations (launch time, transition speed, scroll performance)

2. INFORMATION ARCHITECTURE
   - Complete screen inventory
   - Navigation hierarchy (primary, secondary, modal flows)
   - Deep link structure
   - iOS-specific navigation: tab bar structure, navigation controller stack
   - Android-specific navigation: bottom navigation, back stack behavior
   - React Native shared navigation: React Navigation stack configuration

3. DESIGN SYSTEM
   - Color palette (light and dark mode, both platforms)
   - Typography scale (SF Pro for iOS, Roboto for Android, adaptive for RN)
   - Spacing and grid system (pt for iOS, dp for Android)
   - Iconography: SF Symbols (iOS), Material Symbols (Android), shared set (RN)
   - Component library: buttons, inputs, cards, navigation bars, modals,
     bottom sheets, loading states, empty states, error states, toasts

4. SCREEN DESIGNS — iOS SPECIFIC
   - Layout, components, interactions for every screen
   - Gesture support: swipe back, pull to refresh, long press
   - Dynamic Type support
   - Safe area handling: notch, Dynamic Island, home indicator
   - App switcher privacy: screens that blur PHI content

5. SCREEN DESIGNS — ANDROID SPECIFIC
   - Layout, components, interactions for every screen
   - Material You dynamic color adaptation
   - Edge-to-edge display: window insets, gesture navigation bar
   - App switcher privacy: FLAG_SECURE usage for PHI screens

6. SCREEN DESIGNS — REACT NATIVE CROSS-PLATFORM
   - Shared screen inventory with platform adaptations noted
   - Platform.OS conditionals: where iOS and Android diverge
   - Shared components vs platform-specific overrides
   - React Navigation configuration for both platforms

7. INTERACTION DESIGN
   - Transition animations (platform-appropriate timing and curves)
   - Loading and skeleton screen patterns
   - Pull-to-refresh, infinite scroll behavior
   - Haptic feedback (UIFeedbackGenerator on iOS, VibrationEffect on Android)
   - Biometric authentication flow (Face ID/Touch ID, BiometricPrompt)

8. ACCESSIBILITY SPECIFICATION
   - VoiceOver (iOS): accessibilityLabel, accessibilityHint, accessibilityTraits
   - TalkBack (Android): contentDescription, importantForAccessibility, focus order
   - Touch targets: 44x44pt (iOS), 48x48dp (Android)
   - Dynamic Type / Font Scale: layouts tested at 200% text size
   - Reduced Motion: alternative animations
   - High Contrast mode support

9. PHI & SECURITY UX
   - Screens requiring biometric re-authentication
   - Fields requiring masking with show/hide toggle
   - App switcher blur and screenshot prevention
   - Session timeout UX: warning dialog, auto-lock
   - Offline data sensitivity: what can be cached locally

10. MOBILE QA DESIGN HANDOFF
    - Device test matrix (specific iOS and Android devices)
    - OS version test matrix
    - Accessibility test checklist per screen
    - Platform-specific edge cases
    - Performance benchmarks
    - Beta distribution: TestFlight (iOS), Firebase App Distribution (Android)

Output the complete MUXD as well-formatted markdown.
""",
        expected_output="A complete Mobile UX Document covering iOS, Android, and React Native tracks.",
        agent=designer
    )

    crew = Crew(
        agents=[designer],
        tasks=[muxd_task],
        process=Process.sequential,
        verbose=True
    )

    print(f"\n🎨 Mobile UI/UX Designer creating Mobile UX Document...\n")
    result = crew.kickoff()

    os.makedirs("dev/mobile", exist_ok=True)
    muxd_path = f"dev/mobile/{context['project_id']}_MUXD.md"
    with open(muxd_path, "w") as f:
        f.write(str(result))

    print(f"\n💾 Mobile UX Document saved: {muxd_path}")

    context["artifacts"].append({
        "name": "Mobile UX Document",
        "type": "MUXD",
        "path": muxd_path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "Mobile UI/UX Designer"
    })
    context["status"] = "MUXD_COMPLETE"
    log_event(context, "MUXD_COMPLETE", muxd_path)
    save_context(context)

    return context, muxd_path


if __name__ == "__main__":
    import glob

    logs = sorted(glob.glob("logs/PROJ-*.json"), key=os.path.getmtime, reverse=True)
    if not logs:
        print("No project context found.")
        exit(1)

    with open(logs[0]) as f:
        context = json.load(f)

    prd_path = None
    for artifact in context.get("artifacts", []):
        if artifact.get("type") == "PRD":
            prd_path = artifact["path"]

    if not prd_path:
        print("No PRD found in context.")
        exit(1)

    print(f"📂 Loaded context: {logs[0]}")
    print(f"📄 Using PRD: {prd_path}")
    context, muxd_path = run_mobile_ux_design(context, prd_path)

    print(f"\n✅ Mobile UX design complete.")
    print(f"📄 MUXD: {muxd_path}")
    with open(muxd_path) as f:
        print(f.read(500))
