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


def build_desktop_developer() -> Agent:
    llm = LLM(
        model=os.getenv("TIER2_MODEL", "ollama/qwen2.5-coder:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    return Agent(
        role="Desktop Application Developer",
        goal=(
            "Design and implement a cross-platform desktop application using the "
            "optimal framework for the project requirements — Electron for web-tech "
            "heavy apps or Tauri for performance-critical, security-sensitive apps — "
            "producing production-ready code with native OS integration."
        ),
        backstory=(
            "You are a Senior Desktop Application Engineer with 12 years of experience "
            "building cross-platform desktop applications. You are expert in both major "
            "frameworks and know exactly when to use each: "
            "\n\n"
            "ELECTRON (Chromium + Node.js): "
            "- Best when: the project already has a web frontend (React/Vue/Svelte), "
            "  needs rich web ecosystem libraries, requires heavy DOM manipulation, "
            "  or team expertise is primarily JavaScript/TypeScript. "
            "- You know: main process / renderer process architecture, IPC patterns, "
            "  electron-builder and electron-forge for packaging, auto-update via "
            "  electron-updater, native module integration with node-gyp, context "
            "  isolation and preload scripts for security, Electron Forge with Vite "
            "  for fast builds, tray icons, system notifications, deep linking, "
            "  protocol handlers, and platform-specific menu/shortcut patterns. "
            "- You enforce: context isolation ON, nodeIntegration OFF, sandbox ON, "
            "  CSP headers, no remote module, preload-only IPC bridge. "
            "\n\n"
            "TAURI (Rust + WebView): "
            "- Best when: binary size matters (Tauri ships 3-10MB vs Electron's 150MB+), "
            "  performance is critical (Rust backend, native WebView), security is "
            "  paramount (Rust memory safety, smaller attack surface), or the app "
            "  needs low resource usage (no bundled Chromium). "
            "- You know: Tauri command system (Rust functions callable from JS), "
            "  event system, window management, system tray, file system access "
            "  through scoped permissions, tauri-plugin ecosystem, sidecar binaries, "
            "  updater plugin, SQLite via tauri-plugin-sql, Tauri v2 mobile support. "
            "- You enforce: strict allowlist configuration, scoped FS access, "
            "  capability-based permissions, CSP headers, no eval(). "
            "\n\n"
            "FRAMEWORK DECISION CRITERIA — you evaluate: "
            "1. Does a web frontend already exist? → Electron (reuse it) "
            "2. Is binary size critical (< 20MB)? → Tauri "
            "3. Is the app CPU/memory intensive? → Tauri (Rust backend) "
            "4. Does the app need heavy native OS integration? → Tauri (Rust FFI) "
            "5. Is the team JS/TS only with no Rust experience? → Electron "
            "6. Is security the primary concern? → Tauri (smaller surface) "
            "7. Does the app need a plugin ecosystem? → Either (both have good ones) "
            "You document your framework choice with a decision table showing how "
            "each criterion was evaluated. "
            "\n\n"
            "CROSS-PLATFORM REQUIREMENTS — for both frameworks you ensure: "
            "- Windows, macOS, and Linux builds from a single codebase "
            "- Native look and feel per platform (title bar, menus, file dialogs) "
            "- Code signing configuration for all three platforms "
            "- Auto-update mechanism with rollback "
            "- Crash reporting "
            "- Deep linking / protocol handler registration "
            "- Proper app lifecycle (single instance, graceful shutdown) "
            "- System tray integration where appropriate "
            "- Native file associations if applicable "
            "- Accessibility: keyboard navigation, screen reader support, "
            "  high contrast mode, reduced motion respect "
            "- Offline capability where applicable "
            "- Secure local storage (OS keychain for secrets, encrypted SQLite for data) "
            "\n\n"
            "PACKAGING & DISTRIBUTION — you configure: "
            "- CI/CD for all three platforms (GitHub Actions matrix builds) "
            "- Signed installers: .msi/.exe (Windows), .dmg/.app (macOS), "
            "  .deb/.rpm/.AppImage (Linux) "
            "- Auto-update server or GitHub Releases integration "
            "- Delta updates where framework supports it "
            "\n\n"
            "You produce a Desktop Implementation Report (DSKR) that includes: "
            "framework decision rationale, project structure, IPC/command architecture, "
            "window management design, complete implementation code for all components, "
            "platform-specific configuration, packaging config, auto-update setup, "
            "and security hardening checklist. "
            "\n\n"
            "OUTPUT DISCIPLINE: Write the complete report. No placeholders. "
            "No TODO comments. Every function complete. Do not repeat sections. "
            "Do not loop. Stop after the packaging and distribution section."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_desktop_implementation(context: dict, uxd_path: str,
                                tad_path: str, tip_path: str,
                                bir_path: str = None,
                                fir_path: str = None) -> tuple:
    """Run the Desktop Developer against upstream artifacts."""
    developer = build_desktop_developer()
    # ── Smart extraction: load relevant sections for desktop_dev ──
    ctx = load_agent_context(
        context=context,
        consumer="desktop_dev",
        artifact_types=["UXD", "TAD", "TIP", "BIR", "FIR"],
        max_chars_per_artifact=6000
    )
    prompt_context = format_context_for_prompt(ctx)


    task = Task(
        description=f"""
You are the Desktop Application Developer. Using the upstream artifacts below,
design and implement a cross-platform desktop application.

First, evaluate the framework decision (Electron vs Tauri) based on the project
requirements. Document your decision with a criteria table.

Then implement the complete desktop application.

=== UPSTREAM CONTEXT ===
{prompt_context}


=== BACKEND IMPLEMENTATION REPORT (BIR) ===
{bir_excerpt if bir_excerpt else "(No BIR available — desktop app may be standalone)"}

=== FRONTEND IMPLEMENTATION REPORT (FIR) ===
{fir_excerpt if fir_excerpt else "(No FIR available — desktop app may not share web frontend)"}

=== YOUR DESKTOP IMPLEMENTATION REPORT (DSKR) MUST INCLUDE ===

1. FRAMEWORK DECISION
   - Criteria evaluation table (Electron vs Tauri for each criterion)
   - Final decision with rationale
   - Risk factors and mitigations

2. PROJECT STRUCTURE
   - Complete directory layout
   - Key configuration files (package.json/Cargo.toml, framework config)
   - Dependency list with versions and justifications

3. ARCHITECTURE
   - Main process / renderer (Electron) or Rust backend / WebView (Tauri)
   - IPC / command architecture (every message/command documented)
   - Window management (main window, secondary windows, dialogs)
   - State management approach
   - Data flow diagrams

4. IMPLEMENTATION — BACKEND / MAIN PROCESS
   - Complete code for all IPC handlers / Tauri commands
   - Database integration (if applicable)
   - File system operations
   - System tray implementation
   - Native OS integration (notifications, file associations, protocol handlers)
   - Background tasks / workers

5. IMPLEMENTATION — FRONTEND / RENDERER
   - Complete UI code for all screens from the UXD
   - Component architecture
   - State management implementation
   - IPC client / Tauri invoke calls
   - Theming (light/dark mode, platform-adaptive)

6. SECURITY HARDENING
   - Electron: context isolation, sandbox, CSP, preload scripts
   - Tauri: allowlist, scoped permissions, CSP
   - Secure storage (OS keychain integration)
   - Input validation on IPC boundary

7. PLATFORM-SPECIFIC CONFIGURATION
   - Windows: installer config, registry entries, Start Menu
   - macOS: Info.plist, entitlements, Dock integration, notarization
   - Linux: .desktop file, icon paths, package metadata

8. PACKAGING & DISTRIBUTION
   - CI/CD pipeline (GitHub Actions matrix for Win/Mac/Linux)
   - Code signing configuration per platform
   - Auto-update implementation
   - Installer configuration

9. ACCESSIBILITY
   - Keyboard navigation map
   - Screen reader support
   - High contrast / reduced motion
   - Focus management

No placeholders. No TODO comments. Every function must be complete and working.
""",
        expected_output=(
            "A complete Desktop Implementation Report (DSKR) with framework "
            "decision, full implementation code, platform configs, and packaging."
        ),
        agent=developer
    )

    crew = Crew(
        agents=[developer],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )

    print("\n🖥️  Desktop Developer building cross-platform application...\n")
    result = crew.kickoff()

    os.makedirs("/home/mfelkey/dev-team/dev/desktop", exist_ok=True)
    dskr_path = f"/home/mfelkey/dev-team/dev/desktop/{context['project_id']}_DSKR.md"
    with open(dskr_path, "w") as f:
        f.write(str(result))

    print(f"\n💾 Desktop Implementation Report saved: {dskr_path}")

    context["artifacts"].append({
        "name": "Desktop Implementation Report",
        "type": "DSKR",
        "path": dskr_path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "Desktop Application Developer"
    })
    on_artifact_saved(context, "DSKR", dskr_path)
    log_event(context, "DSKR_COMPLETE", dskr_path)
    save_context(context)
    return context, dskr_path


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

    uxd_path = tad_path = tip_path = bir_path = fir_path = None
    for artifact in context.get("artifacts", []):
        atype = artifact.get("type", "")
        if atype == "UXD": uxd_path = artifact["path"]
        elif atype == "TAD": tad_path = artifact["path"]
        elif atype == "TIP": tip_path = artifact["path"]
        elif atype == "BIR": bir_path = artifact["path"]
        elif atype == "FIR": fir_path = artifact["path"]

    if not tip_path:
        print("Missing TIP. Run Senior Developer first.")
        exit(1)

    print(f"📂 Loaded context: {logs[0]}")
    print(f"🎨 UXD: {uxd_path or 'NOT FOUND'}")
    print(f"🏗️  TAD: {tad_path or 'NOT FOUND'}")
    print(f"📋 TIP: {tip_path}")
    print(f"⚙️  BIR: {bir_path or '(standalone)'}")
    print(f"🖥️  FIR: {fir_path or '(standalone)'}")

    context, dskr_path = run_desktop_implementation(
        context, uxd_path, tad_path, tip_path, bir_path, fir_path
    )
    print(f"\n✅ Desktop implementation complete: {dskr_path}")
    with open(dskr_path) as f:
        print(f.read()[:500])
