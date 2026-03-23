"""
Dev-Team Mission Control — Flask Backend
=========================================
A GUI for Vibe Coders to monitor, control, and interact with the
AI agent pipeline. Phase 1: reference guide + project viewer.
Phase 2 hooks: live agent execution via subprocess.
"""

import json
import glob
import os
import subprocess
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, jsonify, request, send_from_directory

app = Flask(__name__)

# ── Configuration ──────────────────────────────────────────────
# In production, point this to ~/dev-team/logs
PROJECT_DIR = os.environ.get("DEVTEAM_PROJECT_DIR", os.path.expanduser("~/dev-team/logs"))
AGENTS_DIR = os.environ.get("DEVTEAM_AGENTS_DIR", os.path.expanduser("~/dev-team/agents"))

# ── Pipeline Definition ───────────────────────────────────────
# This is the single source of truth for agent ordering, commands,
# checkpoint locations, and metadata.

PIPELINE = {
    "web": [
        # ── Orchestration ─────────────────────────────────────
        {"id": "classify",      "name": "Orchestrator — Classify",  "phase": "orchestrate", "command": "python agents/orchestrator/classify.py",              "produces": "Project Context",  "checkpoint": False, "icon": "🎯"},
        {"id": "route",         "name": "Orchestrator — Route",     "phase": "orchestrate", "command": "python agents/orchestrator/router.py",               "produces": "Routing Decision", "checkpoint": False, "icon": "🔀"},
        # ── Planning ──────────────────────────────────────────
        {"id": "product_mgr",   "name": "Product Manager",          "phase": "plan",  "command": "python agents/dev/strategy/product_manager.py",     "produces": "PRD",             "checkpoint": True,  "icon": "📋"},
        {"id": "biz_analyst",   "name": "Business Analyst",         "phase": "plan",  "command": "python agents/dev/strategy/business_analyst.py",    "produces": "BAD",             "checkpoint": False, "icon": "📊"},
        {"id": "scrum_master",  "name": "Scrum Master",             "phase": "plan",  "command": "python agents/dev/strategy/scrum_master.py",        "produces": "Sprint Plan",     "checkpoint": False, "icon": "🏃"},
        {"id": "architect",     "name": "Technical Architect",      "phase": "plan",  "command": "python agents/dev/strategy/technical_architect.py",  "produces": "TAD",             "checkpoint": True,  "icon": "🏗️"},
        {"id": "security",      "name": "Security Reviewer",        "phase": "plan",  "command": "python agents/dev/strategy/security_reviewer.py",   "produces": "SRR",             "checkpoint": True,  "icon": "🔒"},
        {"id": "ux_designer",   "name": "UX/UI Designer",           "phase": "plan",  "command": "python agents/dev/strategy/ux_designer.py",         "produces": "UXD",             "checkpoint": False, "icon": "🎨"},
        {"id": "ux_content",    "name": "UX Content Guide",         "phase": "plan",  "command": "python agents/dev/strategy/ux_content_guide.py",    "produces": "Content Guide",   "checkpoint": True,  "icon": "✍️"},
        # ── Test Spec (TDD: tests defined before code) ────────
        {"id": "senior_dev",    "name": "Senior Developer",         "phase": "test_spec", "command": "python agents/dev/build/senior_developer.py",    "produces": "TIP",             "checkpoint": False, "icon": "👨‍💻"},
        {"id": "perf_plan",     "name": "Performance Planner",      "phase": "test_spec", "command": "python agents/dev/performance/performance_planner.py", "produces": "PBD",        "checkpoint": False, "icon": "⚡"},
        {"id": "qa_lead",       "name": "QA Lead",                  "phase": "test_spec", "command": "python agents/dev/quality/qa_lead.py",           "produces": "MTP",             "checkpoint": False, "icon": "🧪"},
        {"id": "test_auto",     "name": "Test Automation Engineer",  "phase": "test_spec", "command": "python agents/dev/quality/test_automation_engineer.py", "produces": "TAR",      "checkpoint": True,  "icon": "🤖"},
        # ── Build (code written against existing tests) ───────
        {"id": "backend_dev",   "name": "Backend Developer",        "phase": "build", "command": "python agents/dev/build/backend_developer.py",      "produces": "BIR",             "checkpoint": False, "icon": "⚙️"},
        {"id": "frontend_dev",  "name": "Frontend Developer",       "phase": "build", "command": "python agents/dev/build/frontend_developer.py",     "produces": "FIR",             "checkpoint": False, "icon": "🖥️"},
        {"id": "dba",           "name": "Database Administrator",   "phase": "build", "command": "python agents/dev/build/database_admin.py",         "produces": "DBAR",            "checkpoint": False, "icon": "🗄️"},
        {"id": "desktop_dev",   "name": "Desktop App Developer",    "phase": "build", "command": "python agents/desktop/desktop_developer.py",        "produces": "DSKR",            "checkpoint": False, "icon": "💻"},
        {"id": "devops",        "name": "DevOps Engineer",          "phase": "build", "command": "python agents/dev/build/devops_engineer.py",        "produces": "DIR",             "checkpoint": True,  "icon": "🚀"},
        {"id": "devex_writer",  "name": "DevEx Writer",             "phase": "build", "command": "python agents/docs/devex_writer.py",               "produces": "DXR",             "checkpoint": False, "icon": "📖"},
        # ── Verify (run tests against built code) ─────────────
        {"id": "pen_test",      "name": "Penetration Tester",       "phase": "verify", "command": "python agents/dev/security/penetration_tester.py",  "produces": "PTR",                 "checkpoint": True,  "icon": "🔓"},
        {"id": "scale_arch",    "name": "Scalability Architect",    "phase": "verify", "command": "python agents/dev/scalability/scalability_architect.py", "produces": "SAR",             "checkpoint": True,  "icon": "📈"},
        {"id": "perf_audit",    "name": "Performance Auditor",      "phase": "verify", "command": "python agents/dev/performance/performance_auditor.py",   "produces": "PAR",             "checkpoint": True,  "icon": "⚡"},
        {"id": "a11y_audit",    "name": "Accessibility Specialist", "phase": "verify", "command": "python agents/dev/accessibility/accessibility_specialist.py", "produces": "AAR",        "checkpoint": True,  "icon": "♿"},
        {"id": "license_scan",  "name": "License Scanner",          "phase": "verify", "command": "python agents/compliance/license_scanner.py",       "produces": "LCR",                 "checkpoint": True,  "icon": "⚖️"},
        {"id": "verify",        "name": "Test Verification",        "phase": "verify", "command": "python agents/dev/quality/test_verify.py",         "produces": "Verification Report", "checkpoint": True,  "icon": "✅"},
    ],
    "mobile": [
        # ── Mobile UX ────────────────────────────────────────
        {"id": "mobile_ux",     "name": "Mobile UX Designer",       "phase": "mobile_plan", "command": "python agents/mobile/ux/mobile_ux_designer.py",          "produces": "MUXD",       "checkpoint": False, "icon": "📱"},
        # ── Mobile Test Spec (TDD: mobile tests before code) ─
        {"id": "mobile_qa",     "name": "Mobile QA Specialist",     "phase": "mobile_test", "command": "python agents/mobile/qa/mobile_qa_specialist.py",         "produces": "Mobile Test Plan", "checkpoint": True,  "icon": "✅"},
        # ── Mobile Build (code against test specs) ───────────
        {"id": "ios_dev",       "name": "iOS Developer",            "phase": "mobile_build", "command": "python agents/mobile/ios/ios_developer.py",               "produces": "IIR",        "checkpoint": False, "icon": "🍎"},
        {"id": "android_dev",   "name": "Android Developer",        "phase": "mobile_build", "command": "python agents/mobile/android/android_developer.py",       "produces": "AIR",        "checkpoint": False, "icon": "🤖"},
        {"id": "rn_arch_p1",    "name": "RN Architect (Part 1)",    "phase": "mobile_build", "command": "python agents/mobile/rn/react_native_architect_part1.py", "produces": "RNAD P1",    "checkpoint": False, "icon": "⚛️"},
        {"id": "rn_arch_p2",    "name": "RN Architect (Part 2)",    "phase": "mobile_build", "command": "python agents/mobile/rn/react_native_architect_part2.py", "produces": "RNAD P2",    "checkpoint": False, "icon": "⚛️"},
        {"id": "rn_dev",        "name": "RN Developer",             "phase": "mobile_build", "command": "python agents/mobile/rn/react_native_developer.py",       "produces": "RN Guide",   "checkpoint": False, "icon": "⚛️"},
        {"id": "ios_patch",     "name": "iOS Developer (Patch)",    "phase": "mobile_build", "command": "python agents/mobile/ios/ios_developer_patch.py",         "produces": "IIR Patch",  "checkpoint": False, "icon": "🍎"},
        {"id": "ios_a11y",      "name": "iOS Accessibility Patch",  "phase": "mobile_build", "command": "python agents/mobile/ios/ios_accessibility_patch.py",     "produces": "IIR A11y",   "checkpoint": False, "icon": "♿"},
        {"id": "mobile_devops", "name": "Mobile DevOps Engineer",   "phase": "mobile_build", "command": "python agents/mobile/devops/mobile_devops_engineer.py",   "produces": "MDIR",       "checkpoint": False, "icon": "📦"},
        # ── Mobile Verify ─────────────────────────────────────
        {"id": "mobile_pen_test", "name": "Mobile Penetration Tester", "phase": "mobile_verify", "command": "python agents/mobile/security/mobile_penetration_tester.py", "produces": "Mobile PTR", "checkpoint": True, "icon": "🔓"},
        {"id": "mobile_scale",  "name": "Mobile Scalability Review",  "phase": "mobile_verify", "command": "python agents/mobile/scalability/mobile_scalability_review.py", "produces": "Mobile SAR", "checkpoint": True, "icon": "📈"},
        {"id": "mobile_verify", "name": "Mobile Test Verification",  "phase": "mobile_verify", "command": "python agents/mobile/qa/mobile_test_verify.py",        "produces": "Mobile Verification Report", "checkpoint": True, "icon": "✅"},
    ],
}

