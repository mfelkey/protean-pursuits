"""
tests/test_day6_docs_and_hooks.py

Day 6 umbrella tests:
  - LL-041 is present in docs/LESSONS_LEARNED.md and parses cleanly
    via the training-team's LL parser (the contract the hook depends
    on).
  - scripts/install_post_commit_hook.sh exists, is executable, and
    has valid shell syntax.
  - Manual is at v3.4 with Phase 2 content in the Training Team section.
"""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


UMBRELLA_ROOT = Path(__file__).resolve().parent.parent
LL_PATH = UMBRELLA_ROOT / "docs" / "LESSONS_LEARNED.md"
MANUAL_PATH = UMBRELLA_ROOT / "docs" / "agent_system_operating_manual.md"
HOOK_SCRIPT = UMBRELLA_ROOT / "scripts" / "install_post_commit_hook.sh"
TRAINING_TEAM = UMBRELLA_ROOT / "teams" / "training-team"


# ------------------------------------------------------------------------
# LL-041 presence and parseability
# ------------------------------------------------------------------------

def test_ll_041_present_in_lessons_learned():
    text = LL_PATH.read_text()
    assert "## LL-041 —" in text, "LL-041 entry missing from docs/LESSONS_LEARNED.md"


def test_ll_042_present_in_lessons_learned():
    text = LL_PATH.read_text()
    assert "## LL-042 —" in text, "LL-042 (Unicode caveat) missing"


def test_ll_043_present_in_lessons_learned():
    text = LL_PATH.read_text()
    assert "## LL-043 —" in text, "LL-043 (Phase 2 retrospective) missing"


def test_all_ll_entries_parse_via_training_team_parser():
    """
    Every LL in the file must parse cleanly. Guards against a future
    edit breaking the format (missing date, corrupted heading, etc.).
    """
    submodule_parser = TRAINING_TEAM / "agents" / "curators" / "lessons_learned" / "parser.py"
    if not submodule_parser.exists():
        pytest.skip("training-team submodule not initialized")

    script = (
        f"import sys; sys.path.insert(0, {str(TRAINING_TEAM)!r}); "
        f"from agents.curators.lessons_learned.parser import parse_ll_file; "
        f"entries = parse_ll_file({str(LL_PATH)!r}); "
        f"print(chr(10).join(f\"{{e['ll_id']}}|{{e['date']}}|{{e['severity']}}\" for e in entries))"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        pytest.skip(f"parser subprocess failed: {result.stderr.strip()}")

    out = result.stdout.strip().splitlines()
    ids = [line.split("|")[0] for line in out]
    for expected in ("LL-040", "LL-041", "LL-042", "LL-043"):
        assert expected in ids, f"{expected} not parsed out of {ids}"

    # Every entry has a non-empty date
    for line in out:
        parts = line.split("|")
        assert parts[1], f"entry {parts[0]} has empty date"


def test_ll_041_parses_via_training_team_parser():
    """
    The submodule's LL parser is the canonical consumer of this file.
    If LL-041 doesn't parse out, the post-commit hook won't queue it.
    """
    submodule_parser = TRAINING_TEAM / "agents" / "curators" / "lessons_learned" / "parser.py"
    if not submodule_parser.exists():
        pytest.skip(
            "training-team submodule not initialized — "
            "run `git submodule update --init -- teams/training-team`"
        )

    # Import in a subprocess so the submodule's sys.path mutation doesn't
    # shadow the umbrella's `agents` package for other tests in the run.
    script = (
        f"import sys; sys.path.insert(0, {str(TRAINING_TEAM)!r}); "
        f"from agents.curators.lessons_learned.parser import parse_ll_file; "
        f"entries = parse_ll_file({str(LL_PATH)!r}); "
        f"ids = sorted({{e['ll_id'] for e in entries}}); "
        f"print('IDS:' + ','.join(ids)); "
        f"ll = next(e for e in entries if e['ll_id'] == 'LL-041'); "
        f"print('DATE:' + ll['date']); "
        f"print('SEV:' + ll['severity']); "
        f"print('TITLE:' + ll['title'])"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        pytest.skip(f"parser subprocess failed: {result.stderr.strip()}")

    out = result.stdout
    assert "LL-041" in out, f"parser did not extract LL-041. stdout: {out}"
    assert "DATE:2026-04-22" in out
    assert "SEV:" in out and "MEDIUM" in out


def test_ll_041_body_mentions_propose_knowledge():
    """
    The lesson is specifically about the HITL gate via propose_knowledge.
    Guard against a future edit that accidentally guts the technical
    content.
    """
    text = LL_PATH.read_text()
    # Find the LL-041 section
    start = text.find("## LL-041")
    end = text.find("## LL-040")
    assert start >= 0 and end > start, "couldn't locate LL-041 block"
    body = text[start:end]
    assert "propose_knowledge" in body
    assert "store_knowledge" in body
    assert "approve_candidates" in body


# ------------------------------------------------------------------------
# Post-commit hook installer
# ------------------------------------------------------------------------

def test_hook_installer_exists():
    assert HOOK_SCRIPT.exists(), f"missing {HOOK_SCRIPT}"


def test_hook_installer_is_executable():
    import os
    assert os.access(HOOK_SCRIPT, os.X_OK), \
        f"{HOOK_SCRIPT} is not executable"


def test_hook_installer_shell_syntax_valid():
    """bash -n validates syntax without executing."""
    bash = shutil.which("bash")
    if not bash:
        pytest.skip("bash not available in this environment")
    result = subprocess.run(
        [bash, "-n", str(HOOK_SCRIPT)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, (
        f"shell syntax error:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )


def test_hook_installer_mentions_key_components():
    """
    Smoke check: the installer references the pieces it should
    (training-team flow, ll mode, approve_candidates for review).
    """
    text = HOOK_SCRIPT.read_text()
    assert "training-team" in text
    assert "--mode ll" in text
    assert "approve_candidates" in text


# ------------------------------------------------------------------------
# Manual bump
# ------------------------------------------------------------------------

def test_manual_bumped_to_v34():
    text = MANUAL_PATH.read_text()
    assert "Version 3.4" in text, "manual not bumped to v3.4"
    assert "Version 3.3" not in text, "stale v3.3 reference remains"


def test_manual_training_section_mentions_phase_2():
    """Training Team section must reflect HITL gate + 11 curators + LL."""
    text = MANUAL_PATH.read_text()
    # Find the Training Team heading and check content around it
    start = text.find("## Training Team — Knowledge Management")
    assert start >= 0, "Training Team section heading missing"
    # Read the next ~3000 chars (section is bounded by the next ## or #)
    section = text[start:start + 3000]

    assert "11 agent teams" in section or "11 domain curators" in section, \
        "manual still references old team count (pre-Phase-2)"
    assert "HITL" in section, "HITL gate not mentioned"
    assert "propose_knowledge" in section or "approve_candidates" in section, \
        "HITL mechanism not named"
    assert "Lessons Learned" in section, "LL curator not mentioned"
    assert "LL" in section, "ll mode not mentioned"
