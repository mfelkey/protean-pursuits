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


def test_save_context_missing_project_id_uses_unknown(chdir_tmp):
    """save_context must not raise KeyError when project_id is absent.
    Falls back to 'unknown' in the filename."""
    from core import context as ctx_mod
    ctx = {"team": "video"}
    path = ctx_mod.save_context(ctx, logs_dir="logs")
    assert "unknown_video.json" in path
    import os
    assert os.path.exists(path)


def test_save_context_missing_team_uses_unknown(chdir_tmp):
    """save_context must not raise KeyError when team is absent.
    Hit during the 2026-04-22 video activation — the lead's context
    had project_id but no team key."""
    from core import context as ctx_mod
    ctx = {"project_id": "PROJ-X"}
    path = ctx_mod.save_context(ctx, logs_dir="logs")
    assert "PROJ-X_unknown.json" in path
    import os
    assert os.path.exists(path)


def test_save_context_missing_both_uses_unknown(chdir_tmp):
    """The bare-context case: neither project_id nor team set."""
    from core import context as ctx_mod
    ctx = {}
    path = ctx_mod.save_context(ctx, logs_dir="logs")
    assert "unknown_unknown.json" in path


def test_full_bare_context_log_event_roundtrip(chdir_tmp):
    """
    Full regression guard: the exact sequence that failed on 2026-04-22.
    A bare context (just project_name + project_id) passes through
    log_event -> save_context without crashing.
    """
    from core import context as ctx_mod
    ctx = {"project_name": "ParallaxEdge", "project_id": "PROJ-PARALLAXEDGE"}
    # Real save, not mocked — this is the regression path
    ctx_mod.log_event(ctx, "TEAM_UNAVAILABLE", "video-team", logs_dir="logs")
    assert len(ctx["events"]) == 1
    assert ctx["events"][0]["event_type"] == "TEAM_UNAVAILABLE"
