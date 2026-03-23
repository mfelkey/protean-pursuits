import sys
sys.path.insert(0, "/home/mfelkey/dev-team")

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from agents.orchestrator.orchestrator import log_event, save_context

load_dotenv("config/.env")

def build_mobile_devops_engineer() -> Agent:
    llm = LLM(
        model=os.getenv("TIER2_MODEL", "ollama/qwen3-coder:30b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    return Agent(
        role="Mobile DevOps Engineer",
        goal=(
            "Design and implement the complete mobile CI/CD pipeline, code signing "
            "infrastructure, OTA update strategy, and release automation that takes "
            "the React Native (Expo) application from source code to the App Store "
            "and Google Play reliably, securely, and repeatably."
        ),
        backstory=(
            "You are a Senior Mobile DevOps Engineer with 10 years of experience "
            "building and operating mobile delivery pipelines for enterprise and "
            "healthcare applications. You have deep expertise in EAS Build, Fastlane, "
            "GitHub Actions, and mobile-specific infrastructure concerns like code "
            "signing, provisioning profiles, and OTA updates. "
            "You have shipped dozens of apps through both the App Store and Google Play "
            "review processes and understand the compliance, security, and automation "
            "requirements for each platform. "
            "You are fluent in: Bash and TypeScript for scripting; GitHub Actions for "
            "CI/CD; EAS Build and Fastlane for build automation; Sentry for crash "
            "reporting; and expo-updates for OTA delivery. You understand iOS and "
            "Android code signing at a deep level — provisioning profiles, distribution "
            "certificates, upload keystores, and Play App Signing. "
            "You believe mobile releases should be fully automated — from PR merge "
            "through store submission — with human gates only at promotion checkpoints. "
            "You work from the Technical Implementation Plan, the React Native "
            "Developer's implementation guide, and the Security Review Report. You "
            "take the SRR findings seriously — every CRITICAL and HIGH finding that "
            "has a mobile infrastructure or pipeline component gets addressed in your "
            "implementation. "
            "You produce a Mobile DevOps Implementation Report (MDIR) that gives the "
            "mobile team everything they need to build, test, sign, and deploy the "
            "app — from local dev builds through production store releases. "
            "Nothing ships to the stores without passing your pipeline."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_mobile_devops_implementation(context: dict, tip_path: str, rn_guide_path: str, srr_path: str) -> dict:
    """
    Reads TIP, RN Developer guide, and SRR and produces a Mobile DevOps
    Implementation Report (MDIR).
    Returns updated context.
    """

    with open(tip_path) as f:
        tip_content = f.read()[:1500]

    with open(rn_guide_path) as f:
        rn_content = f.read()[:3000]

    with open(srr_path) as f:
        srr_content = f.read()[:1500]

    mde = build_mobile_devops_engineer()

    mdir_task = Task(
        description=f"""
You are the Mobile DevOps Engineer for the following project. Using the documents
below, produce a complete Mobile DevOps Implementation Report (MDIR) with working
configuration files and scripts for all mobile pipeline and infrastructure components.

--- Technical Implementation Plan (excerpt) ---
{tip_content}

--- React Native Implementation Guide (excerpt) ---
{rn_content}

--- Security Review Report (excerpt) ---
{srr_content}

Produce a complete Mobile DevOps Implementation Report (MDIR) with ALL of the
following sections:

1. LOCAL DEVELOPMENT ENVIRONMENT
   - Expo Dev Client setup for local builds
   - .env.example with all required mobile variables
   - package.json scripts for common developer commands
     (dev, build:dev, build:preview, build:prod, test, lint, typecheck)
   - First-time mobile setup instructions (step by step)
   - Simulator/emulator configuration for iOS and Android

2. EAS BUILD CONFIGURATION
   - Complete eas.json with dev, preview, and production profiles
   - Build-specific environment variables per profile
   - app.config.ts with dynamic environment switching
   - Version and build number auto-increment strategy
   - Custom native module configuration
   - Build caching strategies for faster CI
   - Pre-install and post-install hooks

3. CODE SIGNING & CERTIFICATES
   - iOS: provisioning profiles, distribution certificates,
     App Store Connect API key setup
   - Android: upload keystore generation, Google Play service account JSON
   - EAS managed credentials vs manual signing
   - Certificate renewal and expiration monitoring
   - Team credential sharing procedures
   - Secrets storage (never in repo — EAS Secrets + GitHub Secrets)

4. CI/CD PIPELINE (GitHub Actions)
   - Complete workflow: .github/workflows/mobile-ci.yml
     * Triggers (push to main, PR to main)
     * Jobs: typecheck, lint, test, build-ios, build-android
   - Complete workflow: .github/workflows/mobile-cd.yml
     * Staging: auto-submit to TestFlight + internal track on merge to main
     * Production: manual approval gate, then submit to both stores
     * Rollback: OTA revert or expedited binary rebuild
   - Caching: node_modules, EAS build cache, Gradle/CocoaPods cache
   - Conditional builds: skip iOS when only Android files change and vice versa
   - Slack/Teams notifications on build success/failure
   - Concurrency controls to prevent duplicate builds
   - Branch protection rules for mobile release branches

5. OTA UPDATES (expo-updates)
   - Channel configuration: development, staging, production
   - Runtime version pinning and compatibility matrix
   - expo-updates integration in app.config.ts
   - Update publishing commands per channel
   - Phased rollout strategy (percentage-based)
   - Rollback procedure for bad OTA pushes
   - Monitoring OTA adoption rates and error rates
   - When to OTA vs when to binary release (decision tree)

6. APP STORE & PLAY STORE AUTOMATION
   - Fastlane setup for both platforms
     * Fastfile with lanes: beta, release, screenshots
     * Appfile and Matchfile configuration
   - Metadata management: screenshots, descriptions, changelogs
   - Automated submission: fastlane deliver (iOS) / supply (Android)
   - TestFlight and Google Play internal testing track management
   - Release promotion pipeline: internal → beta → production
   - App Store review guidelines compliance checklist
   - Google Play policy compliance checklist

7. MONITORING & CRASH REPORTING
   - Sentry integration for React Native (sentry-expo)
   - Source map and dSYM upload in CI pipeline
   - Performance monitoring: app start time, screen render time, API latency
   - Release health dashboard: crash-free rate, ANRs, session tracking
   - Alert rules: crash spike, error rate threshold, new error detection
   - User feedback and breadcrumb configuration
   - Addressing relevant security findings from the SRR

8. RELEASE RUNBOOK
   - Pre-release checklist
     (all tests green, staging verified, changelog written, screenshots updated)
   - Standard release process: tag → EAS build → store submit → monitor
   - Hotfix process: expedited path for critical bugs (OTA or binary)
   - Rollback decision tree: OTA revert vs full binary rebuild
   - Post-release monitoring window (24h) and success criteria
   - Version deprecation and forced update strategy (minimum version enforcement)
   - Incident response for store rejection or review hold

Output the complete MDIR as well-formatted markdown with working configuration files.
All security findings from the SRR that apply to mobile must be addressed explicitly.
""",
        expected_output="A complete Mobile DevOps Implementation Report with working CI/CD and infrastructure code.",
        agent=mde
    )

    crew = Crew(
        agents=[mde],
        tasks=[mdir_task],
        process=Process.sequential,
        verbose=True
    )

    print(f"\n🚀 Mobile DevOps Engineer implementing CI/CD and release pipeline...\n")
    result = crew.kickoff()

    os.makedirs("dev/build", exist_ok=True)
    mdir_path = f"dev/build/{context['project_id']}_MDIR.md"
    with open(mdir_path, "w") as f:
        f.write(str(result))

    print(f"\n💾 Mobile DevOps Implementation Report saved: {mdir_path}")

    context["artifacts"].append({
        "name": "Mobile DevOps Implementation Report",
        "type": "MDIR",
        "path": mdir_path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "Mobile DevOps Engineer"
    })
    context["status"] = "MOBILE_DEVOPS_COMPLETE"
    log_event(context, "MOBILE_DEVOPS_COMPLETE", mdir_path)
    save_context(context)

    return context, mdir_path


if __name__ == "__main__":
    import glob

    logs = sorted(glob.glob("logs/PROJ-*.json"), key=os.path.getmtime, reverse=True)
    if not logs:
        print("No project context found.")
        exit(1)

    with open(logs[0]) as f:
        context = json.load(f)

    tip_path = rn_guide_path = srr_path = None
    for artifact in context.get("artifacts", []):
        if artifact.get("type") == "TIP":
            tip_path = artifact["path"]
        if artifact.get("type") in ("RN_GUIDE", "RN_COMBINED"):
            rn_guide_path = artifact["path"]
        if artifact.get("type") == "SRR":
            srr_path = artifact["path"]

    if not all([tip_path, rn_guide_path, srr_path]):
        missing = []
        if not tip_path: missing.append("TIP")
        if not rn_guide_path: missing.append("RN_GUIDE / RN_COMBINED")
        if not srr_path: missing.append("SRR")
        print(f"Missing upstream artifacts: {', '.join(missing)}")
        exit(1)

    print(f"📂 Loaded context: {logs[0]}")
    context, mdir_path = run_mobile_devops_implementation(context, tip_path, rn_guide_path, srr_path)

    print(f"\n✅ Mobile DevOps implementation complete.")
    print(f"📄 MDIR: {mdir_path}")
    print(f"\nFirst 500 chars:")
    with open(mdir_path) as f:
        print(f.read(500))