# Agent detail cards — for the reference guide section
AGENT_DETAILS = {
    "product_mgr":   {"tier": "T1", "model": "qwen2.5:72b",        "file": "dev/strategy/product_manager.py",     "consumes": ["Project Spec"],          "produces": "PRD",           "description": "Turns your project description into a detailed requirements document — user stories, acceptance criteria, scope boundaries."},
    "biz_analyst":   {"tier": "T1", "model": "qwen2.5:72b",        "file": "dev/strategy/business_analyst.py",    "consumes": ["PRD"],                   "produces": "BAD",           "description": "Goes deeper than the PRD. Maps stakeholders, process flows, data dictionaries. Answers every question the PRD leaves open."},
    "scrum_master":  {"tier": "T1", "model": "qwen2.5:72b",        "file": "dev/strategy/scrum_master.py",        "consumes": ["PRD", "BAD"],            "produces": "Sprint Plan",   "description": "Breaks requirements into sprints — prioritized backlog, story points, what gets built first and why."},
    "architect":     {"tier": "T1", "model": "qwen2.5:72b",        "file": "dev/strategy/technical_architect.py",  "consumes": ["PRD", "BAD", "Sprint"], "produces": "TAD",           "description": "Designs the whole system — technologies, data flows, deployment targets, component interactions."},
    "security":      {"tier": "T1", "model": "qwen2.5:72b",        "file": "dev/strategy/security_reviewer.py",   "consumes": ["PRD", "TAD"],            "produces": "SRR",           "description": "Reviews architecture for security holes, compliance gaps, privacy risks. Can block the project if rated RED."},
    "ux_designer":   {"tier": "T1", "model": "qwen2.5:72b",        "file": "dev/strategy/ux_designer.py",         "consumes": ["PRD", "BAD", "SRR"],     "produces": "UXD",           "description": "Designs every screen, interaction, and user journey. Writes all UI text — developers never make up copy."},
    "ux_content":    {"tier": "T1", "model": "qwen2.5:72b",        "file": "dev/strategy/ux_content_guide.py",    "consumes": ["UXD"],                   "produces": "Content Guide", "description": "Produces the definitive guide for every label, button, tooltip, and error message in the application."},
    "senior_dev":    {"tier": "T2", "model": "qwen2.5-coder:32b",  "file": "dev/build/senior_developer.py",       "consumes": ["PRD", "TAD", "UXD"],     "produces": "TIP",           "description": "Translates architecture into a concrete coding plan — project structure, module boundaries, coding standards, implementation order. In TDD mode, this plan also defines testable interfaces that the QA Lead and Test Automation Engineer use to write tests before implementation begins."},
    "qa_lead":       {"tier": "T1", "model": "qwen2.5:72b",        "file": "dev/quality/qa_lead.py",              "consumes": ["PRD", "TIP", "TAD", "UXD"], "produces": "MTP",       "description": "Designs the master test plan BEFORE code is written. Defines acceptance criteria, test cases, and coverage targets that build agents must satisfy. Every user story gets testable pass/fail conditions."},
    "test_auto":     {"tier": "T2", "model": "qwen2.5-coder:32b",  "file": "dev/quality/test_automation_engineer.py", "consumes": ["MTP", "TIP", "TAD"], "produces": "TAR",           "description": "Writes test code (unit stubs, API contract tests, E2E scenarios, accessibility checks) BEFORE implementation. Build agents receive these tests and must write code that passes them. Tests define the contract."},
    "perf_plan":     {"tier": "T1", "model": "qwen2.5:72b",        "file": "dev/performance/performance_planner.py", "consumes": ["TAD", "PRD", "TIP"], "produces": "PBD",           "description": "Sets concrete performance budgets BEFORE code is written: API latency targets (P50/P95/P99 per endpoint), frontend Core Web Vitals budgets, mobile cold start and memory ceilings, database query time limits, and load testing targets (concurrent users, RPS, error rate ceilings). Also defines the benchmarking suite (k6, Lighthouse, profiler scripts) that the Performance Auditor will run in verify. Every budget has a specific number, measurement method, and regression threshold."},
    "backend_dev":   {"tier": "T2", "model": "qwen2.5-coder:32b",  "file": "dev/build/backend_developer.py",      "consumes": ["TIP", "TAD", "MTP", "TAR"],  "produces": "BIR",     "description": "Builds the server side — APIs, database access, authentication, business logic. Receives pre-written test suites and must produce code that passes all test cases defined in the MTP and TAR."},
    "frontend_dev":  {"tier": "T2", "model": "qwen2.5-coder:32b",  "file": "dev/build/frontend_developer.py",     "consumes": ["TIP", "UXD", "MTP", "TAR", "Content Guide"], "produces": "FIR", "description": "Builds the user interface — pages, components, state management, API integration. Must satisfy all frontend test cases, component tests, and accessibility checks defined in the TAR."},
    "dba":           {"tier": "T2", "model": "qwen2.5-coder:32b",  "file": "dev/build/database_admin.py",         "consumes": ["BIR", "TAD", "SRR"],     "produces": "DBAR",          "description": "Reviews and optimizes the database schema — indexes, migrations, backups, capacity planning."},
    "desktop_dev":   {"tier": "T2", "model": "qwen2.5-coder:32b",  "file": "desktop/desktop_developer.py",        "consumes": ["UXD", "TAD", "TIP", "BIR", "FIR"], "produces": "DSKR", "description": "Builds cross-platform desktop app. Evaluates Electron vs Tauri based on project requirements (binary size, performance needs, security, team expertise). Produces complete implementation with IPC architecture, native OS integration (menus, tray, file associations, deep links), platform-specific packaging (MSI/DMG/AppImage), code signing, auto-update, and accessibility (screen reader, keyboard nav, high contrast). Decision table documents framework choice rationale."},
    "devops":        {"tier": "T2", "model": "qwen2.5-coder:32b",  "file": "dev/build/devops_engineer.py",        "consumes": ["TIP", "TAD", "SRR", "TAR"], "produces": "DIR",        "description": "Sets up build, test, and deploy infrastructure — Docker, CI/CD, infrastructure-as-code, secrets management. CI pipeline must run the pre-written test suite and gate deployments on test pass."},
    "devex_writer":  {"tier": "T1", "model": "qwen2.5:72b",        "file": "docs/devex_writer.py",                "consumes": ["PRD", "TAD", "BIR", "FIR", "DIR", "DSKR"], "produces": "DXR", "description": "Produces all developer-facing documentation: README.md (badges, quick start, features, config reference), complete API reference (every endpoint with curl + SDK examples, auth, pagination, errors, webhooks), 3 quickstart tutorials, CONTRIBUTING.md (dev setup, PR conventions, code style, issue templates), CHANGELOG.md (Keep a Changelog format), and deployment guide (Docker, K8s/Helm, env var reference, monitoring). Every code example is copy-pasteable. No placeholders."},
    "scale_arch":    {"tier": "T1", "model": "qwen2.5:72b",        "file": "dev/scalability/scalability_architect.py", "consumes": ["TAD", "BIR", "FIR", "DBAR", "DIR"], "produces": "SAR", "description": "Reviews the complete built system for commercial scalability across four dimensions: multi-tenant SaaS readiness (tenant isolation, data partitioning, per-tenant config), high-throughput API performance (connection pooling, caching layers, async job queues, rate limiting, 10k+ req/sec targets), large dataset handling (query optimization, read replicas, table partitioning, materialized views, pagination strategy for millions of records), and global distribution (CDN configuration, multi-region deployment, edge caching, asset optimization). Produces a Scalability Architecture Report (SAR) rated 🟢 SCALE-READY / 🟡 NEEDS WORK / 🔴 NOT SCALABLE with specific file:line remediation for every finding."},
    "pen_test":      {"tier": "T2", "model": "qwen2.5-coder:32b",  "file": "dev/security/penetration_tester.py",  "consumes": ["SRR", "BIR", "FIR", "DIR", "DBAR"], "produces": "PTR", "description": "Performs static security analysis of all built code against the SRR threat model. Probes for OWASP Top 10 vulnerabilities: SQL injection, XSS, auth bypass, IDOR, SSRF, secrets in code, misconfigured CORS, open debug endpoints, insecure deserialization, and missing rate limits. Produces a Penetration Test Report (PTR) rated 🟢 PASS / 🟡 CONDITIONAL / 🔴 FAIL with specific file:line references for every finding. 🔴 FAIL blocks release."},
    "perf_audit":    {"tier": "T2", "model": "qwen2.5-coder:32b",  "file": "dev/performance/performance_auditor.py", "consumes": ["PBD", "BIR", "FIR", "DIR", "DBAR", "DSKR"], "produces": "PAR", "description": "Audits all built code against Performance Budget Document targets. Detects N+1 queries, missing indexes, synchronous operations that should be async, unbounded queries, missing caching, bundle size violations, unoptimized images, main thread blocking, memory leaks, and missing connection pooling. Every finding references the specific PBD budget violated with expected improvement. Rated 🟢 MEETS BUDGETS / 🟡 NEEDS OPTIMIZATION / 🔴 BUDGET VIOLATION."},
    "a11y_audit":    {"tier": "T1", "model": "qwen2.5:72b",        "file": "dev/accessibility/accessibility_specialist.py", "consumes": ["UXD", "FIR", "BIR", "IIR", "AIR", "RN Guide", "DSKR"], "produces": "AAR", "description": "Dedicated WCAG 2.2 AA accessibility audit across all platforms. Evaluates Perceivable (alt text, contrast, reflow), Operable (keyboard nav, focus indicators, touch targets), Understandable (error handling, labels, predictability), and Robust (valid ARIA, programmatic name/role/value). Platform-specific checks: VoiceOver/Dynamic Type (iOS), TalkBack/font scaling (Android), a11y props (RN), screen reader/high contrast (Desktop). Rated 🟢 ACCESSIBLE / 🟡 PARTIALLY ACCESSIBLE / 🔴 NOT ACCESSIBLE. Satisfies Section 508."},
    "license_scan":  {"tier": "T1", "model": "qwen2.5:72b",        "file": "compliance/license_scanner.py",       "consumes": ["PRD", "BIR", "FIR", "DIR", "DSKR", "IIR", "AIR", "RN Guide"], "produces": "LCR", "description": "Audits project license choice and all dependency licenses for commercial open-source distribution. Scans package.json, requirements.txt, Cargo.toml, Podfile, build.gradle for every dependency. Checks license compatibility (GPL dep in MIT project = violation), copyleft infection risks, missing licenses, attribution requirements. Generates NOTICES file, third-party license bundle, SPDX identifiers. Recommends CI pipeline license gate (license-checker, cargo-deny, pip-licenses). Rated 🟢 COMPLIANT / 🟡 NEEDS REMEDIATION / 🔴 LICENSE CONFLICT."},
    "verify":        {"tier": "T2", "model": "qwen2.5-coder:32b",  "file": "dev/quality/test_verify.py",          "consumes": ["TAR", "BIR", "FIR", "DIR"], "produces": "Verification Report", "description": "Runs the pre-written test suite against the built code. Reports pass/fail per test case, coverage metrics, and any regressions. This is the final TDD gate — if tests fail, build agents must iterate."},
    "mobile_ux":     {"tier": "T1", "model": "qwen2.5:72b",        "file": "mobile/ux/mobile_ux_designer.py",     "consumes": ["PRD"],                   "produces": "MUXD",          "description": "Designs the mobile experience for iOS, Android, and React Native — all three tracks from one document."},
    "mobile_qa":     {"tier": "T1", "model": "qwen2.5:72b",        "file": "mobile/qa/mobile_qa_specialist.py",   "consumes": ["MUXD", "PRD", "TAD"],    "produces": "Mobile Test Plan", "description": "Writes the mobile test plan and test code BEFORE mobile implementation begins. Defines Jest unit tests, RNTL component tests, Detox E2E scenarios, and accessibility checks that all mobile build agents must satisfy."},
    "ios_dev":       {"tier": "T2", "model": "qwen2.5-coder:32b",  "file": "mobile/ios/ios_developer.py",         "consumes": ["MUXD", "PRD", "Mobile Test Plan"],  "produces": "IIR",  "description": "Builds the native iOS app in Swift/SwiftUI. Receives pre-written XCTest cases and must produce code that passes all test assertions, including VoiceOver accessibility tests."},
    "android_dev":   {"tier": "T2", "model": "qwen2.5-coder:32b",  "file": "mobile/android/android_developer.py", "consumes": ["MUXD", "PRD", "Mobile Test Plan"], "produces": "AIR",  "description": "Builds the native Android app in Kotlin/Compose. Receives pre-written JUnit5/Espresso tests and must produce code that passes all test assertions, including TalkBack accessibility tests."},
    "rn_arch_p1":    {"tier": "T2", "model": "qwen2.5-coder:32b",  "file": "mobile/rn/react_native_architect_part1.py", "consumes": ["MUXD", "Mobile Test Plan"], "produces": "RNAD P1", "description": "Designs React Native architecture — navigation, state management, API layer, component hierarchy. Architecture must support the test contracts defined in the Mobile Test Plan."},
    "rn_arch_p2":    {"tier": "T2", "model": "qwen2.5-coder:32b",  "file": "mobile/rn/react_native_architect_part2.py", "consumes": ["RNAD P1"],          "produces": "RNAD P2",       "description": "Completes React Native architecture — testing strategy, deployment config, performance optimization (Part 2)."},
    "rn_dev":        {"tier": "T2", "model": "qwen2.5-coder:32b",  "file": "mobile/rn/react_native_developer.py", "consumes": ["RNAD P1", "RNAD P2", "Mobile Test Plan"], "produces": "RN Guide", "description": "Builds the cross-platform app in React Native/Expo/TypeScript. Must satisfy all Jest, RNTL, and Detox test cases from the Mobile Test Plan."},
    "mobile_devops": {"tier": "T2", "model": "qwen2.5-coder:32b",  "file": "mobile/devops/mobile_devops_engineer.py", "consumes": ["RN Guide", "SRR", "Mobile Test Plan"], "produces": "MDIR", "description": "Sets up mobile build pipelines, code signing, EAS Build, Fastlane, and store submission automation. CI must run mobile test suite and gate on pass."},
    "mobile_scale":  {"tier": "T1", "model": "qwen2.5:72b",        "file": "mobile/scalability/mobile_scalability_review.py", "consumes": ["MUXD", "IIR", "AIR", "RN Guide", "MDIR"], "produces": "Mobile SAR", "description": "Reviews mobile architecture for commercial scalability: API client efficiency (request batching, pagination, delta sync, offline-first with conflict resolution), local data management (SQLite/Realm optimization, cache eviction, storage budgets), asset delivery (image optimization, lazy loading, bundle splitting, OTA update strategy), push notification infrastructure (per-tenant routing, high-volume delivery), and multi-tenant mobile patterns (tenant switching, branded themes, config-driven feature flags). Rates 🟢 SCALE-READY / 🟡 NEEDS WORK / 🔴 NOT SCALABLE per platform."},
    "mobile_pen_test": {"tier": "T2", "model": "qwen2.5-coder:32b", "file": "mobile/security/mobile_penetration_tester.py", "consumes": ["SRR", "IIR", "AIR", "RN Guide", "MDIR"], "produces": "Mobile PTR", "description": "Performs static security analysis of all mobile code. Probes for OWASP Mobile Top 10: insecure data storage, weak auth, certificate pinning bypass, unprotected IPC, code tampering vectors, reverse engineering exposure, debug flags in release builds, hardcoded secrets, insecure WebView configs, and missing root/jailbreak detection. Rates 🟢 PASS / 🟡 CONDITIONAL / 🔴 FAIL with platform-specific findings (iOS, Android, RN)."},
    "mobile_verify": {"tier": "T2", "model": "qwen2.5-coder:32b",  "file": "mobile/qa/mobile_test_verify.py",    "consumes": ["Mobile Test Plan", "IIR", "AIR", "RN Guide", "MDIR"], "produces": "Mobile Verification Report", "description": "Runs the pre-written mobile test suite against all built mobile artifacts. Reports pass/fail per platform (iOS, Android, RN), coverage, and accessibility compliance. Final TDD gate for mobile."},
}


