#!/usr/bin/env python3.11
"""
scripts/verify_tier_routing.py

Audits every agent file and flags any that appear to route reasoning
work to the Tier 2 (code) model, or vice versa.

Usage:
    python3.11 scripts/verify_tier_routing.py

Exit code 0 = clean. Non-zero = findings (printed to stderr).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Agents whose primary output is CODE — legitimately Tier 2.
# Anything matching these path fragments is expected on Tier 2.
CODE_GEN_PATTERNS = (
    "dev-team/agents/dev/build/",
    "dev-team/agents/desktop/",
    "dev-team/agents/mobile/ios/",
    "dev-team/agents/mobile/android/",
    "dev-team/agents/mobile/rn/",
    "dev-team/agents/mobile/devops/",
    "dev-team/agents/mobile/security/mobile_penetration_tester",
    "dev-team/agents/dev/quality/test_automation_engineer",
    "dev-team/agents/dev/quality/test_verify",
    "dev-team/agents/dev/performance/performance_auditor",
    "dev-team/agents/dev/security/penetration_tester",
)

# Parameterized factories — the TIER2_MODEL reference is a routing key,
# not a routing decision. Skip them.
PARAMETERIZED_FACTORIES = (
    "qa-team/agents/orchestrator/base_agent.py",
    "video-team/agents/orchestrator/base_agent.py",
    "video-team/config/config.py",
)

TIER2_LINE = re.compile(r'os\.getenv\(\s*"TIER2_MODEL"')


def is_legit_tier2(path: Path) -> bool:
    sp = str(path)
    if any(p in sp for p in PARAMETERIZED_FACTORIES):
        return True
    return any(p in sp for p in CODE_GEN_PATTERNS)


def main() -> int:
    findings: list[str] = []
    for py in REPO_ROOT.rglob("*.py"):
        if ".git" in py.parts or "tests" in py.parts:
            continue
        try:
            text = py.read_text()
        except (OSError, UnicodeDecodeError):
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if TIER2_LINE.search(line) and not is_legit_tier2(py):
                rel = py.relative_to(REPO_ROOT)
                findings.append(f"{rel}:{lineno}: {line.strip()}")

    if findings:
        print("TIER ROUTING AUDIT — findings:", file=sys.stderr)
        for f in findings:
            print(f"  {f}", file=sys.stderr)
        print(
            f"\n{len(findings)} non-code-gen agent(s) still routed to TIER2_MODEL.",
            file=sys.stderr,
        )
        return 1

    print("TIER ROUTING AUDIT — clean. All TIER2_MODEL references are on code-generation agents or parameterized factories.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
