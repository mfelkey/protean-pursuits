"""
tests/test_video_lead.py

Phase 4 — video-team wiring. Verifies that the Video Team Lead
produces valid flow CLI invocations and serializes structured params
into the --context JSON correctly.
"""
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

UMBRELLA_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(UMBRELLA_ROOT))

from agents.leads.video import video_lead


# ------------------------------------------------------------------------
# Normalization
# ------------------------------------------------------------------------

@pytest.mark.parametrize("given,expected", [
    ("SHORT_FORM",  "SHORT_FORM"),
    ("short_form",  "SHORT_FORM"),
    ("Short_Form",  "SHORT_FORM"),
    ("  brief_only  ", "BRIEF_ONLY"),
    ("FULL",        "FULL"),
])
def test_normalise_mode_accepts_mixed_case(given, expected):
    assert video_lead._normalise_mode(given) == expected


def test_normalise_mode_rejects_empty():
    with pytest.raises(ValueError, match="required"):
        video_lead._normalise_mode("")


def test_normalise_mode_rejects_unknown():
    with pytest.raises(ValueError, match="unknown video mode"):
        video_lead._normalise_mode("podcast")


@pytest.mark.parametrize("given,expected", [
    ("TIKTOK",  "TIKTOK"),
    ("tiktok",  "TIKTOK"),
    ("YouTube", "YOUTUBE"),
    ("",        "TIKTOK"),  # default fallback
])
def test_normalise_format(given, expected):
    assert video_lead._normalise_format(given) == expected


def test_normalise_format_rejects_unknown():
    with pytest.raises(ValueError, match="unknown video_format"):
        video_lead._normalise_format("SMS")


# ------------------------------------------------------------------------
# Task string construction
# ------------------------------------------------------------------------

def test_task_string_uses_brand_brief_verbatim_when_provided():
    task = video_lead._build_task_string(
        mode="SHORT_FORM", topic="anything", brand_brief="my full brief",
        duration=30, video_format="TIKTOK",
    )
    assert task == "my full brief"


def test_task_string_falls_back_to_topic_summary():
    task = video_lead._build_task_string(
        mode="SHORT_FORM", topic="parallax launch", brand_brief="",
        duration=60, video_format="TIKTOK",
    )
    assert "Short Form" in task
    assert "TIKTOK" in task
    assert "60" in task
    assert "parallax launch" in task


def test_task_string_default_when_no_topic_no_brief():
    task = video_lead._build_task_string(
        mode="LONG_FORM", topic="", brand_brief="",
        duration=120, video_format="YOUTUBE",
    )
    assert "Long Form" in task
    assert "YOUTUBE" in task
    assert "120" in task


# ------------------------------------------------------------------------
# Context payload
# ------------------------------------------------------------------------

def test_payload_has_required_fields():
    raw = video_lead._build_context_payload(
        context={"project_name": "ParallaxEdge", "project_id": "PROJ-PARALLAXEDGE"},
        video_format="TIKTOK", topic="launch", duration=60,
        brand_brief="", avatar_config="", recording_path="",
    )
    payload = json.loads(raw)
    assert payload["video_format"] == "TIKTOK"
    assert payload["duration"] == 60
    assert payload["topic"] == "launch"
    assert payload["project_name"] == "ParallaxEdge"
    assert payload["project_id"] == "PROJ-PARALLAXEDGE"


def test_payload_omits_empty_optional_fields():
    raw = video_lead._build_context_payload(
        context={"project_name": "X"},
        video_format="TIKTOK", topic="", duration=30,
        brand_brief="", avatar_config="", recording_path="",
    )
    payload = json.loads(raw)
    assert "topic" not in payload
    assert "brand_brief" not in payload
    assert "avatar_config" not in payload
    assert "recording_path" not in payload


def test_payload_parses_avatar_config_json():
    """If avatar_config is JSON, it nests correctly rather than
    becoming an escaped string."""
    avatar = '{"rig": "heygen_v2", "voice_id": "abc"}'
    raw = video_lead._build_context_payload(
        context={"project_name": "X"},
        video_format="TIKTOK", topic="", duration=30,
        brand_brief="", avatar_config=avatar, recording_path="",
    )
    payload = json.loads(raw)
    assert isinstance(payload["avatar_config"], dict)
    assert payload["avatar_config"]["rig"] == "heygen_v2"


def test_payload_passes_avatar_config_as_string_if_not_json():
    raw = video_lead._build_context_payload(
        context={"project_name": "X"},
        video_format="TIKTOK", topic="", duration=30,
        brand_brief="", avatar_config="simple-rig-id", recording_path="",
    )
    payload = json.loads(raw)
    assert payload["avatar_config"] == "simple-rig-id"


# ------------------------------------------------------------------------
# End-to-end: run_video_deliverable -> invoke_team_flow call shape
# ------------------------------------------------------------------------

