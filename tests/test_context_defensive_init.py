"""
tests/test_context_defensive_init.py

Phase 4 follow-up — log_event/add_artifact/add_blocker must not crash
when called with a bare context dict that doesn't have the expected
list keys pre-populated. Hit on 2026-04-22 during the video-team
bootstrap: run_video_deliverable() passed a context with just
project_name/project_id to invoke_team_flow, which then called
log_event(...) and crashed on KeyError: 'events'.
"""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

UMBRELLA_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(UMBRELLA_ROOT))


@pytest.fixture
def chdir_tmp(tmp_path):
    """Run in a temp dir so logs/ doesn't pollute the repo."""
    prev = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(prev)


def test_log_event_on_bare_context_does_not_crash(chdir_tmp):
    from core import context as ctx_mod
    ctx = {"project_name": "X", "project_id": "PROJ-X"}
    with patch.object(ctx_mod, "save_context"):
        ctx_mod.log_event(ctx, "TEST_EVENT", "detail")
    assert "events" in ctx
    assert len(ctx["events"]) == 1
    assert ctx["events"][0]["event_type"] == "TEST_EVENT"


def test_log_event_preserves_existing_events():
    from core import context as ctx_mod
    ctx = {"events": [{"event_type": "PRIOR"}]}
    with patch.object(ctx_mod, "save_context"):
        ctx_mod.log_event(ctx, "NEW", "d")
    assert len(ctx["events"]) == 2
    assert ctx["events"][0]["event_type"] == "PRIOR"
    assert ctx["events"][1]["event_type"] == "NEW"


def test_add_artifact_on_bare_context_does_not_crash():
    from core import context as ctx_mod
    ctx = {}
    ctx_mod.add_artifact(ctx, name="a", artifact_type="b",
                          path="/x", created_by="me")
    assert len(ctx["artifacts"]) == 1


def test_add_blocker_on_bare_context_does_not_crash():
    from core import context as ctx_mod
    ctx = {}
    ctx_mod.add_blocker(ctx, "B-1", "HIGH", "something", "owner")
    assert len(ctx["blockers"]) == 1
