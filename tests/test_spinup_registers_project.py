"""
tests/test_spinup_registers_project.py

Phase 3 — spinup_project_repo() must auto-register the project with
the training-team knowledge layer on successful spinup, using
DEFAULT_PROJECT_DOMAINS (Option A from the Phase 3 design note).

This closes the last gap from Phase 2: projects existed as repos but
weren't known to the knowledge layer unless someone manually called
register_project(). That left inject_context(project=...) silently
falling back to team-only context for fresh projects.

Integration approach: lazy import from teams/training-team/ to avoid
hard-coupling the umbrella orchestrator to the submodule. If the
submodule is uninitialized, spinup still succeeds but logs a warning
— registration is a best-effort enrichment, not a blocking
precondition.
"""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

UMBRELLA_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(UMBRELLA_ROOT))


@pytest.fixture
def fake_context(tmp_path):
    return {
        "project_name": "ParallaxEdge",
        "project_id": "PROJ-PARALLAXEDGE",
        "status": "PRD_APPROVED",
    }


@pytest.fixture
def fake_target(tmp_path):
    return str(tmp_path / "project_repo")


@pytest.fixture
def stub_spinup_deps():
    """
    Stub the dependencies of spinup_project_repo that aren't the
    registration behaviour we're testing: human approval (always
    approve), log_event, save_context, and the actual copytree.
    """
    with patch("agents.orchestrator.orchestrator.request_human_approval",
               return_value=True), \
         patch("agents.orchestrator.orchestrator.log_event"), \
         patch("agents.orchestrator.orchestrator.save_context"), \
         patch("agents.orchestrator.orchestrator.shutil.copytree"):
        yield


# ------------------------------------------------------------------------
# Contract: successful spinup triggers register_project
# ------------------------------------------------------------------------

def test_spinup_calls_register_project_on_success(
        fake_context, fake_target, stub_spinup_deps):
    from agents.orchestrator import orchestrator as orch

    with patch.object(orch, "_register_project_lazy") as reg:
        orch.spinup_project_repo(
            context=fake_context,
            teams=["dev"],
            target_dir=fake_target,
        )

    assert reg.called, "register_project was not invoked"
    call_args = reg.call_args
    assert call_args.args[0] == "ParallaxEdge" or \
           call_args.kwargs.get("name") == "ParallaxEdge", \
           f"expected project_name='ParallaxEdge', got {call_args}"


def test_spinup_skipped_register_on_rejection(
        fake_context, fake_target):
    """If human rejects the spinup, no registration fires."""
    from agents.orchestrator import orchestrator as orch

    with patch.object(orch, "request_human_approval", return_value=False), \
         patch.object(orch, "log_event"), \
         patch.object(orch, "_register_project_lazy") as reg:
        orch.spinup_project_repo(
            context=fake_context,
            teams=["dev"],
            target_dir=fake_target,
        )

    assert not reg.called, \
        "register_project should not run if spinup was rejected"


def test_register_project_failure_does_not_break_spinup(
        fake_context, fake_target, stub_spinup_deps):
    """
    If register_project raises (submodule uninitialized, ImportError,
    etc.), spinup still succeeds with status REPO_SPUNUP. Registration
    is best-effort.
    """
    from agents.orchestrator import orchestrator as orch

    with patch.object(orch, "_register_project_lazy",
                      side_effect=ImportError("submodule missing")):
        result = orch.spinup_project_repo(
            context=fake_context,
            teams=["dev"],
            target_dir=fake_target,
        )

    assert result["status"] == "REPO_SPUNUP"


# ------------------------------------------------------------------------
# The lazy-import helper itself
# ------------------------------------------------------------------------

def test_register_project_lazy_is_importable():
    """The helper exists as a public symbol in the orchestrator."""
    from agents.orchestrator import orchestrator as orch
    assert hasattr(orch, "_register_project_lazy"), \
        "orchestrator must expose _register_project_lazy"
    assert callable(orch._register_project_lazy)


def test_register_project_lazy_uses_default_project_domains():
    """
    Option A: spinup always uses DEFAULT_PROJECT_DOMAINS. The lazy
    helper does NOT take a domains kwarg — callers who need custom
    domains must call the submodule's register_project directly.
    """
    from agents.orchestrator import orchestrator as orch
    import inspect
    sig = inspect.signature(orch._register_project_lazy)
    # Only one positional parameter: the project name
    assert len(sig.parameters) == 1, (
        f"_register_project_lazy should take only (name), got {list(sig.parameters)}"
    )