# ── Helper Functions ──────────────────────────────────────────

def find_projects():
    """Find all PROJ-*.json files in the logs directory."""
    pattern = os.path.join(PROJECT_DIR, "PROJ-*.json")
    files = glob.glob(pattern)
    projects = []
    for f in files:
        try:
            with open(f, "r") as fh:
                data = json.load(fh)
                projects.append({
                    "id": data.get("project_id", os.path.basename(f)),
                    "status": data.get("status", "UNKNOWN"),
                    "classification": data.get("classification", "?"),
                    "title": data.get("structured_spec", {}).get("title", "Untitled"),
                    "created_at": data.get("created_at", ""),
                    "path": f,
                    "artifact_count": len(data.get("artifacts", [])),
                    "checkpoint_count": len(data.get("checkpoints", [])),
                })
        except (json.JSONDecodeError, IOError):
            continue
    projects.sort(key=lambda p: p["created_at"], reverse=True)
    return projects


def load_project(project_id):
    """Load full project context JSON."""
    pattern = os.path.join(PROJECT_DIR, f"{project_id}.json")
    files = glob.glob(pattern)
    if not files:
        # Try partial match
        pattern = os.path.join(PROJECT_DIR, f"*{project_id}*.json")
        files = glob.glob(pattern)
    if files:
        with open(files[0], "r") as f:
            return json.load(f)
    return None


