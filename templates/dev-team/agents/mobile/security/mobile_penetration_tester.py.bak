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


def build_mobile_penetration_tester() -> Agent:
    llm = LLM(
        model=os.getenv("TIER2_MODEL", "ollama/qwen2.5-coder:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    return Agent(
        role="Mobile Penetration Tester",
        goal=(
            "Perform static security analysis of all mobile code artifacts "
            "against the OWASP Mobile Top 10 and the SRR threat model. Identify "
            "platform-specific vulnerabilities across iOS, Android, and React Native."
        ),
        backstory=(
            "You are a mobile application security specialist with 10 years of "
            "experience in iOS and Android security assessment, reverse engineering, "
            "and mobile penetration testing. You hold GPEN and eMAPT certifications. "
            "You have assessed mobile apps for federal healthcare environments "
            "handling PHI/PII under HIPAA compliance. "
            "\n\n"
            "You systematically analyze mobile code for the OWASP Mobile Top 10:\n"
            "- M1: Improper Platform Usage — misuse of iOS Keychain, Android Keystore, "
            "biometric APIs, platform permissions\n"
            "- M2: Insecure Data Storage — unencrypted local databases, plaintext "
            "SharedPreferences, insecure file permissions, backup exposure\n"
            "- M3: Insecure Communication — missing certificate pinning, cleartext "
            "traffic, weak TLS configuration\n"
            "- M4: Insecure Authentication — weak session management, biometric bypass, "
            "missing re-authentication for sensitive operations\n"
            "- M5: Insufficient Cryptography — weak algorithms, hardcoded keys, "
            "improper IV/nonce usage\n"
            "- M6: Insecure Authorization — client-side authorization checks, missing "
            "server-side validation, privilege escalation\n"
            "- M7: Client Code Quality — buffer overflows, format strings, use-after-free "
            "(native code), memory leaks\n"
            "- M8: Code Tampering — missing integrity checks, debug flags in release, "
            "no root/jailbreak detection, missing ProGuard/R8 obfuscation\n"
            "- M9: Reverse Engineering — hardcoded secrets, API keys in source, "
            "insufficient obfuscation, exposed internal endpoints\n"
            "- M10: Extraneous Functionality — test endpoints, debug logging, "
            "developer backdoors, verbose error messages\n"
            "\n\n"
            "Platform-specific checks:\n"
            "- iOS: App Transport Security, Keychain access groups, FLAG_SECURE "
            "equivalent (UIApplicationProtectedDataAvailable), Info.plist permissions\n"
            "- Android: FLAG_SECURE, Network Security Config, exported components, "
            "content provider permissions, WebView security (setJavaScriptEnabled, "
            "setAllowFileAccess)\n"
            "- React Native: Hermes bytecode exposure, bridge security, AsyncStorage "
            "vs encrypted alternatives, deep link injection\n"
            "\n\n"
            "For every finding you provide:\n"
            "1. Severity: CRITICAL / HIGH / MEDIUM / LOW / INFO\n"
            "2. Platform: iOS / Android / React Native / All\n"
            "3. Category: OWASP Mobile classification\n"
            "4. Location: File path and function/class name\n"
            "5. Evidence: The specific code pattern that is vulnerable\n"
            "6. Impact: What an attacker could achieve\n"
            "7. Remediation: Platform-specific fix with code example\n"
            "\n\n"
            "Your Mobile PTR concludes with:\n"
            "- Per-platform rating: iOS 🟢/🟡/🔴, Android 🟢/🟡/🔴, RN 🟢/🟡/🔴\n"
            "- Overall rating: 🟢 PASS / 🟡 CONDITIONAL / 🔴 FAIL\n"
            "- Any 🔴 FAIL on any platform blocks that platform's release.\n"
            "\n\n"
            "OUTPUT DISCIPLINE: Write the complete report. Do not repeat sections. "
            "Do not loop. Stop after the overall rating and remediation summary."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_mobile_penetration_test(context: dict, srr_path: str,
                                 iir_path: str, air_path: str,
                                 rn_guide_path: str, mdir_path: str) -> tuple:
    """Run the Mobile Penetration Tester against all mobile code artifacts."""
    tester = build_mobile_penetration_tester()

    # Load upstream artifacts
    srr_excerpt = ""
    if srr_path and os.path.exists(srr_path):
        with open(srr_path) as f:
            srr_excerpt = f.read()[:5000]

    iir_excerpt = ""
    if iir_path and os.path.exists(iir_path):
        with open(iir_path) as f:
            iir_excerpt = f.read()[:6000]

    air_excerpt = ""
    if air_path and os.path.exists(air_path):
        with open(air_path) as f:
            air_excerpt = f.read()[:6000]

    rn_excerpt = ""
    if rn_guide_path and os.path.exists(rn_guide_path):
        with open(rn_guide_path) as f:
            rn_excerpt = f.read()[:6000]

    mdir_excerpt = ""
    if mdir_path and os.path.exists(mdir_path):
        with open(mdir_path) as f:
            mdir_excerpt = f.read()[:4000]

    task = Task(
        description=f"""
Perform a comprehensive mobile security assessment of all mobile code artifacts.
Analyze against the OWASP Mobile Top 10 and the SRR threat model.

=== SECURITY REVIEW REPORT (THREAT MODEL) ===
{srr_excerpt}

=== iOS IMPLEMENTATION REPORT (IIR) ===
{iir_excerpt}

=== ANDROID IMPLEMENTATION REPORT (AIR) ===
{air_excerpt}

=== REACT NATIVE GUIDE (RN) ===
{rn_excerpt}

=== MOBILE DEVOPS REPORT (MDIR) ===
{mdir_excerpt}

=== YOUR MOBILE PENETRATION TEST REPORT MUST INCLUDE ===

1. EXECUTIVE SUMMARY
   - Scope: iOS, Android, React Native
   - Per-platform rating: iOS 🟢/🟡/🔴, Android 🟢/🟡/🔴, RN 🟢/🟡/🔴
   - Overall rating: 🟢 PASS / 🟡 CONDITIONAL / 🔴 FAIL
   - Finding counts by severity and platform

2. OWASP MOBILE TOP 10 ANALYSIS
   For each of M1–M10, analyze all three platforms:
   | # | Category | iOS | Android | RN | Findings |

3. iOS SECURITY ANALYSIS
   - Keychain usage and access groups
   - App Transport Security configuration
   - Data protection API usage
   - Biometric authentication implementation
   - Findings table with file:function references

4. ANDROID SECURITY ANALYSIS
   - EncryptedSharedPreferences usage
   - Network Security Config
   - FLAG_SECURE implementation
   - Exported components and content providers
   - WebView security settings
   - Findings table with file:function references

5. REACT NATIVE SECURITY ANALYSIS
   - Secure storage (not AsyncStorage for sensitive data)
   - Hermes bytecode and bundle security
   - Bridge communication security
   - Deep link validation
   - Third-party dependency risk
   - Findings table with file:function references

6. BUILD & DISTRIBUTION SECURITY
   - Code signing configuration
   - Debug vs release build separation
   - ProGuard/R8 obfuscation (Android)
   - App Store / Play Store metadata
   - CI/CD pipeline security (secrets, signing keys)

7. COMPLETE FINDINGS TABLE
   | # | Severity | Platform | Category | Location | Description | Remediation |

8. PER-PLATFORM RATING & REMEDIATION ROADMAP
   - iOS: 🟢/🟡/🔴 with justification
   - Android: 🟢/🟡/🔴 with justification
   - React Native: 🟢/🟡/🔴 with justification
   - Overall: 🟢/🟡/🔴
   - Prioritized remediation by platform

No placeholders. No TODO comments. Every finding must have a specific
file reference and concrete remediation with code example.
""",
        expected_output=(
            "A complete Mobile Penetration Test Report with per-platform "
            "OWASP Mobile Top 10 analysis, findings table, and per-platform "
            "🟢/🟡/🔴 ratings."
        ),
        agent=tester
    )

    crew = Crew(
        agents=[tester],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )

    print("\n🔓 Mobile Penetration Tester analyzing mobile code...\n")
    result = crew.kickoff()

    os.makedirs("/home/mfelkey/dev-team/dev/mobile/security", exist_ok=True)
    mptr_path = f"/home/mfelkey/dev-team/dev/mobile/security/{context['project_id']}_MOBILE_PTR.md"
    with open(mptr_path, "w") as f:
        f.write(str(result))

    print(f"\n💾 Mobile Penetration Test Report saved: {mptr_path}")

    context["artifacts"].append({
        "name": "Mobile Penetration Test Report",
        "type": "MOBILE_PTR",
        "path": mptr_path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "Mobile Penetration Tester"
    })
    log_event(context, "MOBILE_PTR_COMPLETE", mptr_path)
    save_context(context)
    return context, mptr_path


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

    srr_path = iir_path = air_path = rn_guide_path = mdir_path = None
    for artifact in context.get("artifacts", []):
        atype = artifact.get("type", "")
        if atype == "SRR": srr_path = artifact["path"]
        elif atype == "IIR": iir_path = artifact["path"]
        elif atype == "AIR": air_path = artifact["path"]
        elif atype in ("RN_GUIDE", "RNIR"): rn_guide_path = artifact["path"]
        elif atype == "MDIR": mdir_path = artifact["path"]

    if not (iir_path or air_path or rn_guide_path):
        print("No mobile artifacts found. Run mobile build agents first.")
        exit(1)

    print(f"📂 Loaded context: {logs[0]}")
    print(f"🔒 SRR: {srr_path or 'NOT FOUND'}")
    print(f"🍎 IIR: {iir_path or 'NOT FOUND'}")
    print(f"🤖 AIR: {air_path or 'NOT FOUND'}")
    print(f"⚛️  RN:  {rn_guide_path or 'NOT FOUND'}")
    print(f"📦 MDIR: {mdir_path or 'NOT FOUND'}")

    context, mptr_path = run_mobile_penetration_test(
        context, srr_path, iir_path, air_path, rn_guide_path, mdir_path
    )
    print(f"\n✅ Mobile Penetration Test complete: {mptr_path}")
    with open(mptr_path) as f:
        print(f.read()[:500])
