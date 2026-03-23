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


def build_accessibility_specialist() -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/qwen2.5:72b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    return Agent(
        role="Accessibility Specialist",
        goal=(
            "Perform a comprehensive accessibility audit of all built code — web, "
            "mobile, and desktop — ensuring WCAG 2.2 AA compliance and platform-native "
            "assistive technology support. Produce specific, code-level remediation."
        ),
        backstory=(
            "You are a Principal Accessibility Engineer with 12 years of experience "
            "making software usable by everyone. You have conducted hundreds of "
            "accessibility audits for government agencies (Section 508), healthcare "
            "systems (ADA/HIPAA), financial services, and consumer products. You have "
            "personally used screen readers (VoiceOver, TalkBack, NVDA, JAWS), switch "
            "control, voice control, and magnification to test software. "
            "\n\n"
            "You understand accessibility is not a checklist — it is a user experience. "
            "A screen reader user should have the same quality of experience as a "
            "sighted mouse user. Your audit goes beyond automated tools to catch "
            "issues that only manual review reveals. "
            "\n\n"
            "YOUR AUDIT COVERS: "
            "\n\n"
            "1. PERCEIVABLE (WCAG 2.2 Principle 1) "
            "- Text alternatives: Every non-text element (img, icon, chart, video) "
            "  has meaningful alt text. Decorative images have empty alt or role=presentation. "
            "- Time-based media: Captions, transcripts, audio descriptions where applicable. "
            "- Adaptable: Content structure uses semantic HTML (headings, landmarks, lists, "
            "  tables with headers). Information is not conveyed by color alone. "
            "- Distinguishable: Color contrast ≥ 4.5:1 for normal text, ≥ 3:1 for large text. "
            "  Text resizable to 200% without loss. Content reflows at 320px width. "
            "\n\n"
            "2. OPERABLE (WCAG 2.2 Principle 2) "
            "- Keyboard accessible: Every interactive element reachable and operable by "
            "  keyboard alone. Visible focus indicators. No keyboard traps. "
            "  Skip navigation links present. Tab order is logical. "
            "- Enough time: Timeouts adjustable or warned. Auto-playing content controllable. "
            "- Seizures: No content that flashes more than 3 times per second. "
            "- Navigable: Page titles descriptive. Focus order meaningful. Link purpose clear. "
            "  Multiple ways to find pages. Headings and labels descriptive. "
            "- Input modalities: Touch targets ≥ 44x44px. Dragging has alternatives. "
            "  No motion-only activation. "
            "\n\n"
            "3. UNDERSTANDABLE (WCAG 2.2 Principle 3) "
            "- Readable: Language of page declared. Abbreviations expanded. "
            "- Predictable: Navigation consistent. Components behave consistently. "
            "  No unexpected context changes. "
            "- Input assistance: Error identification specific and descriptive. "
            "  Labels present for all inputs. Error prevention for important actions "
            "  (confirm, undo, review). "
            "\n\n"
            "4. ROBUST (WCAG 2.2 Principle 4) "
            "- Compatible: Valid HTML/ARIA. Name, role, value programmatically determined. "
            "  Status messages announced without focus change (aria-live). "
            "  ARIA roles, states, and properties used correctly (no misuse). "
            "\n\n"
            "5. PLATFORM-SPECIFIC CHECKS "
            "iOS: "
            "- VoiceOver: accessibilityLabel, accessibilityHint, accessibilityTraits "
            "- Dynamic Type support (all text scales with system setting) "
            "- Reduce Motion support (disable animations when enabled) "
            "- Switch Control and Voice Control compatibility "
            "- Smart Invert color support "
            "\n"
            "Android: "
            "- TalkBack: contentDescription, importantForAccessibility, live regions "
            "- Font scaling support "
            "- Reduce Animations support "
            "- Switch Access compatibility "
            "- High contrast text support "
            "\n"
            "React Native: "
            "- accessible prop, accessibilityLabel, accessibilityRole "
            "- accessibilityState (disabled, selected, checked, expanded) "
            "- accessibilityLiveRegion for dynamic content "
            "- Platform-specific a11y prop mapping "
            "\n"
            "Desktop (Electron/Tauri): "
            "- Screen reader compatibility (NVDA, JAWS, VoiceOver) "
            "- Keyboard navigation for all controls including custom widgets "
            "- High contrast mode support "
            "- Zoom/magnification support "
            "- Focus management across windows and dialogs "
            "\n\n"
            "6. AUTOMATED TEST COVERAGE "
            "- axe-core rules coverage for web "
            "- Accessibility test file review (do tests exist? what do they cover?) "
            "- CI integration (accessibility tests block merge?) "
            "\n\n"
            "For every finding: "
            "1. WCAG criterion: e.g., 1.1.1 Non-text Content "
            "2. Level: A / AA / AAA "
            "3. Severity: CRITICAL / HIGH / MEDIUM / LOW "
            "4. Platform: Web / iOS / Android / RN / Desktop / All "
            "5. File and line/component reference "
            "6. Current state (what's wrong) "
            "7. Required state (what WCAG requires) "
            "8. Remediation (specific code fix) "
            "9. Impact (which users are affected and how) "
            "\n\n"
            "Your Accessibility Audit Report (AAR) concludes with: "
            "- 🟢 ACCESSIBLE — No CRITICAL/HIGH findings. WCAG 2.2 AA compliant. "
            "- 🟡 PARTIALLY ACCESSIBLE — HIGH findings with clear remediation. "
            "- 🔴 NOT ACCESSIBLE — CRITICAL gaps. Users with disabilities cannot use the system. "
            "\n\n"
            "OUTPUT DISCIPLINE: Write the complete report. Do not repeat sections. "
            "Do not loop. Stop after the overall rating."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_accessibility_audit(context: dict, uxd_path: str = None,
                             fir_path: str = None, bir_path: str = None,
                             iir_path: str = None, air_path: str = None,
                             rn_guide_path: str = None,
                             dskr_path: str = None) -> tuple:
    """Run accessibility audit against all built artifacts."""
    specialist = build_accessibility_specialist()

    uxd_excerpt = ""
    if uxd_path and os.path.exists(uxd_path):
        with open(uxd_path) as f:
            uxd_excerpt = f.read()[:4000]

    fir_excerpt = ""
    if fir_path and os.path.exists(fir_path):
        with open(fir_path) as f:
            fir_excerpt = f.read()[:6000]

    bir_excerpt = ""
    if bir_path and os.path.exists(bir_path):
        with open(bir_path) as f:
            bir_excerpt = f.read()[:3000]

    iir_excerpt = ""
    if iir_path and os.path.exists(iir_path):
        with open(iir_path) as f:
            iir_excerpt = f.read()[:5000]

    air_excerpt = ""
    if air_path and os.path.exists(air_path):
        with open(air_path) as f:
            air_excerpt = f.read()[:5000]

    rn_excerpt = ""
    if rn_guide_path and os.path.exists(rn_guide_path):
        with open(rn_guide_path) as f:
            rn_excerpt = f.read()[:5000]

    dskr_excerpt = ""
    if dskr_path and os.path.exists(dskr_path):
        with open(dskr_path) as f:
            dskr_excerpt = f.read()[:5000]

    task = Task(
        description=f"""
Perform a comprehensive accessibility audit of all built code. Evaluate against
WCAG 2.2 AA and platform-native assistive technology requirements.

=== USER EXPERIENCE DOCUMENT (UXD) ===
{uxd_excerpt if uxd_excerpt else "(No UXD)"}

=== FRONTEND IMPLEMENTATION REPORT (FIR) ===
{fir_excerpt if fir_excerpt else "(No FIR — no web frontend)"}

=== BACKEND IMPLEMENTATION REPORT (BIR) — API error responses ===
{bir_excerpt if bir_excerpt else "(No BIR)"}

=== iOS IMPLEMENTATION REPORT (IIR) ===
{iir_excerpt if iir_excerpt else "(No IIR — no iOS app)"}

=== ANDROID IMPLEMENTATION REPORT (AIR) ===
{air_excerpt if air_excerpt else "(No AIR — no Android app)"}

=== REACT NATIVE GUIDE ===
{rn_excerpt if rn_excerpt else "(No RN — no React Native app)"}

=== DESKTOP IMPLEMENTATION REPORT (DSKR) ===
{dskr_excerpt if dskr_excerpt else "(No DSKR — no desktop app)"}

=== YOUR ACCESSIBILITY AUDIT REPORT (AAR) MUST INCLUDE ===

1. EXECUTIVE SUMMARY
   - Overall rating: 🟢 ACCESSIBLE / 🟡 PARTIALLY ACCESSIBLE / 🔴 NOT ACCESSIBLE
   - Per-platform rating
   - Findings by WCAG principle and severity
   - Affected user populations

2. PERCEIVABLE AUDIT (WCAG Principle 1)
   - Text alternatives for non-text content
   - Adaptable content structure (semantic HTML, landmarks)
   - Color contrast analysis
   - Text resizing and reflow
   - Findings per platform with code references

3. OPERABLE AUDIT (WCAG Principle 2)
   - Keyboard accessibility (tab order, focus indicators, no traps)
   - Touch targets (≥ 44x44px)
   - Time-based content handling
   - Navigation patterns
   - Findings per platform with code references

4. UNDERSTANDABLE AUDIT (WCAG Principle 3)
   - Language declaration
   - Error handling and input assistance
   - Predictable behavior
   - Findings per platform with code references

5. ROBUST AUDIT (WCAG Principle 4)
   - Valid HTML and ARIA usage
   - Programmatic name/role/value
   - Status message announcements
   - Findings per platform with code references

6. PLATFORM-SPECIFIC AUDIT
   a. Web — semantic structure, ARIA, axe-core coverage
   b. iOS — VoiceOver, Dynamic Type, Reduce Motion, Switch Control
   c. Android — TalkBack, contentDescription, font scaling
   d. React Native — accessible prop, a11y labels/roles/states
   e. Desktop — screen reader, keyboard nav, high contrast, zoom

7. AUTOMATED TEST COVERAGE REVIEW
   - Existing a11y test files and what they cover
   - Gaps in automated a11y testing
   - CI integration assessment

8. COMPLETE FINDINGS TABLE
   | # | WCAG | Level | Severity | Platform | Component | Issue | Fix | Impact |

9. REMEDIATION ROADMAP
   - Priority 1 (CRITICAL — blocks launch, users cannot access core features)
   - Priority 2 (HIGH — significant barriers, workarounds may exist)
   - Priority 3 (MEDIUM — degraded experience but usable)

10. OVERALL RATING
    - Web: 🟢/🟡/🔴
    - iOS: 🟢/🟡/🔴
    - Android: 🟢/🟡/🔴
    - React Native: 🟢/🟡/🔴
    - Desktop: 🟢/🟡/🔴
    - OVERALL: 🟢 ACCESSIBLE / 🟡 PARTIALLY ACCESSIBLE / 🔴 NOT ACCESSIBLE

No placeholders. Every finding must reference specific code and include
a concrete fix. This audit must be thorough enough to satisfy Section 508
compliance review.
""",
        expected_output=(
            "A complete Accessibility Audit Report (AAR) with per-platform findings, "
            "WCAG criterion references, remediation roadmap, and 🟢/🟡/🔴 rating."
        ),
        agent=specialist
    )

    crew = Crew(
        agents=[specialist],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )

    print("\n♿ Accessibility Specialist auditing all platforms...\n")
    result = crew.kickoff()

    os.makedirs("/home/mfelkey/dev-team/dev/accessibility", exist_ok=True)
    aar_path = f"/home/mfelkey/dev-team/dev/accessibility/{context['project_id']}_AAR.md"
    with open(aar_path, "w") as f:
        f.write(str(result))

    print(f"\n💾 Accessibility Audit Report saved: {aar_path}")

    context["artifacts"].append({
        "name": "Accessibility Audit Report",
        "type": "AAR",
        "path": aar_path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "Accessibility Specialist"
    })
    log_event(context, "AAR_COMPLETE", aar_path)
    save_context(context)
    return context, aar_path


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

    uxd_path = fir_path = bir_path = None
    iir_path = air_path = rn_guide_path = dskr_path = None
    for artifact in context.get("artifacts", []):
        atype = artifact.get("type", "")
        if atype == "UXD": uxd_path = artifact["path"]
        elif atype == "FIR": fir_path = artifact["path"]
        elif atype == "BIR": bir_path = artifact["path"]
        elif atype == "IIR": iir_path = artifact["path"]
        elif atype == "AIR": air_path = artifact["path"]
        elif atype in ("RN_GUIDE", "RNIR"): rn_guide_path = artifact["path"]
        elif atype == "DSKR": dskr_path = artifact["path"]

    if not (fir_path or iir_path or air_path or rn_guide_path or dskr_path):
        print("No built UI artifacts found. Run build agents first.")
        exit(1)

    print(f"📂 Loaded context: {logs[0]}")
    print(f"🎨 UXD: {uxd_path or 'N/A'}")
    print(f"🖥️  FIR: {fir_path or 'N/A'}")
    print(f"🍎 IIR: {iir_path or 'N/A'}")
    print(f"🤖 AIR: {air_path or 'N/A'}")
    print(f"⚛️  RN:  {rn_guide_path or 'N/A'}")
    print(f"💻 DSKR: {dskr_path or 'N/A'}")

    context, aar_path = run_accessibility_audit(
        context, uxd_path, fir_path, bir_path,
        iir_path, air_path, rn_guide_path, dskr_path
    )
    print(f"\n✅ Accessibility audit complete: {aar_path}")
    with open(aar_path) as f:
        print(f.read()[:500])
