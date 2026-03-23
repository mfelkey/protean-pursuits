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
        role="iOS Accessibility Specialist",
        goal=(
            "Produce complete, per-screen VoiceOver accessibility implementations "
            "for all screens in the iOS app, plus Dynamic Type "
            "and Reduce Motion modifiers. Every screen must have working Swift code "
            "showing every accessibility modifier — no summaries, no examples, "
            "no placeholders."
        ),
        backstory=(
            "You are a Senior iOS Accessibility Engineer with 10 years of experience "
            "implementing VoiceOver support for government and healthcare apps. "
            "You are an expert in SwiftUI accessibility modifiers: .accessibilityLabel, "
            ".accessibilityHint, .accessibilityTraits, .accessibilityValue, "
            ".accessibilityElement(children:), .accessibilityAction, and "
            ".accessibilityAdjustableAction. "
            "You know that Section 508 compliance requires every interactive element "
            "to have a meaningful accessibilityLabel, every non-obvious action to have "
            "an accessibilityHint, and every custom control to declare its "
            "accessibilityTraits. "
            "You write complete SwiftUI view bodies. You never write 'all elements "
            "have accessibility labels' — you write the actual modifier on every "
            "actual element. No exceptions, no summaries."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_accessibility_patch(context: dict, iir_path: str) -> tuple:

    ios_dev = build_ios_developer()

    a11y_task = Task(
        description="""
You are producing Section 8 — Accessibility Implementation — for the project
iOS app. This is a HIPAA-regulated healthcare app requiring Section 508 compliance.

Produce complete SwiftUI code for ALL of the following. Every element in every
screen must have accessibility modifiers. No screen may be omitted. No placeholder
comments. Working Swift code only.

---

## 8. ACCESSIBILITY IMPLEMENTATION (COMPLETE)

### 8.1 DashboardView — Complete Accessible Implementation

Produce the complete DashboardView body with:
- Navigation title: .accessibilityLabel("Dashboard")
- Each KPI card wrapped in .accessibilityElement(children: .combine)
  with .accessibilityLabel("Total trips: \\(totalTrips), in-house: \\(inHousePercent) percent, cost: \\(cost) dollars")
- Chart view: .accessibilityLabel("Monthly trip trend chart")
  .accessibilityHint("Shows data counts by month. Double tap to hear data summary.")
  .accessibilityElement(children: .ignore)
  with a custom .accessibilityAction(named: "Read chart data") { ... }
- Filter button in toolbar:
  .accessibilityLabel("Filter trips")
  .accessibilityHint("Opens filter options for month, trip type, and region")
  .accessibilityTraits(.button)
- Pull to refresh:
  .accessibilityLabel("Pull down to refresh dashboard data")
- Loading skeleton:
  .accessibilityLabel("Loading dashboard data")
  .accessibilityTraits(.updatesFrequently)

### 8.2 TripListView — Complete Accessible Implementation

Produce the complete TripListView body with:
- Each trip row .accessibilityElement(children: .combine)
  .accessibilityLabel("Trip on \\(trip.date), provider \\(trip.provider), distance \\(trip.distance) miles")
  .accessibilityHint("Double tap to view trip details")
  .accessibilityTraits(.button)
- Empty state view:
  .accessibilityLabel("No trips found")
  .accessibilityHint("Try adjusting your filters")
- Loading indicator:
  .accessibilityLabel("Loading trips")
  .accessibilityTraits(.updatesFrequently)
- Pagination footer (loading more):
  .accessibilityLabel("Loading more trips")

### 8.3 TripDetailView — Complete Accessible Implementation

Produce the complete TripDetailView body with:
- Screen title: .accessibilityLabel("Trip detail")
- Date row: .accessibilityLabel("Trip date: \\(trip.date)")
- Provider row: .accessibilityLabel("Provider: \\(trip.provider)")
- Distance row: .accessibilityLabel("Distance: \\(trip.distance) miles")
- Patient ID field (masked):
  .accessibilityLabel("Patient ID: hidden")
  .accessibilityHint("Double tap the reveal button to show for 10 seconds")
- Patient ID field (revealed):
  .accessibilityLabel("Patient ID: \\(patientId)")
  .accessibilityHint("Field will auto-hide after 10 seconds")
- Reveal/hide button:
  .accessibilityLabel(isRevealed ? "Hide patient ID" : "Show patient ID")
  .accessibilityHint(isRevealed ? "Hides the patient identification number" : "Reveals the patient identification number for 10 seconds")
  .accessibilityTraits(.button)
- Cost field (masked and revealed, same pattern as patient ID)
- Biometric re-auth prompt overlay:
  .accessibilityLabel("Authentication required")
  .accessibilityHint("Biometric authentication is required to view protected health information")

### 8.4 FilterModalView — Complete Accessible Implementation

Produce the complete FilterModalView body with:
- Modal title: .accessibilityLabel("Filter trips")
- Month picker:
  .accessibilityLabel("Select month")
  .accessibilityHint("Swipe up or down to change the selected month")
  .accessibilityTraits(.adjustable)
  with .accessibilityAdjustableAction { ... }
- Trip type picker:
  .accessibilityLabel("Select trip type")
  .accessibilityHint("Choose between all trips, in-house, or contracted")
- Region picker:
  .accessibilityLabel("Select region")
  .accessibilityHint("Filter trips by geographic region")
- Apply button:
  .accessibilityLabel("Apply filters")
  .accessibilityHint("Applies selected filters and closes this panel")
  .accessibilityTraits(.button)
- Reset button:
  .accessibilityLabel("Reset filters")
  .accessibilityHint("Clears all filters and shows all trips")
  .accessibilityTraits(.button)

### 8.5 SettingsView — Complete Accessible Implementation

Produce the complete SettingsView body with:
- Section header "Account": .accessibilityAddTraits(.isHeader)
- Biometric toggle:
  .accessibilityLabel("Biometric authentication")
  .accessibilityValue(biometricEnabled ? "enabled" : "disabled")
  .accessibilityHint("Double tap to \\(biometricEnabled ? "disable" : "enable") biometric login")
- Session timeout row:
  .accessibilityLabel("Session timeout: 10 minutes")
  .accessibilityHint("Session automatically locks after 10 minutes of inactivity")
- Privacy policy row:
  .accessibilityLabel("Privacy policy")
  .accessibilityHint("Opens the VA privacy policy document")
  .accessibilityTraits([.button, .link])
- Logout button:
  .accessibilityLabel("Log out")
  .accessibilityHint("Signs you out and clears all session data")
  .accessibilityTraits(.button)
  — must also post UIAccessibility.post(notification: .announcement, argument: "Logged out successfully") after logout

### 8.6 LoginView — Complete Accessible Implementation

Produce the complete LoginView body with:
- App logo image: .accessibilityLabel("the app")
  .accessibilityHidden(false) (decorative only — make it hidden if truly decorative)
- OIDC login button:
  .accessibilityLabel("Log in with VA credentials")
  .accessibilityHint("Opens the VA authentication page in your browser")
  .accessibilityTraits(.button)
- Loading state button:
  .accessibilityLabel("Logging in")
  .accessibilityTraits([.button, .notEnabled])
- Error message:
  .accessibilityLabel("Login error: \\(errorMessage)")
  .accessibilityTraits(.staticText)
  — must post UIAccessibility.post(notification: .announcement, argument: errorMessage) when error appears

---

### 8.7 Dynamic Type Support

Produce a complete DynamicTypeAwareText ViewModifier:
```swift
struct DynamicTypeAwareText: ViewModifier {
    // Uses @Environment(\\.dynamicTypeSize)
    // Applies .minimumScaleFactor(0.7) for sizes below .accessibility1
    // Applies lineLimit(nil) always
    // Applies .fixedSize(horizontal: false, vertical: true)
}
```

Show usage on a Body-M text element and a Header-XL text element.

Show a complete PreviewProvider demonstrating the view at
.accessibilityExtraExtraExtraLarge dynamic type size.

---

### 8.8 Reduce Motion Support

Produce a complete ReduceMotionModifier ViewModifier:
```swift
struct ReduceMotionModifier: ViewModifier {
    @Environment(\\.accessibilityReduceMotion) var reduceMotion
    // if reduceMotion: use .opacity transition with 0.2s animation
    // else: use .slide + .opacity combined transition with 0.25s spring animation
}
```

Show complete usage wrapping the DashboardView chart animation and the
TripListView skeleton loading animation.

---

### 8.9 VoiceOver Focus Management

Produce an AccessibilityFocusManager helper:
- Uses @AccessibilityFocusState to move focus after async data loads
- Implementation for DashboardView: after KPI cards load, move focus to first KPI card
- Implementation for TripDetailView: after biometric succeeds, move focus to trip date field
- Implementation for error states: move focus to error message when it appears

---

Output the complete Section 8 as well-formatted markdown with working Swift code.
Every modifier listed must appear in the actual code. No screen may be summarized.
""",
        expected_output="Complete Section 8 accessibility implementation with working Swift code for all 6 screens.",
        agent=ios_dev
    )

    crew = Crew(
        agents=[ios_dev],
        tasks=[a11y_task],
        process=Process.sequential,
        verbose=True
    )

    print(f"\n♿ iOS Accessibility Specialist producing Section 8...\n")
    result = crew.kickoff()

    a11y_path = iir_path.replace("_IIR.md", "_IIR_A11Y.md")
    with open(a11y_path, "w") as f:
        f.write(str(result))

    # Append to IIR
    with open(iir_path, "a") as f:
        f.write("\n\n---\n\n# IIR ACCESSIBILITY PATCH — Section 8 Complete\n\n")
        f.write(str(result))

    print(f"\n💾 Accessibility patch saved: {a11y_path}")
    print(f"💾 IIR updated: {iir_path}")

    context["artifacts"].append({
        "name": "iOS Accessibility Patch",
        "type": "IIR_A11Y",
        "path": a11y_path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "iOS Accessibility Specialist"
    })
    log_event(context, "IIR_A11Y_COMPLETE", a11y_path)
    save_context(context)

    return context, a11y_path


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
    context, a11y_path = run_accessibility_patch(context, iir_path)

    print(f"\n✅ Accessibility patch complete.")
    print(f"📄 Patch: {a11y_path}")
    with open(a11y_path) as f:
        print(f.read(500))