def get_pipeline_status(project_data):
    """Determine which agents have completed based on project artifacts."""
    if not project_data:
        return {}
    artifacts = project_data.get("artifacts", [])
    artifact_types = {a.get("type", "").upper() for a in artifacts}

    # Map artifact types back to pipeline step IDs
    type_to_step = {}
    for pipeline_name, steps in PIPELINE.items():
        for step in steps:
            produces = step["produces"].upper().replace(" ", "_")
            type_to_step[produces] = step["id"]
            # Also map common variations
            type_to_step[step["produces"].upper()] = step["id"]

    completed = set()
    for at in artifact_types:
        if at in type_to_step:
            completed.add(type_to_step[at])

    return completed


# ── Routes ────────────────────────────────────────────────────

@app.route("/")
def index():
    """Main GUI page."""
    return render_template("index.html")


@app.route("/api/pipeline")
def api_pipeline():
    """Return full pipeline definition."""
    return jsonify(PIPELINE)


@app.route("/api/agents")
def api_agents():
    """Return all agent detail cards."""
    return jsonify(AGENT_DETAILS)


@app.route("/api/agents/<agent_id>")
def api_agent_detail(agent_id):
    """Return single agent detail."""
    detail = AGENT_DETAILS.get(agent_id)
    if detail:
        return jsonify(detail)
    return jsonify({"error": "Agent not found"}), 404


