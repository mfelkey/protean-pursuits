"""
tests/test_team_templates.py

TDD — TEAM_TEMPLATES in agents/orchestrator/orchestrator.py must
register every team that PP can spin up. Prior to Day 3, training and
hr were both missing (confirmed in the Phase 2 kickoff doc).

Contract:
  - Every key in TEAM_TEMPLATES has a path on disk (or is an explicit
    submodule reference like teams/training-team).
  - All 10 teams are registered: dev, ds, marketing, strategy, legal,
    design, qa, video, hr, training.
"""
from pathlib import Path

import pytest


UMBRELLA_ROOT = Path(__file__).resolve().parent.parent


def test_team_templates_contains_all_10_teams():
    """Every PP team must be registered in TEAM_TEMPLATES."""
    from agents.orchestrator.orchestrator import TEAM_TEMPLATES

    expected = {
        "dev", "ds", "marketing", "strategy",
        "legal", "design", "qa", "video",
        "hr", "training",
    }
    assert expected.issubset(set(TEAM_TEMPLATES.keys())), (
        f"missing teams: {expected - set(TEAM_TEMPLATES.keys())}"
    )


def test_team_templates_paths_exist_on_disk():
    """
    Every registered path must exist — otherwise spinup_project_repo
    will silently skip that team with a warning, which is a latent bug.
    """
    from agents.orchestrator.orchestrator import TEAM_TEMPLATES

    for team, rel_path in TEAM_TEMPLATES.items():
        full = UMBRELLA_ROOT / rel_path
        assert full.exists(), (
            f"TEAM_TEMPLATES['{team}'] = '{rel_path}' does not exist on disk"
        )


def test_hr_registered():
    """HR was flagged missing in the kickoff doc — Day 3 fixes it."""
    from agents.orchestrator.orchestrator import TEAM_TEMPLATES
    assert "hr" in TEAM_TEMPLATES


def test_training_registered():
    """Training-team is the Day 3 addition."""
    from agents.orchestrator.orchestrator import TEAM_TEMPLATES
    assert "training" in TEAM_TEMPLATES
