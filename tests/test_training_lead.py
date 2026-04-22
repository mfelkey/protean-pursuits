"""
tests/test_training_lead.py

TDD — tests for agents/leads/training/training_lead.py.

The lead wraps build_team_lead() with training-team specifics and
exposes run_training_refresh() which dispatches into the submodule's
flows/training_flow.py via invoke_team_flow.

We do not hit CrewAI or Ollama in these tests — we patch build_team_lead
and invoke_team_flow at the import site so the tests are fast,
deterministic, and env-independent.
"""
from unittest.mock import patch, MagicMock

import pytest


def test_training_lead_module_importable():
    from agents.leads.training import training_lead  # noqa: F401


def test_build_training_lead_uses_correct_team_name():
    """build_training_lead must dispatch build_team_lead with team_name='training-team'."""
    import agents.leads.training.training_lead as tl

    with patch.object(tl, "build_team_lead") as mock_build:
        mock_build.return_value = MagicMock(name="FakeAgent")
        tl.build_training_lead()

    assert mock_build.called
    kwargs = mock_build.call_args.kwargs
    assert kwargs["team_name"] == "training-team"
    assert "Training" in kwargs["role"] or "training" in kwargs["role"].lower()
    # Backstory should mention HITL or knowledge (core responsibility)
    backstory = kwargs["backstory"].lower()
    assert "knowledge" in backstory or "curator" in backstory


def test_run_training_refresh_mode_full():
    """mode=full dispatches with just --mode full."""
    import agents.leads.training.training_lead as tl

    with patch.object(tl, "invoke_team_flow") as mock_inv:
        mock_inv.return_value = {"status": "ok"}
        tl.run_training_refresh(context={"project_name": "X"}, mode="full")

    assert mock_inv.called
    args = mock_inv.call_args.args
    assert args[0] == "training-team"
    assert args[1] == "flows/training_flow.py"
    # args[2] is the args list passed to the subprocess
    flow_args = args[2]
    assert "--mode" in flow_args
    assert "full" in flow_args
    # no extra args on a bare 'full' call
    assert "--team" not in flow_args
    assert "--topic" not in flow_args


def test_run_training_refresh_mode_team():
    """mode=team requires --team to be passed through."""
    import agents.leads.training.training_lead as tl

    with patch.object(tl, "invoke_team_flow") as mock_inv:
        mock_inv.return_value = {"status": "ok"}
        tl.run_training_refresh(context={}, mode="team", team="legal")

    flow_args = mock_inv.call_args.args[2]
    assert "--team" in flow_args
    assert "legal" in flow_args


def test_run_training_refresh_mode_on_demand():
    """mode=on_demand forwards both --team and --topic."""
    import agents.leads.training.training_lead as tl

    with patch.object(tl, "invoke_team_flow") as mock_inv:
        mock_inv.return_value = {"status": "ok"}
        tl.run_training_refresh(
            context={}, mode="on_demand",
            team="legal", topic="UKGC new ruling",
        )

    flow_args = mock_inv.call_args.args[2]
    assert "--team" in flow_args
    assert "legal" in flow_args
    assert "--topic" in flow_args
    assert "UKGC new ruling" in flow_args


def test_run_training_refresh_mode_alerts_with_hours():
    """mode=alerts forwards --hours."""
    import agents.leads.training.training_lead as tl

    with patch.object(tl, "invoke_team_flow") as mock_inv:
        mock_inv.return_value = {"status": "ok"}
        tl.run_training_refresh(context={}, mode="alerts", hours=48)

    flow_args = mock_inv.call_args.args[2]
    assert "--hours" in flow_args
    assert "48" in flow_args
