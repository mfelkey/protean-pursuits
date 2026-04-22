"""
tests/test_teams_dir_path.py

Phase 4.3 regression — TEAMS_DIR in agents/leads/base_lead.py must
resolve to <umbrella-root>/teams, NOT to <one-level-above-umbrella>/teams.

The prior implementation had one extra '..' in the path join, which
silently broke team_exists() for every team lead. Masked because the
leads framework wasn't exercised end-to-end until the 2026-04-22 video
activation.

We import via a fresh spec_from_file_location so the test doesn't
require the full crewai import chain to succeed.
"""
import importlib.util
import os
import sys
from pathlib import Path

import pytest

UMBRELLA_ROOT = Path(__file__).resolve().parent.parent
BASE_LEAD_PATH = UMBRELLA_ROOT / "agents" / "leads" / "base_lead.py"


def _load_base_lead_without_crewai():
    """Load base_lead.py far enough to read TEAMS_DIR without needing
    crewai. We parse the file directly and eval the constant."""
    import ast
    tree = ast.parse(BASE_LEAD_PATH.read_text())
    for node in ast.walk(tree):
        if (isinstance(node, ast.Assign) and
                any(getattr(t, "id", None) == "TEAMS_DIR"
                    for t in node.targets)):
            # Reconstruct and eval the expression safely-ish: it's
            # os.path.abspath(os.path.join(os.path.dirname(__file__), ...))
            # We substitute __file__ with BASE_LEAD_PATH.
            import os
            return eval(
                compile(ast.Expression(node.value), "<ast>", "eval"),
                {"os": os, "__file__": str(BASE_LEAD_PATH)},
            )
    raise RuntimeError("TEAMS_DIR not found in base_lead.py")


def test_teams_dir_resolves_inside_umbrella_repo():
    """TEAMS_DIR must point at <umbrella>/teams, not <parent>/teams."""
    teams_dir = _load_base_lead_without_crewai()
    expected = str(UMBRELLA_ROOT / "teams")
    assert teams_dir == expected, (
        f"TEAMS_DIR resolved to {teams_dir!r} but expected {expected!r}. "
        f"Check the number of '..' in the os.path.join call in base_lead.py."
    )


def test_teams_dir_is_an_existing_directory():
    """Sanity: the computed TEAMS_DIR actually exists on disk."""
    teams_dir = _load_base_lead_without_crewai()
    assert os.path.isdir(teams_dir), (
        f"TEAMS_DIR {teams_dir!r} does not exist as a directory"
    )


def test_teams_dir_contains_known_teams():
    """
    Guard against a future refactor that accidentally breaks TEAMS_DIR
    again. At least dev-team and training-team must be discoverable.
    """
    teams_dir = _load_base_lead_without_crewai()
    entries = set(os.listdir(teams_dir))
    # Be lenient on this list — only check for teams that have been
    # registered for a while (pre Phase 4). dev, ds, training are
    # safe bets.
    for expected in ("dev-team", "training-team"):
        assert expected in entries, (
            f"{expected!r} not found under TEAMS_DIR={teams_dir!r}. "
            f"Present: {sorted(entries)}"
        )