@app.route("/api/projects")
def api_projects():
    """List all projects found in logs directory."""
    return jsonify(find_projects())


@app.route("/api/projects/<project_id>")
def api_project_detail(project_id):
    """Return full project context."""
    data = load_project(project_id)
    if data:
        return jsonify(data)
    return jsonify({"error": "Project not found"}), 404


@app.route("/api/projects/<project_id>/status")
def api_project_status(project_id):
    """Return pipeline completion status for a project."""
    data = load_project(project_id)
    completed = get_pipeline_status(data)
    return jsonify({
        "project_id": project_id,
        "completed_steps": list(completed),
        "total_web_steps": len(PIPELINE["web"]),
        "total_mobile_steps": len(PIPELINE["mobile"]),
    })


# ── Phase 2 Hooks (Future: Live Agent Control) ───────────────

@app.route("/api/projects", methods=["POST"])
def api_create_project():
    """
    Create a new project from a plain-English description.
    
    Phase 1: Creates the PROJ JSON file directly (lightweight, no LLM needed).
    Phase 2: Optionally runs classify.py to have the Orchestrator structure it.
    """
    data = request.json or {}
    description = data.get("description", "").strip()
    if not description:
        return jsonify({"error": "Project description is required"}), 400

    title = data.get("title", "").strip()
    run_classify = data.get("run_classify", False)

    # Generate project ID
    import hashlib
    hash_input = f"{description}{datetime.now().isoformat()}"
    project_id = "PROJ-" + hashlib.sha256(hash_input.encode()).hexdigest()[:8].upper()

    # Build initial project context
    now = datetime.now().isoformat() + "Z"
    project_context = {
        "project_id": project_id,
        "created_at": now,
        "status": "INITIATED",
        "classification": "UNKNOWN",
        "original_request": description,
        "structured_spec": {
            "title": title or description[:80],
            "description": description,
            "business_goal": "",
            "deliverables": [],
            "success_criteria": [],
            "estimated_complexity": data.get("complexity", "MEDIUM"),
            "data_required": data.get("data_required", False),
            "primary_crew": "DEV",
            "handoff_direction": None
        },
        "assigned_crew": None,
        "artifacts": [],
        "checkpoints": [],
        "handoffs": [],
        "audit_log": [
            {
                "timestamp": now,
                "event": "PROJECT_CREATED",
                "detail": f"Created via Mission Control GUI"
            }
        ]
    }

    # Ensure logs directory exists
    os.makedirs(PROJECT_DIR, exist_ok=True)
    project_path = os.path.join(PROJECT_DIR, f"{project_id}.json")

    # Write the project file
    with open(project_path, "w") as f:
        json.dump(project_context, f, indent=2)

    result = {
        "status": "created",
        "project_id": project_id,
        "path": project_path,
        "message": f"Project {project_id} created.",
        "next_step": "Run classify.py to structure the project, then router.py to assign a crew."
    }

    # Phase 2: Run the Orchestrator classify.py to structure the project
    if run_classify:
        classify_cmd = PIPELINE["web"][0]["command"]  # classify.py
        try:
            proc = subprocess.run(
                classify_cmd.split(),
                cwd=os.path.expanduser("~/dev-team"),
                capture_output=True,
                text=True,
                timeout=300
            )
            result["classify_status"] = "completed" if proc.returncode == 0 else "failed"
            result["classify_stdout"] = proc.stdout[-2000:]
            result["classify_stderr"] = proc.stderr[-500:]
            # Reload the project to get the structured version
            updated = load_project(project_id)
            if updated:
                result["status"] = updated.get("status", "INITIATED")
                result["classification"] = updated.get("classification", "UNKNOWN")
        except subprocess.TimeoutExpired:
            result["classify_status"] = "timeout"
        except FileNotFoundError:
            result["classify_status"] = "not_found"
            result["classify_message"] = "classify.py not found — project file created but not classified"

    return jsonify(result), 201