def test_run_video_deliverable_produces_valid_args():
    """
    invoke_team_flow must be called with arguments the flow's argparse
    will actually accept. This is the main regression guard against
    the Phase 4 bug that broke this lead for every prior session.
    """
    ctx = {"project_name": "ParallaxEdge", "project_id": "PROJ-PARALLAXEDGE"}
    with patch.object(video_lead, "invoke_team_flow",
                       return_value=ctx) as spy:
        video_lead.run_video_deliverable(
            context=ctx,
            mode="short_form",  # lowercase on purpose
            video_format="tiktok",
            topic="ParallaxEdge launch",
            duration=45,
        )
    assert spy.called
    call_args = spy.call_args
    team_name, flow_script, args, context = call_args.args
    assert team_name == "video-team"
    assert flow_script == "flows/video_flow.py"

    # The args list must match the flow's argparse surface.
    assert "--mode" in args
    assert args[args.index("--mode") + 1] == "SHORT_FORM"   # normalized
    assert "--task" in args
    assert "--context" in args
    # With a project_name, --project + --save go in
    assert "--project" in args
    assert args[args.index("--project") + 1] == "ParallaxEdge"
    assert "--save" in args

    # --context is the only place the extras live — not separate CLI flags
    assert "--format" not in args
    assert "--duration" not in args
    assert "--topic" not in args
    assert "--avatar-config" not in args


def test_run_video_deliverable_without_project_omits_save():
    """If no project_name, skip --project/--save; the flow enforces
    the invariant --save requires --project."""
    ctx = {}
    with patch.object(video_lead, "invoke_team_flow", return_value=ctx) as spy:
        video_lead.run_video_deliverable(
            context=ctx, mode="BRIEF_ONLY", video_format="TIKTOK",
            topic="quick test",
        )
    _, _, args, _ = spy.call_args.args
    assert "--save" not in args
    assert "--project" not in args


def test_run_video_deliverable_context_json_roundtrips():
    """The --context JSON the lead produces must be parseable JSON
    containing all structured params."""
    ctx = {"project_name": "P", "project_id": "PROJ-P"}
    captured = {}
    def spy(team, flow, args, context):
        captured["args"] = args
        return context
    with patch.object(video_lead, "invoke_team_flow", side_effect=spy):
        video_lead.run_video_deliverable(
            context=ctx, mode="AVATAR", video_format="REELS",
            topic="demo", duration=30,
            avatar_config='{"rig":"heygen","voice":"v1"}',
            recording_path="/tmp/screen.mp4",
        )
    ctx_json = captured["args"][captured["args"].index("--context") + 1]
    payload = json.loads(ctx_json)
    assert payload["video_format"] == "REELS"
    assert payload["duration"] == 30
    assert payload["topic"] == "demo"
    assert payload["avatar_config"]["rig"] == "heygen"
    assert payload["recording_path"] == "/tmp/screen.mp4"
    assert payload["project_id"] == "PROJ-P"


def test_run_video_deliverable_rejects_unknown_mode():
    with pytest.raises(ValueError, match="unknown video mode"):
        video_lead.run_video_deliverable(
            context={"project_name": "X"},
            mode="definitely-not-a-mode",
        )


def test_run_video_deliverable_rejects_unknown_format():
    with pytest.raises(ValueError, match="unknown video_format"):
        video_lead.run_video_deliverable(
            context={"project_name": "X"},
            mode="SHORT_FORM",
            video_format="SMS",
        )


# ------------------------------------------------------------------------
# build_video_lead smoke
# ------------------------------------------------------------------------

def test_build_video_lead_module_importable():
    """Public API contract — build_video_lead is a module-level callable."""
    assert callable(video_lead.build_video_lead)


# ------------------------------------------------------------------------
# Submodule bootstrap script
# ------------------------------------------------------------------------

def test_bootstrap_script_exists_and_executable():
    """The submodule bootstrap helper must exist and be executable."""
    import os
    script = UMBRELLA_ROOT / "scripts" / "bootstrap_video_team_submodule.sh"
    assert script.exists(), f"missing {script}"
    assert os.access(script, os.X_OK), f"{script} is not executable"


def test_bootstrap_script_references_key_paths():
    """Smoke check — script targets the right template + remote."""
    script_text = (UMBRELLA_ROOT / "scripts" /
                   "bootstrap_video_team_submodule.sh").read_text()
    assert "templates/video-team" in script_text
    assert "teams/video-team" in script_text
    assert "mfelkey/video-team" in script_text
    # Ensures we don't force-push
    assert "--force" not in script_text
    assert "push -f" not in script_text


def test_bootstrap_script_shell_syntax_valid():
    """bash -n validates syntax without executing."""
    import shutil
    import subprocess
    bash = shutil.which("bash")
    if not bash:
        pytest.skip("bash not available")
    script = UMBRELLA_ROOT / "scripts" / "bootstrap_video_team_submodule.sh"
    result = subprocess.run([bash, "-n", str(script)],
                             capture_output=True, text=True)
    assert result.returncode == 0, (
        f"shell syntax error:\n{result.stderr}"
    )