@app.route("/api/run/<agent_id>", methods=["POST"])
def api_run_agent(agent_id):
    """
    PHASE 2 HOOK: Run an agent via subprocess.
    Currently returns a stub. When ready, uncomment the subprocess call.
    """
    # Find the command for this agent
    command = None
    for pipeline_name, steps in PIPELINE.items():
        for step in steps:
            if step["id"] == agent_id:
                command = step["command"]
                break
    if not command:
        return jsonify({"error": "Agent not found"}), 404

    # Phase 2: Uncomment to enable live agent execution
    # try:
    #     result = subprocess.run(
    #         command.split(),
    #         cwd=os.path.expanduser("~/dev-team"),
    #         capture_output=True,
    #         text=True,
    #         timeout=3600  # 1 hour timeout
    #     )
    #     return jsonify({
    #         "status": "completed" if result.returncode == 0 else "failed",
    #         "stdout": result.stdout[-2000:],  # Last 2000 chars
    #         "stderr": result.stderr[-1000:],
    #         "returncode": result.returncode
    #     })
    # except subprocess.TimeoutExpired:
    #     return jsonify({"status": "timeout", "error": "Agent timed out after 1 hour"})

    return jsonify({
        "status": "stub",
        "message": f"Phase 2: Would run '{command}'. Enable live execution in app.py.",
        "command": command
    })


@app.route("/api/checkpoint/<project_id>", methods=["POST"])
def api_checkpoint_action(project_id):
    """
    PHASE 2 HOOK: Submit checkpoint approval/rejection.
    """
    action = request.json.get("action", "").upper()
    reason = request.json.get("reason", "")

    if action not in ("APPROVE", "REJECT"):
        return jsonify({"error": "Action must be APPROVE or REJECT"}), 400

    # Phase 2: Write to project context and trigger next step
    return jsonify({
        "status": "stub",
        "message": f"Phase 2: Would {action} checkpoint for {project_id}.",
        "action": action,
        "reason": reason
    })


# ── Main ──────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n  🚀 Dev-Team Mission Control")
    print(f"  📂 Watching: {PROJECT_DIR}")
    print(f"  🌐 Open: http://localhost:5000\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
